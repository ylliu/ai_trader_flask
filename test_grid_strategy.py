from unittest import TestCase

from grid_strategy import GridStrategy
from train_model import TrainModel


class Test(TestCase):
    def test_grid_strategy_should_buy_when_price_up(self):
        grid_strategy = GridStrategy()
        train_model = TrainModel()
        train_model.save_data2('sz300803', 241)
        expect_buy_time = grid_strategy.simulate_grid_trading_from_csv('sz300803.csv', '10:26', 'buy')
        self.assertEqual('10:42', expect_buy_time)

    def test_grid_strategy_should_sell_when_price_down(self):
        grid_strategy = GridStrategy()
        train_model = TrainModel()
        train_model.save_data2('sz301536', 241)
        expect_sell_time = grid_strategy.simulate_grid_trading_from_csv('sz301536.csv', '13:27', 'sell')
        self.assertEqual('14:24', expect_sell_time)
