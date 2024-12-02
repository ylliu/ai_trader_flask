from unittest import TestCase

from app import get_time_share_data, sell_point_playback


class Test(TestCase):
    def test_get_time_share_data(self):
        get_time_share_data('sh600628')


    def test_sell_point_playback(self):
        sell_point_playback('sz300001')
