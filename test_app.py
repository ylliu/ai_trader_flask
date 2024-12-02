from unittest import TestCase

from app import get_time_share_data, sell_point_playback, add_stock, app, delete_stock, get_all_stocks


class Test(TestCase):
    def test_get_time_share_data(self):
        get_time_share_data('sh600628')

    def test_sell_point_playback(self):
        sell_point_playback('sz300001')

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
