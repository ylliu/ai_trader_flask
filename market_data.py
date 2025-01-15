import akshare as ak


class MarketData:
    def __init__(self):
        self.stock_zh_a_spot_em_df = ak.stock_zh_a_spot_em()

    def count_negative_change(self):
        return (self.stock_zh_a_spot_em_df['涨跌幅'] < 0).sum()

    def count_positive_change(self):
        return (self.stock_zh_a_spot_em_df['涨跌幅'] > 0).sum()

cout = MarketData()
print(cout.count_negative_change())

