import json
import sys
import time
from threading import Thread, Event

from flask import Flask, jsonify, request
import pandas as pd
import os
from flask_cors import CORS
from Ashare import get_price
from SimulatedClock import SimulatedClock
from train_model import TrainModel
from flask_sqlalchemy import SQLAlchemy

from tushare_interface import TushareInterface

WIN = sys.platform.startswith('win')
if WIN:  # 如果是 Windows 系统，使用三个斜线
    prefix = 'sqlite:///'
else:  # 否则使用四个斜线
    prefix = 'sqlite:////'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(app.root_path, './data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭对模型修改的监控
# 在扩展类实例化前加载配置
db = SQLAlchemy(app)
CORS(app)  # 添加这一行来启用 CORS 支持
CORS(app, resources={r"/*": {"origins": "*"}})
stop_event = Event()
monitor_thread = None


# 数据存储路径

class MonitorStocks(db.Model):
    # 将 stock_code 设置为主键
    stock_code = db.Column(db.String(10), unique=True, nullable=False, primary_key=True)  # 设置为主键
    # 描述字段
    name = db.Column(db.String(20))

    def __repr__(self):
        return f"<MonitorStocks(stock_code={self.stock_code}, description={self.name})>"


@app.route('/time_share_data/<name>', methods=['GET'])
def get_time_share_data(name):
    try:
        tushare_interface = TushareInterface()
        stock_code = tushare_interface.get_code_by_name(name)
        pre_close = tushare_interface.get_pre_close(tushare_interface.get_code_by_name2(name))
        if stock_code is None:
            return jsonify({"message": f"Stock with name {name} not exists."}), 400
        train_model = TrainModel()
        select_count = train_model.select_count()
        df = get_price(stock_code, frequency='1m', count=select_count)
        # 如果数据为空，返回400错误
        if df.empty:
            return jsonify({"error": "No time share data available"}), 400
        last_index = df.index[-1]
        df = df.drop(last_index)
        df.index.name = 'time'
        df = df.reset_index()
        df['time'] = df['time'].apply(lambda x: x.timestamp())
        print(df)
        # 选择要返回的列（time, open, close, high, low, volume）
        result = df[['time', 'open', 'close', 'high', 'low', 'volume']].reset_index().to_dict(orient='records')
        # json_file_path = f'{code}_time_share_data.json'
        # with open(json_file_path, 'w') as json_file:
        #     json.dump(result, json_file)
        #
        # # 从 JSON 文件读取数据
        # json_file_path = f'{code}_time_share_data.json'
        # with open(json_file_path, 'r') as json_file:
        #     result = json.load(json_file)
        # 返回 JSON 格式的结果
        response = {
            "pre_close": pre_close,
            "data": result
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 开始训练接口
@app.route('/start_train/<name>', methods=['POST'])
def start_train(name):
    try:
        tushare_interface = TushareInterface()
        stock_code = tushare_interface.get_code_by_name(name)
        if stock_code is None:
            return jsonify({"message": f"Stock with name {name} not exists."}), 400
        # 从请求体中获取开始时间和结束时间
        request_data = request.get_json()
        start_time = request_data.get("start_time")
        end_time = request_data.get("end_time")
        action = request_data.get("action")

        if not start_time or not end_time:
            return jsonify({"error": "Start time and end time are required"}), 400

        # 模拟训练逻辑
        print(f"开始训练，股票代码：{stock_code}")
        print(f"开始时间：{start_time}, 结束时间：{end_time}")
        train_model = TrainModel()
        train_model.save_data(stock_code, start_time, end_time, action)
        train_model.retrain_with_all_data()
        # 训练逻辑可以包括数据过滤、模型训练等
        # 示例: 根据时间范围过滤数据
        # filtered_data = filter_data_by_time_range(code, start_time, end_time)

        # 返回训练成功的消息
        return jsonify({"message": f"Training started for stock {stock_code} from {start_time} to {end_time}"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/playback_sell_point/<name>', methods=['POST'])
def sell_point_playback(name):
    tushare_interface = TushareInterface()
    stock_code = tushare_interface.get_code_by_name(name)
    if stock_code is None:
        return jsonify({"message": f"Stock with name {name} not exists."}), 400
    train_model = TrainModel()
    train_model.retrain_with_all_data()
    train_model.save_data2(stock_code, 500)
    select_count = train_model.select_count()
    clock = SimulatedClock(code=stock_code, point_count=select_count)
    time = clock.get_current_time()
    sell_points = []
    while not clock.is_time_to_end():
        if clock.count < 20:
            clock.count = 20
        df = train_model.get_time_series_data('%s.csv' % stock_code, time, clock.count)
        sell_point = train_model.code_sell_point_use_date(df, stock_code, False)
        if sell_point is not None:
            sell_points.append(sell_point)
        time = clock.next()

    return jsonify(sell_points)


@app.route('/add_stock/<name>', methods=['POST'])
def add_stock(name):
    # 假设股票代码是通过某种方式获取的，例如通过 API 或静态列表
    # 这里我们假设股票代码是固定的，实际中你应该从外部数据源或API查询。
    tushare_interface = TushareInterface()
    stock_code = tushare_interface.get_code_by_name(name)
    if stock_code is None:
        return jsonify({"message": f"Stock with name {name} not exists."}), 400
    print(stock_code)

    # 检查数据库中是否已存在该股票代码
    existing_stock = MonitorStocks.query.filter_by(stock_code=stock_code).first()
    if existing_stock:
        return jsonify({"message": f"Stock with name {name} already exists."}), 400

    # 创建新的 MonitorStocks 实例
    new_stock = MonitorStocks(stock_code=stock_code, name=name)

    # 将新股票保存到数据库
    db.session.add(new_stock)
    db.session.commit()

    # 返回保存成功的结果
    return jsonify({
        "message": "Stock added successfully.",
        "stock_code": new_stock.stock_code,
        "name": new_stock.name
    }), 201


# 删除股票接口
@app.route('/delete_stock/<code>', methods=['DELETE'])
def delete_stock(code):
    # 查找要删除的股票

    stock = MonitorStocks.query.filter_by(stock_code=code).first()
    # 如果没有找到该股票，则返回错误信息
    if not stock:
        return jsonify({"error": "Stock not found"}), 404

    # 删除该股票
    db.session.delete(stock)
    db.session.commit()

    return jsonify({"message": f"Stock {code} deleted successfully"}), 200


@app.route('/get_all_stocks', methods=['GET'])
def get_all_stocks():
    # 查询所有股票记录
    stocks = MonitorStocks.query.all()

    # 将结果转换为字典列表
    stocks_list = []
    for stock in stocks:
        stocks_list.append({
            'stock_code': stock.stock_code,
            'name': stock.name
        })

    # 返回所有股票数据
    return jsonify(stocks_list)


def monitor_stocks():
    with app.app_context():
        train_model = TrainModel()
        train_model.retrain_with_all_data()
        stocks = MonitorStocks.query.all()
        while not stop_event.is_set():
            for stock in stocks:
                print("code:", stock.stock_code)
                # 在这里添加监控逻辑
                df = get_price(stock.stock_code, frequency='1m', count=train_model.select_count())
                last_index = df.index[-1]
                df = df.drop(last_index)
                df.index.name = 'time'
                # 重命名列
                df.rename(columns={'close': 'Price', 'volume': 'Volume'}, inplace=True)
                df.reset_index()
                train_model.code_sell_point_use_date(df, stock.name, True)
            time.sleep(1)


@app.route('/start_monitor', methods=['POST'])
def start_monitor():
    global monitor_thread

    # 如果监控线程已经存在，返回已启动的消息
    if monitor_thread is not None and monitor_thread.is_alive():
        return jsonify({"message": "股票监控已启动"}), 200

    # 创建并启动监控线程
    stop_event.clear()  # 确保停止事件被清除
    monitor_thread = Thread(target=monitor_stocks)
    monitor_thread.start()

    return jsonify({"message": "股票监控已启动"}), 200


@app.route('/stop_monitor', methods=['POST'])
def stop_monitor():
    global monitor_thread
    stop_event.set()  # 设置停止事件，指示线程停止监控

    if monitor_thread is not None:
        monitor_thread.join()  # 等待线程结束
        monitor_thread = None  # 重置监控线程

    return jsonify({"message": "股票监控已停止"}), 200


# with app.app_context():
#     db.drop_all()  # This will delete everything
#     print('11111')
#     db.create_all()
#     print('22222')

if __name__ == "__main__":
    # 启动 Flask 应用
    app.run(host='0.0.0.0', port=5001)
