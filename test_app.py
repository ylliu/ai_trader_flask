import datetime
from unittest import TestCase

from app import get_time_share_data, sell_point_playback, add_stock, app, delete_stock, get_all_stocks, \
    buy_point_playback, monitor_stocks, register, insert_trade_record, TradingRecord
from train_model import TraderRecord


class Test(TestCase):
    def test_get_time_share_data(self):
        with app.app_context():
            df = get_time_share_data('双林股份')

    def test_sell_point_playback(self):
        with app.app_context():
            sell_point_playback('视觉中国')

    def test_add_stock(self):
        with app.app_context():
            add_stock("华大九天")

    def test_del_stock(self):
        with app.app_context():
            delete_stock("sz301269")

    def test_get_all_stocks(self):
        with app.app_context():
            add_stock("")
            res = get_all_stocks()
            print(res.json)

    def test_buy_point_playback(self):
        with app.app_context():
            buy_point_playback("视觉中国")

    def test_monitor_stocks(self):
        with app.app_context():
            monitor_stocks()

    def test_insert_trade_record(self):
        with app.app_context():
            try:
                new_record = TraderRecord("华大九天", 'buy', 34.2, datetime.datetime(2024, 10, 11, 22, 00, 00))
                insert_trade_record(new_record)
            except Exception as e:
                print(e)
