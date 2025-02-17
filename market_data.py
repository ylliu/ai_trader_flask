from datetime import datetime

import akshare as ak


class MarketData:

    def __init__(self):
        self.stock_zh_a_spot_em_df = None
        self.UP_COUNT_MAX = 4000
        self.UP_COUNT_MIN = 1500

    def get_all_market_info(self):
        self.stock_zh_a_spot_em_df = ak.stock_zh_a_spot_em()
        print(self.stock_zh_a_spot_em_df)

    def count_negative_change(self):
        return (self.stock_zh_a_spot_em_df['涨跌幅'] < 0).sum()

    def count_positive_change(self):
        return (self.stock_zh_a_spot_em_df['涨跌幅'] > 0).sum()

    def calc_buy_threshold(self):
        # if self.count_positive_change() > self.UP_COUNT_MAX:
        #     return 0.60
        # if self.count_positive_change() < self.UP_COUNT_MIN:
        #     return 0.68
        # else:
            return 0.64

    def calc_sell_threshold(self):
        # if self.count_positive_change() > self.UP_COUNT_MAX:
        #     return 0.68
        # if self.count_positive_change() < self.UP_COUNT_MIN:
        #     return 0.60
        # else:
            return 0.64

    def get_up_data(self, date):
        stock_zt_pool_em_df = ak.stock_zt_pool_em(date=date)
        print(stock_zt_pool_em_df)

    def get_down_data(self):
        current_date = datetime.now().date()
        # 将日期转换为字符串，格式为 YYYYMMDD
        date_str = current_date.strftime("%Y%m%d")
        stock_dt_pool_em_df = ak.stock_zt_pool_dtgc_em(date=date_str)
        return len(stock_dt_pool_em_df)

    def calc_stop_loss_time(self):
        stop_loss_time = '14:40'
        if self.get_down_data() > 30:
            stop_loss_time = "10:30"
        return stop_loss_time
