from unittest import TestCase

from tushare_interface import TushareInterface


class TestTushareInterface(TestCase):
    def test_get_pre_close(self):
        tushare_interface = TushareInterface()
        tushare_interface.get_pre_close('300001.SZ')

    def test_convert_stock_code_to_dot_s(self):
        tushare_interface = TushareInterface()
        code = tushare_interface.convert_stock_code_to_dot_s('sz300001')
        self.assertEqual('300001.SZ', code)
        code = tushare_interface.convert_stock_code_to_dot_s('sh600001')
        self.assertEqual('600001.SH', code)
