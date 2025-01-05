import calendar

from sqlalchemy import create_engine, Column, String, Float, Date, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class AccountProfitRate(Base):
    """
    定义 accountProfit 数据库表
    """
    __tablename__ = 'account_profit_rate'

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, unique=True, nullable=False)
    profit_rate = Column(Float, nullable=False)


# 创建数据库
engine = create_engine('sqlite:///trader.db')  # SQLite 数据库，文件名为 trader.db
Base.metadata.create_all(engine)  # 创建表

# 创建会话
Session = sessionmaker(bind=engine)
session = Session()

from datetime import datetime


class XtTrader:
    def __init__(self):
        # 初始化数据库会话
        self.session = session

    def set_profit_rate(self, date, profit_rate):
        """
        设置某个日期的收益率。
        :param date: 日期字符串，格式为 'YYYY-MM-DD'
        :param profit_rate: 收益率 (float)
        """
        # 转换日期为 datetime.date 对象
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()

        # 检查是否已存在该日期记录
        record = self.session.query(AccountProfitRate).filter_by(date=date_obj).first()
        if record:
            # 更新记录
            record.profit_rate = profit_rate
        else:
            # 插入新记录
            new_record = AccountProfitRate(date=date_obj, profit_rate=profit_rate)
            self.session.add(new_record)

        self.session.commit()

    def get_profit_rate(self, date):
        """
        获取某个日期的收益率。
        :param date: 日期字符串，格式为 'YYYY-MM-DD'
        :return: 收益率 (float)，如果没有记录则返回 None
        """
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        record = self.session.query(AccountProfitRate).filter_by(date=date_obj).first()
        return record.profit_rate if record else None

    def get_last_day_of_month(self, year, month):
        """
        获取指定年份和月份的最后一天。
        :param year: 年份 (int)
        :param month: 月份 (int)
        :return: 最后一天 (datetime.date)
        """
        last_day = calendar.monthrange(year, month)[1]
        return datetime(year, month, last_day).date()

    def calculate_monthly_profit(self, year, month):
        """
        计算指定年份和月份的累计收益。
        :param year: 年份 (int)
        :param month: 月份 (int)
        :return: 月累计收益率 (float)
        """
        start_date = datetime(year, month, 1).date()
        end_date = self.get_last_day_of_month(year, month)  # 获取当月最后一天

        # 查询当月的所有记录
        records = self.session.query(AccountProfitRate).filter(
            AccountProfitRate.date.between(start_date, end_date)
        ).all()

        # 累加收益率
        return sum(record.profit_rate for record in records)

    def allowed_positions(self):
        """
        根据账户收益情况计算允许的仓位比例。
        - 如果连续亏损 3 笔以上，仓位设置为 0。
        - 如果最近一个月累计收益亏损超过 5%，仓位设置为 3 层（30%）。
        :return: 仓位比例 (float)
        """
        # 获取最新的一条记录
        latest_record = (
            self.session.query(AccountProfitRate)
            .order_by(AccountProfitRate.date.desc())
            .first()
        )

        if latest_record and latest_record.profit_rate < -3:
            # 如果单次亏损超过 3%
            return 0.3  # 仓位调整为 3 层

        # 如果连续亏损 3 笔以上，禁止买入（仓位为 0）
        if self.has_consecutive_losses(num_losses=3):
            return 0.0
        # 如果连续亏损 2 笔以上，禁止买入（仓位为 0）
        if self.has_consecutive_losses(num_losses=2):
            return 0.5

        # 检查最近一个月的累计收益
        today = datetime.now()
        monthly_profit = self.calculate_monthly_profit(today.year, today.month)

        # 如果累计收益率亏损超过 5%，设置仓位为 3 层
        if monthly_profit < -5:
            return 0.3

        # 默认仓位为全仓
        return 0.7

    def has_consecutive_losses(self, num_losses=3):
        """
        判断最近是否存在连续亏损 num_losses 笔以上。
        :param num_losses: 连续亏损的次数 (默认值为 3)
        :return: 如果存在连续亏损则返回 True，否则返回 False
        """
        # 按日期从最近到最早查询最近 num_losses 条记录
        records = self.session.query(AccountProfitRate).order_by(AccountProfitRate.date.desc()).limit(num_losses).all()

        consecutive_losses = 0

        # 遍历记录，检查是否全部为亏损
        for record in records:
            if record.profit_rate < 0:  # 如果是亏损
                consecutive_losses += 1
            else:
                break  # 一旦遇到非亏损记录，退出循环

        return consecutive_losses >= num_losses

    def clear_account_profit_rate(self):
        """
        清除 AccountProfitRate 表中的所有记录。
        """
        self.session.query(AccountProfitRate).delete()
        self.session.commit()
