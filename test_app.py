import datetime
from unittest import TestCase

from app import get_time_share_data, sell_point_playback, add_stock, app, delete_stock, get_all_stocks, \
    buy_point_playback, monitor_stocks, register, monitor_holdings_stocks, insert_trade_record, \
    monitor_my_holding_stocks_sell_point, monitor_selected_stocks_buy_point
from train_model import TrainModel, TraderRecord


class Test(TestCase):
    def test_get_time_share_data(self):
        with app.app_context():
            df = get_time_share_data('双林股份')

    def test_sell_point_playback(self):
        with app.app_context():
            sell_point_playback('软通动力')

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
            buy_point_playback("麦格米特")

    def test_monitor_stocks(self):
        with app.app_context():
            monitor_stocks()

    def test_monitor_holdings_stocks(self):
        with app.app_context():
            train_model = TrainModel()
            time = datetime.datetime.now()

            current_time = time.replace(second=0, microsecond=0)
            monitor_holdings_stocks(current_time, train_model)

    def test_insert_trade_record(self):
        with app.app_context():
            try:
                new_record = TraderRecord("华大九天", 'buy', 34.2, datetime.datetime(2024, 12, 19, 22, 00, 00))
                insert_trade_record(new_record)
            except Exception as e:
                print(e)

    def test_monitor_my_holding_stocks_sell_point(self):
        with app.app_context():
            current_time = datetime.datetime(2025, 1, 9, 9, 49, 00)
            train_model = TrainModel()
            train_model.retrain_with_all_sell_data()
            monitor_my_holding_stocks_sell_point(current_time, train_model)

    def test_monitor_selected_stocks_buy_point(self):
        with app.app_context():
            current_time = datetime.datetime(2025, 1, 9, 9, 50, 00)
            train_model = TrainModel()
            train_model.retrain_with_all_buy_data()
            monitor_selected_stocks_buy_point(current_time, train_model)
