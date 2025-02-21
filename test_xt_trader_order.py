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
        res = xt_trader_order.buy_stock('600673.SH', 12.37, cash)
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

    def test_get_stock_position_pct(self):
        xt_trader_order = XtTraderOrder()
        pct = xt_trader_order.get_stock_position_pct('002851.SZ')
        self.assertEqual(22.8, pct)
        pct = xt_trader_order.get_stock_position_pct('603068.SZ')
        self.assertEqual(0.0, pct)

    def test_get_stock_position_number(self):
        xt_trader_order = XtTraderOrder()
        number = xt_trader_order.get_stock_position_number('300058.SZ')
        self.assertEqual(600, number)

    def test_get_mini_number(self):
        xt_trader_order = XtTraderOrder()
        res = xt_trader_order.get_mini_number(100, 6.0)
        self.assertEqual(res, 800)
        res = xt_trader_order.get_mini_number(100, 28.0)
        self.assertEqual(res, 200)

    def test_get_mini_sell_number(self):
        xt_trader_order = XtTraderOrder()
        res = xt_trader_order.get_mini_sell_number(6.0)
        self.assertEqual(res, 500)
        res = xt_trader_order.get_mini_sell_number(40.0)
        self.assertEqual(res, 100)
        res = xt_trader_order.get_mini_sell_number(71.0)
        self.assertEqual(res, 100)

    def test_get_available_holdings(self):
        xt_trader_order = XtTraderOrder()
        res = xt_trader_order.get_available_holdings()
        for stock in res:
            print(stock.code)
            print(stock.available_number)

    def test_get_open_price(self):
        xt_trader_order = XtTraderOrder()
        res = xt_trader_order.get_open_price('002639.SZ')
        print(res)
