import pandas as pd

from GridStrategy2 import GridStrategy2
from train_model import TrainModel


class GridStrategy:
    def __init__(self, grid_interval=0.1):
        """
        初始化网格策略
        :param grid_interval: 归一化后的网格间隔（单位：归一化值）
        """
        self.grid_interval = grid_interval  # 网格间隔（归一化后）
        self.last_buy_price = None  # 上一次触发买入信号的归一化价格
        self.strategy_map = {}

    def run(self, code, indicate_buy_time):
        df = pd.read_csv(code + '.csv')

        pass

    def normalize_data(self, prices):
        """
        对价格数据进行归一化
        :param prices: 收盘价列表
        :return: 归一化后的价格列表、最小值和最大值
        """
        min_price = min(prices)
        max_price = max(prices)
        normalized_prices = [(price - min_price) / (max_price - min_price) for price in prices]
        return normalized_prices, min_price, max_price

    def simulate_grid_trading_from_csv(self, file_path, indicate_buy_time, type, grid_interval=0.1):
        """
        从 CSV 文件模拟网格策略交易
        :param file_path: CSV 文件路径
        :param grid_interval: 归一化后的网格间隔
        """
        # 读取 CSV 数据
        df = pd.read_csv(file_path)
        df['datetime'] = pd.to_datetime(df['time'])

        # 提取收盘价数据
        prices = df['Price'].tolist()
        pre_close = df.iloc[0]['Price']
        # 找到 `indicate_buy_time` 列中匹配目标值的行索引

        # 提取 `datetime` 列的时分部分，匹配输入时间
        indices = df[df['datetime'].dt.strftime('%H:%M') == indicate_buy_time].index
        start_index = indices[0]
        df_next = df.iloc[start_index:]
        print(df_next)
        # 模拟逐条加载数据并判定买入信号
        grid_strategy = GridStrategy2(15)

        for i, row in enumerate(df_next.itertuples(index=False)):
            min_price = df[:i + start_index + 1].Price.min()
            max_price = df[:i + start_index + 1].Price.max()
            print(row.datetime.strftime('%H:%M'))
            grid_strategy.generate_grids(min_price, max_price)
            last_price = df.iloc[start_index + i - 1]['Price']
            action = grid_strategy.check_price(row.Price, type, last_price, pre_close)
            print(action)
            if action == 'buy' and type == 'buy':
                return row.datetime.strftime('%H:%M')
            if action == 'sell' and type == 'sell':
                return row.datetime.strftime('%H:%M')

    def should_buy(self, normalized_price, original_price):
        """
        判断是否触发买入信号
        :param normalized_price: 当前价格的归一化值
        :param original_price: 当前价格的原始值
        :return: 是否买入（True 或 False）
        """
        if self.last_buy_price is None or normalized_price >= self.last_buy_price + self.grid_interval:
            self.last_buy_price = normalized_price  # 更新买入点（归一化价格）
            return True, original_price  # 返回买入信号和原始价格
        return False, None

    def realtime_grid_trading_from_csv(self, action, current_time, stock_code):
        """
        从 CSV 文件模拟网格策略交易
        :param grid_interval: 归一化后的网格间隔
        """
        train_model = TrainModel()
        select_count = train_model.select_count2(current_time) + 1
        df = train_model.get_time_series_data('%s.csv' % stock_code, current_time,
                                              select_count)
        print(df)

        # 提取收盘价数据
        prices = df['Price'].tolist()
        pre_close = df.iloc[0]['Price']
        # 找到 `indicate_buy_time` 列中匹配目标值的行索引

        # 如果stock_code不存在 创建一个map 用来存储GridStrategy2类 如果存在则从map中取出
        grid_strategy = GridStrategy2(15)
        if stock_code not in self.strategy_map:
            grid_strategy = GridStrategy2(15)
            self.strategy_map[stock_code] = grid_strategy
        else:
            grid_strategy = self.strategy_map[stock_code]
        min_price = df['Price'].min()
        max_price = df['Price'].max()
        grid_strategy.generate_grids(min_price, max_price)
        action = grid_strategy.check_price(prices[-1], action, pre_close)
        return action
        #
        # for i, row in enumerate(df_next.itertuples(index=False)):
        #     min_price = df[:i + start_index + 1].Price.min()
        #     max_price = df[:i + start_index + 1].Price.max()
        #     print(row.datetime.strftime('%H:%M'))
        #     grid_strategy.generate_grids(min_price, max_price)
        #     last_price = df.iloc[start_index + i - 1]['Price']
        #     action = grid_strategy.check_price(row.Price, type, last_price, pre_close)
        #     print(action)
        #     if action == 'buy' and type == 'buy':
        #         return row.datetime.strftime('%H:%M')
        #     if action == 'sell' and type == 'sell':
        #         return row.datetime.strftime('%H:%M')
