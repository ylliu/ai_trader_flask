# -*- coding: utf-8 -*-
"""
申请开通QMT请添加微信咨询gjquant，获取更多资料访问https://miniqmt.com/
此代码脚本仅用于软件测试，不能用于实盘交易，以此代码进行交易本人不承担任何损失
"""
import logging
import os
import sys
import time
import pandas as pd
from xtquant.xttrader import XtQuantTrader  # 创建交易对象使用
from xtquant.xttype import StockAccount  # 订阅账户信息使用
from xtquant import xtconstant  # 执行交易的时候需要引入
from datetime import datetime  # 时间戳改为日期时间格式的时候使用

from xtquant import xtdata

from tushare_interface import TushareInterface


class XtTraderOrder:
    def __init__(self):
        # 设置日志
        self.setup_logger()
        # ——————————————————————————————————————————————————————————————————————————————————————————————————————
        # 设置你的path=''QMT安装路径信息，acc=''引号内填入你的账号
        path = r'D:\QMT\userdata_mini\userdata_mini'
        acc = "8883252929"
        # 创建交易对象
        session_id = int(time.time())
        self.xt_trader = XtQuantTrader(path, session_id)

        # xttrader连接miniQMT终端
        self.xt_trader.start()
        if self.xt_trader.connect() == 0:
            print('【软件终端连接成功！】')
        else:
            print('【软件终端连接失败！】', '\n 请运行并登录miniQMT.EXE终端。', '\n path=改成你的QMT安装路径')
        # 订阅账户信息
        self.ID = StockAccount(acc, 'STOCK')
        subscribe_result = self.xt_trader.subscribe(self.ID)
        if subscribe_result == 0:
            print('【账户信息订阅成功！】')
        else:
            print('【账户信息订阅失败！】', '\n 账户配置错误，检查账号是否正确。', '\n acct=""内填加你的账号')
            sys.exit()  # 如果运行环境，账户都没配置好，后面的代码就不执行

    def setup_logger(self):
        """配置日志记录器"""
        # 生成日志文件名，格式为 trader_record_YYYYMMDD_HHMMSS.log
        log_dir = "./log"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_filename = os.path.join(log_dir, f"trader_record_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.FileHandler(log_filename, encoding='utf-8'),  # 输出到文件
                logging.StreamHandler()  # 同时输出到控制台
            ]
        )
        self.logger = logging.getLogger("XtTraderOrder")

    def get_close_price_of(self, code):
        tushare = TushareInterface()
        daily_line = tushare.gat_realtime_data(code)
        return daily_line.close

    def get_account_profit_rate(self):
        total_asset = self.get_total_asset()
        print('总资产:', total_asset)
        # 打印汇总信息
        print('-' * 18, '【当日汇总】', '-' * 18)
        orders_df = self.orders_df()
        trades_df = self.trades_df()
        positions_df = self.positions_df()
        print(f"委托个数：{len(orders_df)}    成交个数：{len(trades_df)}    持仓数量：{len(positions_df)}")
        # 输出DataFrame
        print('-' * 18, "【订单信息】", '-' * 18)
        print(orders_df if not orders_df.empty else "无委托信息")

        print('-' * 18, "【成交信息】", '-' * 18)
        print(trades_df if not trades_df.empty else "无成交信息")

        print('-' * 18, "【持仓信息】", '-' * 18)
        print(positions_df if not positions_df.empty else "无持仓信息")
        pass

    def get_total_asset(self):
        # 打印账户信息
        asset = self.xt_trader.query_stock_asset(self.ID)
        return asset.total_asset

    def get_cash(self):
        # 打印账户信息
        asset = self.xt_trader.query_stock_asset(self.ID)
        return asset.cash

    # 委托信息
    def orders_df(self):
        orders_df = pd.DataFrame([(order.stock_code, order.order_volume, order.price, order.order_id, order.status_msg,
                                   datetime.fromtimestamp(order.order_time).strftime('%H:%M:%S'))
                                  for order in self.xt_trader.query_stock_orders(self.ID)],
                                 columns=['证券代码', '委托数量', '委托价格', '订单编号', '委托状态', '报单时间'])
        return orders_df

    # 成交信息
    def trades_df(self):
        trades_df = pd.DataFrame([(trade.stock_code, trade.traded_volume, trade.traded_price, trade.traded_amount,
                                   trade.order_id, trade.traded_id,
                                   datetime.fromtimestamp(trade.traded_time).strftime('%H:%M:%S'))
                                  for trade in self.xt_trader.query_stock_trades(self.ID)],
                                 columns=['证券代码', '成交数量', '成交均价', '成交金额', '订单编号', '成交编号',
                                          '成交时间'])
        return trades_df

    # 持仓信息
    def positions_df(self):
        positions_df = pd.DataFrame(
            [(position.stock_code, position.volume, position.can_use_volume, position.frozen_volume,
              position.open_price, position.market_value, position.on_road_volume,
              position.yesterday_volume)
             for position in self.xt_trader.query_stock_positions(self.ID)],
            columns=['证券代码', '持仓数量', '可用数量', '冻结数量', '开仓价格', '持仓市值',
                     '在途股份', '昨夜持股'])
        return positions_df

    def get_holdings(self):
        df = self.positions_df()
        non_zero_positions = df[df['持仓数量'] != 0]
        # 获取这些行的证券代码
        stock_codes = non_zero_positions['证券代码'].tolist()
        print(stock_codes)
        return stock_codes

    def buy_stock(self, code, price, cash):
        if self.get_position_pct() > 70:
            self.logger.info(f'position is over 70 not allowed to buy,buy code:{code},number:{100},price:{price}')
            return False
        number = 100
        if price * 100 > cash:
            self.logger.info(f'no enough cash,buy code:{code},number:{number},price:{price}')
            return False
        print(f'buy code:{code},number:{number},price:{price}')
        self.xt_trader.order_stock(self.ID, code, xtconstant.STOCK_BUY, number, xtconstant.FIX_PRICE, price)
        return True

    def sell_stock(self, code, number, price):
        self.logger.info(f'sell code:{code},number:{number},price:{price}')
        self.xt_trader.order_stock(self.ID, code, xtconstant.STOCK_SELL, number, xtconstant.FIX_PRICE, price)

    def get_position_pct(self):
        df = self.positions_df()
        non_zero_positions = df[df['持仓数量'] != 0]
        # 将持仓市值进行相加
        total_market_value = non_zero_positions['持仓市值'].sum()
        total_asset = self.get_total_asset()
        return round(total_market_value / total_asset * 100, 1)
