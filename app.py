import json
import sys
import time
import datetime
from threading import Thread, Event

from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
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
# 配置 JWT 密钥
app.config['JWT_SECRET_KEY'] = 'your-secret-key'
jwt = JWTManager(app)


# 数据存储路径

class MonitorStocks(db.Model):
    # 将 stock_code 设置为主键
    stock_code = db.Column(db.String(10), unique=True, nullable=False, primary_key=True)  # 设置为主键
    # 描述字段
    name = db.Column(db.String(20))

    def __repr__(self):
        return f"<MonitorStocks(stock_code={self.stock_code}, description={self.name})>"


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


class LoginRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    login_time = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    ip_address = db.Column(db.String(50), nullable=False)

    user = db.relationship('User', backref=db.backref('login_records', lazy=True))


# 数据库模型
class Holding(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stock_name = db.Column(db.String(50), unique=True, nullable=False)
    stock_code = db.Column(db.String(50), unique=True, nullable=False)
    cost_price = db.Column(db.Float, nullable=False)
    added_on = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f"<Holding {self.stock_name}>"


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
        print(df['low'].min())
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
        train_model.retrain_with_all_sell_data()
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
    train_model.retrain_with_all_sell_data()
    train_model.save_data2(stock_code, 500)
    select_count = train_model.select_count()
    clock = SimulatedClock(code=stock_code, point_count=select_count)
    time = clock.get_current_time()
    print(time)
    sell_points = []
    while not clock.is_time_to_end():
        data_count = max(clock.count, 20)
        data_count = min(data_count, train_model.MAX_SELL_PERIOD)
        df = train_model.get_time_series_data('%s.csv' % stock_code, time, data_count)
        sell_point, _ = train_model.code_trade_point_use_date(df, name, False, train_model.SELL_POINT)
        if sell_point is not None:
            sell_points.append(sell_point)
        time = clock.next()

    return jsonify(sell_points)


@app.route('/playback_buy_point/<name>', methods=['POST'])
def buy_point_playback(name):
    tushare_interface = TushareInterface()
    stock_code = tushare_interface.get_code_by_name(name)
    if stock_code is None:
        return jsonify({"message": f"Stock with name {name} not exists."}), 400
    train_model = TrainModel()
    train_model.retrain_with_all_buy_data()
    train_model.save_data2(stock_code, 500)
    select_count = train_model.select_count()
    clock = SimulatedClock(code=stock_code, point_count=select_count)
    time = clock.get_current_time()
    print(time)
    buy_points = []
    while not clock.is_time_to_end():
        data_count = max(clock.count, 20)
        df = train_model.get_time_series_data('%s.csv' % stock_code, time, data_count)
        buy_point, _ = train_model.code_trade_point_use_date(df, name, False, train_model.BUY_POINT)
        if buy_point is not None:
            buy_points.append(buy_point)
        time = clock.next()

    return jsonify(buy_points)


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
        train_model.retrain_with_all_sell_data()
        train_model.retrain_with_all_buy_data()
        while not stop_event.is_set():
            start_time = time.time()
            current_time = datetime.datetime.now()
            current_time1 = datetime.datetime.now()
            current_time_str = current_time.strftime('%H:%M')
            current_time = current_time.replace(second=0, microsecond=0)
            if '09:30' <= current_time_str < '11:30' or '13:01' <= current_time_str < '15:00':
                second = current_time1.second
                if second != 5:
                    time.sleep(0.8)
                    continue
                minute = current_time1.minute
                if minute % 10 == 0:
                    train_model.send_message_to_dingding("监控程序在线中", "ON_LINE", "00:00")
                    monitor_holdings_stocks(current_time, train_model)
                monitor_selected_stocks_buy_point(current_time, train_model)
                monitor_my_holding_stocks_sell_point(current_time, train_model)

                end_time = time.time()
                cost = end_time - start_time
                print(f"执行时间: {end_time - start_time} 秒")
                if cost > 50:
                    train_model.send_message_to_dingding("计算超时", "", "00:00")
            else:
                time.sleep(60)


def monitor_my_holding_stocks_sell_point(current_time, train_model):
    stocks = Holding.query.all()
    for stock in stocks:
        print(stock.stock_name)
        train_model.save_data2(stock.stock_code, 500)
        select_count = train_model.select_count2(current_time)
        data_count_sell = max(20, select_count)
        data_count_sell = min(data_count_sell, train_model.MAX_SELL_PERIOD)
        # 在这里添加监控逻辑
        df_sell = train_model.get_time_series_data('%s.csv' % stock.stock_code, current_time,
                                                   data_count_sell)
        sell_point, sell_record = train_model.code_trade_point_use_date(df_sell, stock.stock_name, True,
                                                                        train_model.SELL_POINT)
        insert_trade_record(sell_record)


def monitor_selected_stocks_buy_point(current_time, train_model):
    stocks = MonitorStocks.query.all()
    for stock in stocks:
        print(stock.name)
        train_model.save_data2(stock.stock_code, 500)
        select_count = train_model.select_count2(current_time)
        data_count_buy = max(20, select_count)
        df_buy = train_model.get_time_series_data('%s.csv' % stock.stock_code, current_time,
                                                  data_count_buy)
        buy_point, buy_record = train_model.code_trade_point_use_date(df_buy, stock.name, True, train_model.BUY_POINT)
        insert_trade_record(buy_record)


def monitor_holdings_stocks(current_time, train_model):
    stocks = Holding.query.all()
    for stock in stocks:
        print(stock)
        code = stock.stock_code
        current_price = get_current_price(code)
        print(current_price)
        cost_price = stock.cost_price
        # 计算跌幅百分比
        if cost_price > 0:
            percentage_decrease = ((current_price - cost_price) / cost_price) * 100
        else:
            percentage_decrease = 0

        # 如果跌幅超过 5%，则发送提醒
        print(percentage_decrease)
        if percentage_decrease < -5.0:
            insert_stock_name = stock.stock_name + "进入5%止损区间"
            train_model.send_message_to_dingding(insert_stock_name, train_model.SELL_POINT, current_time)
            time.sleep(0.1)
        # 在这里添加监控逻辑


def get_current_price(code):
    df = get_price(code, frequency='1m', count=2)  # 支持'1m','5m','15m','30m','60m'
    last_index = df.index[-1]
    df = df.drop(last_index)
    current_price = df.iloc[-1]['close']
    return current_price


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


@app.route('/monitor_status', methods=['GET'])
def monitor_status():
    # 使用一个布尔值直接表示监控状态
    is_monitoring = monitor_thread is not None
    return jsonify({"isMonitoring": is_monitoring}), 200


@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    print('register')
    print("username:", username)
    if not username or not password:
        return jsonify({"message": "Username and password are required."}), 400

    hashed_password = generate_password_hash(password)

    try:
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User registered successfully."}), 201
    except Exception as e:
        db.session.rollback()
        if "UNIQUE constraint failed" in str(e):
            return jsonify({"message": "Username already exists."}), 409
        return jsonify({"message": "An error occurred."}), 500


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    print('login')
    print("username:", username)
    if not username or not password:
        return jsonify({"message": "Username and password are required."}), 400

    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password, password):
        access_token = create_access_token(identity=user.username, fresh=True,
                                           expires_delta=datetime.timedelta(hours=1))
        # 获取当前时间和客户端 IP 地址
        ip_address = request.remote_addr  # 获取客户端 IP 地址

        # 插入登录记录
        login_record = LoginRecord(user_id=user.id, ip_address=ip_address)
        db.session.add(login_record)
        db.session.commit()

        return jsonify({"message": "Login successful", "access_token": access_token}), 200
    else:
        return jsonify({"message": "Invalid username or password."}), 401


