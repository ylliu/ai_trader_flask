import datetime
from unittest import TestCase

from app import get_time_share_data, sell_point_playback, add_stock, app, delete_stock, get_all_stocks, \
    buy_point_playback, monitor_stocks, register, monitor_holdings_stocks
from train_model import TrainModel


class Test(TestCase):
    def test_get_time_share_data(self):
        with app.app_context():
            df = get_time_share_data('双林股份')

    def test_sell_point_playback(self):
        with app.app_context():
            sell_point_playback('国盛金控')

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
            buy_point_playback("沃尔核材")

    def test_monitor_stocks(self):
        with app.app_context():
            monitor_stocks()

    def test_monitor_holdings_stocks(self):
        with app.app_context():
            train_model = TrainModel()
            time = datetime.datetime.now()

            current_time = time.replace(second=0, microsecond=0)
            monitor_holdings_stocks(current_time, train_model)