#     # ——————————————————————————————————————————————————————————————————————————————————————————————————————
#
#
# # 设置你的path=''QMT安装路径信息，acc=''引号内填入你的账号
# path = r'D:\QMT\userdata_mini\userdata_mini'
# acc = "8883252929"
# # 创建交易对象
# session_id = int(time.time())
# xt_trader = XtQuantTrader(path, session_id)
#
# # xttrader连接miniQMT终端
# xt_trader.start()
# if xt_trader.connect() == 0:
#     print('【软件终端连接成功！】')
# else:
#     print('【软件终端连接失败！】', '\n 请运行并登录miniQMT.EXE终端。', '\n path=改成你的QMT安装路径')
# # 订阅账户信息
# ID = StockAccount(acc, 'STOCK')
# subscribe_result = xt_trader.subscribe(ID)
# if subscribe_result == 0:
#     print('【账户信息订阅成功！】')
# else:
#     print('【账户信息订阅失败！】', '\n 账户配置错误，检查账号是否正确。', '\n acct=""内填加你的账号')
#     sys.exit()  # 如果运行环境，账户都没配置好，后面的代码就不执行
# # ——————————————————————————————————————————————————————————————————————————————————————————————————————
# # 打印账户信息
# asset = xt_trader.query_stock_asset(ID)
# print('-' * 18, '【{0}】'.format(asset.account_id), '-' * 18)
# if asset: print(f"资产总额: {asset.total_asset}\n"
#                 f"持仓市值：{asset.market_value}\n"
#                 f"可用资金：{asset.cash}\n"
#                 f"在途资金：{asset.frozen_cash}")
#
#
# # time.sleep(1) #演示用
# # #——————————————————————————————————————————————————————————————————————————————————————————————————————
# # # ！！！注意，以下代码将启动账户进行交易，谨慎使用
# # POOL = '512660.SH'  #设置股票池（POOL）
# # BP = 0.834         #买入价格(BP)
# # BQ = 600      #买入数量(BQ)
# # CASH = asset.cash
# # BQALL = int((CASH / BP) // 1 * 100)
# #
# # SP = 2.55            #卖出价格(SP)
# # SQ = 2100          #卖出数量(SQ)
# #
# # SN = "策略"       #策略名称
# # PS = "备注"       #备注
# # # ！！！注意，以下代码将启动账户进行交易，谨慎使用
# # #下面两行删除"#"井号后，运行将以BP = “ ”的价格委托买入BQ = “ ” 股的，股票池为POOL = “ ” 执行交易买入/卖出委托，请谨慎使用
# #
# # #order_id = xt_trader.order_stock(ID, POOL, xtconstant.STOCK_BUY, BQALL, xtconstant.FIX_PRICE, BP) #买入
# # #order_id2 = xt_trader.order_stock(ID, POOL, xtconstant.STOCK_SELL, SQ, xtconstant.FIX_PRICE, SP) #卖出
# # #——————————————————————————————————————————————————————————————————————————————————————————————————————
# # 委托信息
# def orders_df():
#     orders_df = pd.DataFrame([(order.stock_code, order.order_volume, order.price, order.order_id, order.status_msg,
#                                datetime.fromtimestamp(order.order_time).strftime('%H:%M:%S'))
#                               for order in xt_trader.query_stock_orders(ID)],
#                              columns=['证券代码', '委托数量', '委托价格', '订单编号', '委托状态', '报单时间'])
#     return orders_df
#
#
# # 成交信息
# def trades_df():
#     trades_df = pd.DataFrame([(trade.stock_code, trade.traded_volume, trade.traded_price, trade.traded_amount,
#                                trade.order_id, trade.traded_id,
#                                datetime.fromtimestamp(trade.traded_time).strftime('%H:%M:%S'))
#                               for trade in xt_trader.query_stock_trades(ID)],
#                              columns=['证券代码', '成交数量', '成交均价', '成交金额', '订单编号', '成交编号',
#                                       '成交时间'])
#     return trades_df
#
#
# # 持仓信息
# def positions_df():
#     positions_df = pd.DataFrame([(position.stock_code, position.volume, position.can_use_volume, position.frozen_volume,
#                                   position.open_price, position.market_value, position.on_road_volume,
#                                   position.yesterday_volume)
#                                  for position in xt_trader.query_stock_positions(ID)],
#                                 columns=['证券代码', '持仓数量', '可用数量', '冻结数量', '开仓价格', '持仓市值',
#                                          '在途股份', '昨夜持股'])
#     return positions_df
#
#
# # 打印汇总信息
# print('-' * 18, '【当日汇总】', '-' * 18)
# orders_df = orders_df()
# trades_df = trades_df()
# positions_df = positions_df()
# print(f"委托个数：{len(orders_df)}    成交个数：{len(trades_df)}    持仓数量：{len(positions_df)}")
# # 输出DataFrame
# print('-' * 18, "【订单信息】", '-' * 18)
# print(orders_df if not orders_df.empty else "无委托信息")
#
# print('-' * 18, "【成交信息】", '-' * 18)
# print(trades_df if not trades_df.empty else "无成交信息")
#
# print('-' * 18, "【持仓信息】", '-' * 18)
# print(positions_df if not positions_df.empty else "无持仓信息")
