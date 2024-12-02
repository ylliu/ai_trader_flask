import json

from flask import Flask, jsonify, request
import pandas as pd
import os
from flask_cors import CORS
from Ashare import get_price
from SimulatedClock import SimulatedClock
from train_model import TrainModel

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}})


# 数据存储路径

@app.route('/time_share_data/<code>', methods=['GET'])
def get_time_share_data(code):
    try:
        df = get_price(code, frequency='1m', count=241)
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
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 开始训练接口
@app.route('/start_train/<code>', methods=['POST'])
def start_train(code):
    try:
        # 从请求体中获取开始时间和结束时间
        request_data = request.get_json()
        start_time = request_data.get("start_time")
        end_time = request_data.get("end_time")
        action = request_data.get("action")

        if not start_time or not end_time:
            return jsonify({"error": "Start time and end time are required"}), 400

        # 模拟训练逻辑
        print(f"开始训练，股票代码：{code}")
        print(f"开始时间：{start_time}, 结束时间：{end_time}")
        train_model = TrainModel()
        train_model.save_data(code, start_time, end_time, action)
        train_model.retrain_with_all_data()
        # 训练逻辑可以包括数据过滤、模型训练等
        # 示例: 根据时间范围过滤数据
        # filtered_data = filter_data_by_time_range(code, start_time, end_time)

        # 返回训练成功的消息
        return jsonify({"message": f"Training started for stock {code} from {start_time} to {end_time}"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/playback_sell_point/<code>', methods=['POST'])
def sell_point_playback(code):
    train_model = TrainModel()
    train_model.retrain_with_all_data()
    train_model.save_data2(code, 500)
    clock = SimulatedClock()
    time = clock.get_current_time()
    sell_points = []
    while not clock.is_time_to_end():
        print(time)
        df = train_model.get_time_series_data('%s.csv' % code, time, 200)
        sell_point = train_model.code_sell_point_use_date(df, code)
        if sell_point is not None:
            sell_points.append(sell_point)
        time = clock.next()

    return jsonify(sell_points)


if __name__ == "__main__":
    # 启动 Flask 应用
    app.run(host='0.0.0.0', port=5000)
