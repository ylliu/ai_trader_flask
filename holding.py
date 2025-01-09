import datetime

from database import db


class Holding(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stock_name = db.Column(db.String(50), unique=True, nullable=False)
    stock_code = db.Column(db.String(50), unique=True, nullable=False)
    cost_price = db.Column(db.Float, nullable=False)
    added_on = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f"<Holding {self.stock_name}>"
