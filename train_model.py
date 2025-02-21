import logging
import os
import pickle
from datetime import datetime, timedelta
import time
# import talib  # 用于计算技术指标
import pandas as pd
import numpy as np
import requests
from scipy.stats import linregress
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import MinMaxScaler
from Ashare import get_price
from trading_record import TradingRecord
from tushare_interface import TushareInterface
from xt_trader_order import XtTraderOrder

from log import get_logger


class TraderRecord:
    def __init__(self, name, direction, price, timestamp):
        self.stock_name = name
        self.direction = direction
        self.price = price
        self.timestamp = timestamp


class TrainModel:
    def __init__(self):
        self.loaded_sell_model = None
        self.loaded_buy_model = None
        self.sell_model_file = None
        self.sell_features = ['Volume', 'SMA5', 'mean', 'Price_change', 'Volume_change', 'rsi', 'volume_ma5',
                              'vwap', 'distance']
        self.buy_features = ['Price', 'Volume', 'SMA5', 'SMA10', 'Price_change', 'Volume_change', 'rsi']
        self.BUY_POINT = "Buy_Point"
        self.SELL_POINT = "Sell_Point"
        self.buy_model_file = None
        self.create_directories_if_not_exists()
        self.logger = get_logger("ai_trader_data", False)
        self.SELL_POINT_THRESHOLD = 0.64
        self.SELL_POINT_SMONTH_THRESHOLD = 0.6
        self.BUY_POINT_THRESHOLD = 0.64
        self.MAX_SELL_PERIOD = 80
        self.to_buy_list = []
        self.to_sell_list = []

    def set_buy_threshold(self, buy_threshold):
        self.BUY_POINT_THRESHOLD = buy_threshold

    def set_sell_threshold(self, sell_threshold):
        self.SELL_POINT_THRESHOLD = sell_threshold

    def get_threshold(self):
        return self.BUY_POINT_THRESHOLD, self.SELL_POINT_THRESHOLD

    def create_directories_if_not_exists(self):
        # 定义要创建的文件夹路径
        base_dir = 'test'
        sell_dir = os.path.join(base_dir, 'sell')
        buy_dir = os.path.join(base_dir, 'buy')

        # 检查 base_dir 是否存在，如果不存在则创建它
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
            print(f"Base directory '{base_dir}' created.")

        # 检查 sell_dir 和 buy_dir 是否存在，如果不存在则创建它们
        if not os.path.exists(sell_dir):
            os.makedirs(sell_dir)
            print(f"Directory '{sell_dir}' created.")
        else:
            print(f"Directory '{sell_dir}' already exists.")

        if not os.path.exists(buy_dir):
            os.makedirs(buy_dir)
            print(f"Directory '{buy_dir}' created.")
        else:
            print(f"Directory '{buy_dir}' already exists.")

    def calculate_rsi(self, series, period=14):
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_price_slope(self, data, window_minutes=10):
        # 获取最近window_minutes个数据
        if len(data) < window_minutes:
            raise ValueError(f"数据长度小于 {window_minutes}，无法计算斜率")

        # 只使用最近10分钟的数据
        y = data['Price'].values[-window_minutes:]
        x = range(window_minutes)  # x 为时间索引，从0到window_minutes-1

        # 计算线性回归的斜率
        slope, _, _, _, _ = linregress(x, y)

        return slope

    # 计算 MACD
    def calculate_macd(self, data, fast_period=12, slow_period=26, signal_period=9):
        fast_ema = data['Price'].ewm(span=fast_period, adjust=False).mean()
        slow_ema = data['Price'].ewm(span=slow_period, adjust=False).mean()
        macd = fast_ema - slow_ema
        signal = macd.ewm(span=signal_period, adjust=False).mean()
        return macd, signal

    def data_convert2(self, data):
        # 预处理：如去除缺失值、归一化等
        data.ffill()
        # 归一化价格和成交量数据
        scaler = MinMaxScaler()
        data['Close'] = data['Price']
        data[['Price', 'Volume']] = scaler.fit_transform(data[['Price', 'Volume']])

        # 添加简单的移动平均线作为特征
        data['SMA5'] = data['Price'].rolling(window=5).mean()
        data['SMA10'] = data['Price'].rolling(window=10).mean()
        # 添加价格变化率
        data['Price_change'] = data['Price'].pct_change().fillna(0)
        data['Price_change'] = data['Price_change'].replace([np.inf, -np.inf], 0)
        # 添加成交量变化率
        data['Volume_change'] = data['Volume'].pct_change().fillna(0)
        data['Volume_change'] = data['Volume_change'].replace([np.inf, -np.inf], 0)
        data['rsi'] = self.calculate_rsi(data['Price'], 14).fillna(0)
        data['volume_ma5'] = data['Volume'].rolling(window=5).mean()
        data['vwap'] = (data['Price'] * data['Volume']).cumsum() / data['Volume'].cumsum()
        data['mean'] = data['Close'].mean()

        # 计算距离比例
        data['distance'] = (data['Close'] - data['mean']) / data['mean']
        # 对 'distance' 列进行归一化
        scaler = MinMaxScaler(feature_range=(0, 1))
        data['distance'] = scaler.fit_transform(data[['distance']])
        # 去除空值
        # print(data)
        data.dropna(inplace=True)
        return data

    def load_and_merge_data(self, file_names):
        all_data = []
        for file in file_names:
            data_input = pd.read_csv(file)
            data = self.data_convert2(data_input)
            all_data.append(data)
        # 合并所有数据
        merged_data = pd.concat(all_data, axis=0, ignore_index=True)
        return merged_data

    def load_test_case(self, file_names):
        self.data = self.load_and_merge_data(file_names)

    def train_model(self, action):
        # 输入特征和目标变量
        if action == self.BUY_POINT:
            X = self.data[self.buy_features]
        if action == self.SELL_POINT:
            X = self.data[self.sell_features]
        y = self.data[action]  # 卖点标签（1 为卖点，0 为非卖点）
        X_train = X
        y_train = y
        # 划分训练集和测试集

        # 创建 XGBoost 模型
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        # model = xgb.XGBClassifier()
        # 训练模型
        model.fit(X_train, y_train)

        # 保存模型到文件
        if action == self.BUY_POINT:
            self.buy_model_file = 'buy_point_model.pkl'
            pickle.dump(model, open(self.buy_model_file, 'wb'))
        if action == self.SELL_POINT:
            self.sell_model_file = 'sell_point_model.pkl'
            pickle.dump(model, open(self.sell_model_file, 'wb'))

    def load_model_predict(self, x_input, action):
        # 使用加载的模型进行预测
        if action == self.BUY_POINT:
            predictions = self.loaded_buy_model.predict(x_input)
        elif action == self.SELL_POINT:
            predictions = self.loaded_sell_model.predict(x_input)
        return predictions

    def load_buy_model_predict(self, x_input):
        # 使用加载的模型进行预测
        predictions = self.loaded_buy_model.predict(x_input)
        return predictions

    def code_trade_point_use_date(self, data_input, name, is_send_message, action):
        # print(action)
        data_test = self.data_convert2(data_input)
        self.logger.info(f'action:{action},name:{name}')
        if action == self.SELL_POINT:
            point = 'Predicted_Sell_Point'
            X_test = data_test[self.sell_features]
        if action == self.BUY_POINT:
            point = 'Predicted_Buy_Point'
            X_test = data_test[self.buy_features]

        # 输入特征和目标变量

        y_pred = self.load_model_predict(X_test, action)
        if action == self.BUY_POINT:
            threshold = self.BUY_POINT_THRESHOLD  # 设置你的阈值
            prob_pred = self.loaded_buy_model.predict_proba(X_test)  # 获取预测概率
        elif action == self.SELL_POINT:
            threshold = self.SELL_POINT_THRESHOLD  # 设置你的阈值
            prob_pred = self.loaded_sell_model.predict_proba(X_test)  # 获取预测概率
            # # 获取特征重要性
            # feature_importances = self.loaded_sell_model.feature_importances_
            #
            # # 创建一个DataFrame来展示特征重要性
            # feature_names = [f'Feature_{i}' for i in range(len(self.sell_features))]
            # importance_df = pd.DataFrame({'Feature': feature_names, 'Importance': feature_importances})
            # importance_df = importance_df.sort_values(by='Importance', ascending=False)
            #
            # print(importance_df)

        # 假设是二分类问题，prob_pred[:, 1] 是类别1的预测概率
        smoothed_prob = prob_pred[-4:, 1].mean()
        custom_pred = (prob_pred[:, 1] >= threshold).astype(int)  # 根据阈值决定类别
        time_str = data_test['time'].iloc[-1]
        print(time_str)
        print(prob_pred[-1])
        # print(prob_pred)
        self.logger.info(f'time:{time_str},pred:{prob_pred[-1]},smoothed_prob:{smoothed_prob}')
        self.logger.info(f'data:{data_input}')
        if custom_pred[-1] == 1:
            # print(prob_pred)
            print('smoothed_prob:', smoothed_prob)
            if is_send_message is True:
                # 解析日期时间字符串

                date_time_str = data_test['time'].iloc[-1]
                date_time_obj = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")
                # # 提取时分信息
                # five_minutes_ago = datetime.strptime(data_test['time'].iloc[-1], "%Y-%m-%d %H:%M:%S") - timedelta(
                #     minutes=3)
                # # 查询数据库
                # recent_record = TradingRecord.query.filter(
                #     TradingRecord.stock_name == name,
                #     TradingRecord.direction == action,
                #     TradingRecord.timestamp >= five_minutes_ago
                # ).first()
                # # if recent_record is None:
                # #     print('no result')
                # if recent_record:
                #     self.logger.info(f"Message for {name}-{action} was already sent in the last 5 minutes. Skipping...")
                #     self.send_message_to_dingding(name, "INFO", date_time_obj.strftime("%H:%M"))
                #     return None, None
                self.send_message_to_dingding(name, action, date_time_obj.strftime("%H:%M"))
                time.sleep(0.1)
            # print('code:', code)

            data_test[('%s' % point)] = y_pred  # 将预测的卖点添加到数据中
            # 只显示预测为卖点（Sell_Point = 1）的记录
            trade_points = data_test[data_test[point] == 1]
            # 打印时间、卖点预测值和实际标签
            print(trade_points[['time', point]].reset_index())
            new_record = TraderRecord(name, action, data_test['Close'].iloc[-1],
                                      datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S'))
            return data_test['time'].iloc[-1], new_record, smoothed_prob, len(trade_points)
        return None, None, None, None

    def save_data(self, code, sell_start, sell_end, action_type):
        sell_start = datetime.strptime(sell_start, '%Y-%m-%d %H:%M:%S')
        sell_end = datetime.strptime(sell_end, '%Y-%m-%d %H:%M:%S')
        df = get_price(code, frequency='1m', count=241)  # 支持'1m','5m','15m','30m','60m'
        last_index = df.index[-1]
        df = df.drop(last_index)
        df.index.name = 'time'
        # 重命名列
        df.rename(columns={'close': 'Price', 'volume': 'Volume'}, inplace=True)
        sell_mask = (df.index >= sell_start) & (df.index <= sell_end)
        # 保存DataFrame为CSV文件
        df[action_type] = sell_mask.astype(int)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # 根据 action_type 确定文件夹
        if action_type == self.BUY_POINT:
            csv_file_path = f'./test/buy/{code}_{timestamp}.csv'
        else:
            csv_file_path = f'./test/sell/{code}_{timestamp}.csv'
        df.to_csv(csv_file_path, index=True)  # index=False表示不保存DataFrame的索引
        print(f'数据已保存至 {csv_file_path}')
        return csv_file_path

    def get_newest_price(self, stock_code, time, data_count):
        df = self.get_time_series_data('%s.csv' % stock_code, time, data_count)

        print(df['Price'].iloc[-1])

    def save_data2(self, code, size):
        df = get_price(code, frequency='1m', count=size)  # 支持'1m','5m','15m','30m','60m'
        last_index = df.index[-1]
        df = df.drop(last_index)
        df.index.name = 'time'
        # 重命名列
        df.rename(columns={'close': 'Price', 'volume': 'Volume'}, inplace=True)

        csv_file_path = f'{code}.csv'
        df.to_csv(csv_file_path, index=True)  # index=False表示不保存DataFrame的索引
        print(f'数据已保存至 {csv_file_path}')

    def send_message_to_dingding(self, name, action, time):
        # 你的Server酱API密钥
        SCKEY = 'SCT264646TimdMu3Bib84f7EJ52Ay06ydD'

        # 发送消息到钉钉的URL
        url = f'https://sctapi.ftqq.com/{SCKEY}.send?channel=2'

        # 要发送的消息内容，你可以根据Server酱的文档来格式化这个JSON
        # 这里只是一个简单的示例
        if action == self.BUY_POINT:
            action_text = "Buy点"
        if action == self.SELL_POINT:
            action_text = "Sell点"
        if action is None:
            action_text = "timeout"
        if action == "ON_LINE":
            action_text = "online"
        if action == "INFO":
            action_text = "2分钟内已经提醒过"

        data = {
            "text": f"{time} {name}提示{action_text}"
        }

        # 发送POST请求
        response = requests.post(url, data=data)

        # 打印响应结果，检查是否发送成功
        print(response.text)

    def send_message2_wechat(self, title):
        SCKEY = 'SCT264646TimdMu3Bib84f7EJ52Ay06ydD'

        # 发送消息到钉钉的URL
        url = f'https://sctapi.ftqq.com/{SCKEY}.send?channel=2'

        # 要发送的消息内容，你可以根据Server酱的文档来格式化这个JSON
        # 这里只是一个简单的示例
        data = {
            "text": f"{title}",
        }

        # 发送POST请求
        response = requests.post(url, data=data)

    def train_use_new_file(self, new_file):

        pass

    def get_all_test_csv(self, type):
        # 指定目录路径
        directory = 'test'
        if type == self.BUY_POINT:
            directory = 'test/buy'
        if type == self.SELL_POINT:
            directory = 'test/sell'
        # 初始化一个空列表来存储CSV文件的路径
        csv_files = []

        # 遍历目录中的所有文件和子目录
        for root, dirs, files in os.walk(directory):
            for file in files:
                # 检查文件扩展名是否为.csv
                if file.endswith('.csv'):
                    csv_files.append(os.path.join(root, file))

        # 打印找到的CSV文件路径
        print(csv_files)
        return csv_files

    def retrain_with_all_sell_data(self):
        file_names = self.get_all_test_csv(self.SELL_POINT)
        self.load_test_case(file_names)
        self.train_model(self.SELL_POINT)
        self.load_sell_model()

    def retrain_with_all_buy_data(self):
        file_names = self.get_all_test_csv(self.BUY_POINT)
        self.load_test_case(file_names)
        self.train_model(self.BUY_POINT)
        self.load_buy_model()

    def train_with_all_buy_data(self):
        file_names = self.get_all_test_csv(self.BUY_POINT)
        self.load_test_case(file_names)
        self.train_buy_model()

    def train_buy_model(self):
        X = self.data[self.features]
        y = self.data[self.BUY_POINT]  # 卖点标签（1 为卖点，0 为非卖点）
        X_train = X
        y_train = y
        # 划分训练集和测试集

        # 创建 XGBoost 模型
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        # model = xgb.XGBClassifier()
        # 训练模型
        model.fit(X_train, y_train)

        # 保存模型到文件
        self.buy_model_file = 'buy_point_model.pkl'
        pickle.dump(model, open(self.buy_model_file, 'wb'))

    # def load_buy_model_predict(self, x_input):
    #     loaded_model = pickle.load(open(self.buy_model_file, 'rb'))
    #
    #     # 使用加载的模型进行预测
    #     predictions = loaded_model.predict(x_input)
    #     return predictions

    def get_time_series_data(self, file_name, target_time, time_window_minutes=60):
        # 读取 CSV 文件
        df = pd.read_csv(file_name)
        # 将 'time' 列转换为 datetime 格式
        target_time = datetime.strftime(target_time, '%Y-%m-%d %H:%M:%S')
        # target_time = "2024-12-11 15:00:00"
        # 确保目标时间存在于数据中
        if target_time not in df['time'].values:
            self.logger.info(f'target_time:{target_time} not found in the data.')

        # 获取目标时间的索引位置
        target_index = df[df['time'] == target_time].index[0]

        # 计算60条数据的起始索引
        start_index = max(target_index - time_window_minutes, 0)
        cols_needed = ['time', 'open', 'Price', 'high', 'low', 'Volume']
        # 获取从目标时间前60条数据
        result_df = df.loc[start_index:target_index, cols_needed]
        self.logger.info(f'result_df_size:{len(result_df)}')
        self.logger.info(f'select_count:{time_window_minutes}')
        return result_df

    def load_sell_model(self):
        self.loaded_sell_model = pickle.load(open(self.sell_model_file, 'rb'))

    def load_buy_model(self):
        self.loaded_buy_model = pickle.load(open(self.buy_model_file, 'rb'))

    def select_count(self):
        df = get_price('sz300001', frequency='1m', count=241)
        last_index = df.index[-1]
        df = df.drop(last_index)
        df.index.name = 'time'
        df = df.reset_index()
        tushare_interface = TushareInterface()
        date = tushare_interface.find_nearest_trading_day(tushare_interface.get_today_date())
        print(date)
        s = date.strftime('%Y-%m-%d')
        threshold = pd.to_datetime('%s 09:30:00' % s)
        filtered_df = df[df['time'] >= threshold]
        return len(filtered_df)

    def select_count2(self, current_time):
        # 计算当前时间距离9:30的分钟数
        threshold = current_time.replace(hour=9, minute=30, second=0, microsecond=0)
        delta = current_time - threshold
        # #  计算13：00到9点30的分钟数的时候 跳过中间休市的时间
        # if delta.seconds // 60 > 150:
        #     delta = timedelta(minutes=150)
        count = delta.seconds // 60
        if count >= 211:
            count = count - 90

        return count