# 获取所有持仓
@app.route('/get_holdings', methods=['GET'])
def get_holdings():
    holdings = Holding.query.all()
    holding_list = [
        {
            'stockName': holding.stock_name,
            'costPrice': holding.cost_price,
            'addedOn': holding.added_on
        }
        for holding in holdings
    ]
    return jsonify(holding_list)


# 添加持仓
@app.route('/add_holding/<stock_name>', methods=['POST'])
def add_holding(stock_name):
    tushare_interface = TushareInterface()
    stock_code = tushare_interface.get_code_by_name(stock_name)
    data = request.json
    cost_price = data.get('cost_price')

    if not cost_price:
        return jsonify({"message": "成本价和当前价是必需的"}), 400

    # 检查股票是否已存在
    existing_holding = Holding.query.filter_by(stock_name=stock_name).first()
    if existing_holding:
        return jsonify({"message": "持仓已存在"}), 400

    new_holding = Holding(
        stock_name=stock_name,
        cost_price=cost_price,

        stock_code=stock_code
    )
    db.session.add(new_holding)
    db.session.commit()

    return jsonify({"message": "持仓添加成功"}), 201


# 删除持仓
@app.route('/del_holding/<stock_name>', methods=['POST'])
def delete_holding(stock_name):
    holding = Holding.query.filter_by(stock_name=stock_name).first()
    if not holding:
        return jsonify({"message": "持仓不存在"}), 404

    db.session.delete(holding)
    db.session.commit()

    return jsonify({"message": "持仓删除成功"}), 200


class TradingRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stock_name = db.Column(db.String(100), nullable=False)
    direction = db.Column(db.String(10), nullable=False)  # 'buy' or 'sell'
    price = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f'<TradingRecord {self.stock_name} {self.direction} {self.price} {self.timestamp}>'


def insert_trade_record(new_record):
    if new_record is None:
        return
    try:
        trading_record = TradingRecord(stock_name=new_record.stock_name, direction=new_record.direction,
                                       price=new_record.price,
                                       timestamp=new_record.timestamp)
        db.session.add(trading_record)
        db.session.commit()
    except Exception as e:
        print(e)
        db.session.rollback()


# 获取所有交易记录的 API
@app.route('/trading_records', methods=['GET'])
def get_all_trading_records():
    # 获取前端传递的日期参数，格式为 YYYY-MM-DD
    date_str = request.args.get('date')  # 例如：2024-12-19
    print(f"Received date: {date_str}")  # 打印接收到的日期参数
    tushare_interface = TushareInterface()

    if date_str:
        try:
            # 将日期字符串转换为 datetime 对象
            date_start = datetime.datetime.strptime(date_str, '%Y-%m-%d')  # 当天的开始时间：2024-12-19 00:00:00
            date_end = date_start + datetime.timedelta(days=1)  # 第二天的开始时间：2024-12-20 00:00:00

            # 打印调试信息
            print(f"Start: {date_start}, End: {date_end}")

            # 按日期范围过滤交易记录
            records = TradingRecord.query.filter(
                TradingRecord.timestamp >= date_start,
                TradingRecord.timestamp < date_end
            ).all()
        except Exception as e:
            return jsonify({"error": f"Invalid date format or query issue: {str(e)}"}), 400
    else:
        # 如果没有提供日期参数，则返回所有记录
        records = TradingRecord.query.all()

    # 将查询结果转换为 JSON 格式，并格式化时间戳
    return jsonify([
        {
            "id": record.id,
            "stock_name": record.stock_name,
            "direction": record.direction,
            "price": record.price,
            "timestamp": record.timestamp.strftime('%Y-%m-%d %H:%M:%S'),  # 格式化为 YYYY-MM-DD HH:MM:SS
            "close_price": get_current_price(tushare_interface.get_code_by_name(record.stock_name))
        } for record in records
    ])


# with app.app_context():
#     # db.drop_all()  # This will delete everything
#     print('11111')
#     db.create_all()
#     print('22222')

if __name__ == "__main__":
    # 启动 Flask 应用
    app.run(host='0.0.0.0', port=5001)
