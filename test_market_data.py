from unittest import TestCase

from market_data import MarketData


class TestMarketData(TestCase):
    def test_calc_sell_threshold(self):
        market_data = MarketData()
        market_data.get_all_market_info()
        res = market_data.calc_sell_threshold()
        self.assertEqual(0.64, res)

    def test_get_up_data(self):
        market_data = MarketData()
        market_data.get_up_data('20250117')

    def test_get_down_data(self):
        market_data = MarketData()
        count = market_data.get_down_data()
        self.assertEqual(2, count)
