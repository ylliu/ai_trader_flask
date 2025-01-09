from unittest import TestCase

from xt_trader_order import XtTraderOrder


class TestXtTraderOrder(TestCase):
    def test_get_account_profit_rate(self):
        xt_trader_order = XtTraderOrder()
        rate = xt_trader_order.get_account_profit_rate('2025-01-08')
        self.assertEqual(2.07, rate)
