import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()  # 不绑定 app，仅定义 SQLAlchemy 实例


class TradingRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stock_name = db.Column(db.String(100), nullable=False)
    direction = db.Column(db.String(10), nullable=False)  # 'buy' or 'sell'
    price = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f'<TradingRecord {self.stock_name} {self.direction} {self.price} {self.timestamp}>'
