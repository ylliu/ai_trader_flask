from database import db


class StrategyConfig(db.Model):
    __tablename__ = 'strategy_config'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    is_sell_only = db.Column(db.Boolean, default=False)  # 只卖不买配置

    def to_dict(self):
        return {
            "id": self.id,
            "isSellOnly": self.is_sell_only
        }
