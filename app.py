import json

from flask import Flask, jsonify, request
import pandas as pd
import os
from flask_cors import CORS
from Ashare import get_price

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}})


# 数据存储路径

@app.route('/time_share_data/<code>', methods=['GET'])
def get_time_share_data(code):
    try:
        # df = get_price(code, frequency='1m', count=241)
        # # 如果数据为空，返回400错误
        # if df.empty:
        #     return jsonify({"error": "No time share data available"}), 400
        # last_index = df.index[-1]
        # df = df.drop(last_index)
        # df.index.name = 'time'
        # df = df.reset_index()
        # df['time'] = df['time'].apply(lambda x: x.timestamp())
        # print(df)
        # # 选择要返回的列（time, open, close, high, low, volume）
        # result = df[['time', 'open', 'close', 'high', 'low', 'volume']].reset_index().to_dict(orient='records')
        # json_file_path = f'{code}_time_share_data.json'
        # with open(json_file_path, 'w') as json_file:
        #     json.dump(result, json_file)

        # 从 JSON 文件读取数据
        json_file_path = f'{code}_time_share_data.json'
        with open(json_file_path, 'r') as json_file:
            result = json.load(json_file)
        # 返回 JSON 格式的结果
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # 启动 Flask 应用
    app.run(host='0.0.0.0', port=5000)
