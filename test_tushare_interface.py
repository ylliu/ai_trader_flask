from unittest import TestCase

from tushare_interface import TushareInterface


class TestTushareInterface(TestCase):
    def test_get_pre_close(self):
        tushare_interface = TushareInterface()
        tushare_interface.get_pre_close('300001.SZ')

