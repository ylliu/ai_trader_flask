from unittest import TestCase

from xt_trader_order import XtTraderOrder


class TestXtTraderOrder(TestCase):
    def test_get_account_profit_rate(self):
        xt_trader_order = XtTraderOrder()
        rate = xt_trader_order.get_account_profit_rate()
        self.assertEqual(0.42, rate)

    def test_get_price_of(self):
        xt_trader_order = XtTraderOrder()
        df = xt_trader_order.get_close_price_of('301536.SZ')
        print(df)

    def test_buy_stock_when_no_enough_cash(self):
        xt_trader_order = XtTraderOrder()
        cash = 9000
        res = xt_trader_order.buy_stock('300570.SZ', 96.34, cash)
        self.assertEqual(False, res)

    def test_buy_stock_when_have_enough_cash(self):
        xt_trader_order = XtTraderOrder()
        cash = 10000
        res = xt_trader_order.buy_stock('300570.SZ', 96.34, cash)
        self.assertEqual(True, res)

    def test_get_holdings(self):
        xt_trader_order = XtTraderOrder()
        stocks = xt_trader_order.get_holdings()
        self.assertEqual(2, len(stocks))

    def test_get_position_pct(self):
        xt_trader_order = XtTraderOrder()
        pct = xt_trader_order.get_position_pct()
        self.assertEqual(57.7, pct)
