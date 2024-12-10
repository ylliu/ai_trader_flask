import datetime

from Ashare import get_price

class SimulatedClockForTest:
    def __init__(self):
        self.current_time = datetime(2024, 12, 10, 9, 30)
        self.end_time = datetime(2024, 12, 10, 15, 0)

    def next(self):
        if self.current_time < self.end_time:
            self.current_time += datetime.timedelta(minutes=1)
            return self.current_time
        return None
class SimulatedClock:
    def __init__(self, start_time=None, code=None,point_count=None):
        self.code = code
        df = get_price(code, frequency='1m', count=point_count)
        last_index = df.index[-1]
        df = df.drop(last_index)
        df.index.name = 'time'
        df = df.reset_index()
        self.times = df['time']
        self.count = 0
        self.current_time = self.times.iloc[self.count]

    def next(self):
        """
        将时间推进1分钟，如果到达11:30则跳过到13:01
        """
        self.count += 1
        self.current_time = self.times.iloc[self.count]
        return self.current_time

    def get_current_time(self):
        return self.current_time

    def is_time_to_end(self):
        """
        判断是否已经到达结束时间
        """
        return self.count + 1 >= len(self.times)



# 示例使用
if __name__ == "__main__":
    clock = SimulatedClock()

    # 模拟每分钟推进一次
    while not clock.is_time_to_end():
        print("Current Time:", clock.get_current_time().strftime('%Y-%m-%d %H:%M:%S'))
        clock.next()  # 推进时间
