from unittest import TestCase

from xt_trader_position_manager import XtTraderPositionManager, AccountProfitRate


class TestXtTraderPositionManager(TestCase):
    def setUp(self):
        """
        每个测试用例运行之前执行的初始化方法。
        可以在这里初始化 XtTrader 实例。
        """
        self.xt_trader = XtTraderPositionManager()

    def tearDown(self):
        """
        每个测试用例运行之后执行的清理方法。
        在这里执行清库操作，确保测试之间不会互相影响。
        """
        self.xt_trader.clear_account_profit_rate()

    def test_get_profit_rate(self):
        self.xt_trader.set_profit_rate('2025-01-03', 2.3)
        rate = self.xt_trader.get_profit_rate('2025-01-03')
        self.assertEqual(2.3, rate)

    def test_账户亏百分之五以上仓位降低到3层(self):
        self.xt_trader.set_profit_rate('2025-01-01', -5)
        self.xt_trader.set_profit_rate('2025-01-02', -3)
        self.xt_trader.set_profit_rate('2025-01-03', 1)
        allowed_positions = self.xt_trader.allowed_positions()
        self.assertEqual(0.3, allowed_positions)

    def test_账户连续亏损3笔以上不进行买入操作(self):
        self.xt_trader.set_profit_rate('2025-01-01', -5)
        self.xt_trader.set_profit_rate('2025-01-02', -3)
        self.xt_trader.set_profit_rate('2025-01-03', 1)
        self.xt_trader.set_profit_rate('2025-01-04', -1)
        self.xt_trader.set_profit_rate('2025-01-05', -1)
        self.xt_trader.set_profit_rate('2025-01-06', -1)
        allowed_positions = self.xt_trader.allowed_positions()
        self.assertEqual(0, allowed_positions)

    def test_账户单次出现百分之三以上的亏损仓位调整为3层(self):
        self.xt_trader.set_profit_rate('2025-01-01', -5)
        allowed_positions = self.xt_trader.allowed_positions()
        self.assertEqual(0.3, allowed_positions)

    def test_账户连续两次亏损仓位调整为半仓(self):
        self.xt_trader.set_profit_rate('2025-01-01', -1)
        self.xt_trader.set_profit_rate('2025-01-02', -2)
        allowed_positions = self.xt_trader.allowed_positions()
        self.assertEqual(0.5, allowed_positions)

    def test_正常仓位设置为7层(self):
        self.xt_trader.set_profit_rate('2025-01-01', -5)
        self.xt_trader.set_profit_rate('2025-01-02', -3)
        self.xt_trader.set_profit_rate('2025-01-03', 1)
        self.xt_trader.set_profit_rate('2025-01-04', -1)
        self.xt_trader.set_profit_rate('2025-01-05', -1)
        self.xt_trader.set_profit_rate('2025-01-06', -1)
        self.xt_trader.set_profit_rate('2025-01-07', 14)
        allowed_positions = self.xt_trader.allowed_positions()
        self.assertEqual(0.7, allowed_positions)

    def test_clear_account_profit_rate(self):
        # 添加测试数据
        self.xt_trader.set_profit_rate('2025-01-01', -5)
        self.xt_trader.set_profit_rate('2025-01-02', 3)
        self.xt_trader.set_profit_rate('2025-01-03', 1)

        # 确认表中有数据
        records_before_clear = self.xt_trader.session.query(AccountProfitRate).all()
        self.assertGreater(len(records_before_clear), 0)  # 确认有记录

        # 调用清除方法
        self.xt_trader.clear_account_profit_rate()

        # 确认表中无数据
        records_after_clear = self.xt_trader.session.query(AccountProfitRate).all()
        self.assertEqual(len(records_after_clear), 0)  # 确认记录被清除
