class GridStrategy2:
    def __init__(self, grid_levels):
        """
        初始化网格策略
        :param grid_levels: 网格层数
        """

        self.grid_levels = grid_levels
        self.has_initialized = False
        self.current_position = None
        self.grids = None

    def generate_grids(self, min_price, max_price):
        """
        生成价格网格
        """
        step = (max_price - min_price) / self.grid_levels
        self.grids = [min_price + step * i for i in range(self.grid_levels + 1)]

    def check_price(self, price):
        """
        检查当前价格并触发买卖
        :param price: 当前价格
        :return: 动作 ("buy", "sell" 或 None)
        """
        for i in range(len(self.grids) - 1):
            lower_bound = self.grids[i]
            upper_bound = self.grids[i + 1]
            if lower_bound <= price < upper_bound:
                # 如果尚未初始化，触发一次买入并标记为已初始化
                if not self.has_initialized:
                    self.has_initialized = True
                    self.current_position = i
                    return "buy"
                if i > self.current_position:
                    self.current_position = i
                    return "buy"  # 价格上升，买入
                elif i < self.current_position:
                    self.current_position = i
                    return "sell"  # 价格下降，卖出
        return None
