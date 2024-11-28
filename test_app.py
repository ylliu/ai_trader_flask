from unittest import TestCase

from app import get_time_share_data


class Test(TestCase):
    def test_get_time_share_data(self):
        get_time_share_data('sh600628')
