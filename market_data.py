import akshare as ak


class MarketData:

    def __init__(self):
        self.stock_zh_a_spot_em_df = None
        self.UP_COUNT_MAX = 4000
        self.UP_COUNT_MIN = 1500

    def get_all_market_info(self):
        self.stock_zh_a_spot_em_df = ak.stock_zh_a_spot_em()

    def count_negative_change(self):
        return (self.stock_zh_a_spot_em_df['涨跌幅'] < 0).sum()

    def count_positive_change(self):
        return (self.stock_zh_a_spot_em_df['涨跌幅'] > 0).sum()

    def calc_buy_threshold(self):
        if self.count_positive_change() > self.UP_COUNT_MAX:
            return 0.60
        if self.count_positive_change() < self.UP_COUNT_MIN:
            return 0.68
        else:
            return 0.64

    def calc_sell_threshold(self):
        if self.count_positive_change() > self.UP_COUNT_MAX:
            return 0.68
        if self.count_positive_change() < self.UP_COUNT_MIN:
            return 0.60
        else:
            return 0.64
