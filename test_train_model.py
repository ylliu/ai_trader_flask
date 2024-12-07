from unittest import TestCase

from train_model import TrainModel


class TestTrainModel(TestCase):
    def test_select_count(self):
        train_model = TrainModel()
        print(train_model.select_count())

    def test_create_directories_if_not_exists(self):
        train_model = TrainModel()
        train_model.create_directories_if_not_exists()

    def test_save_data_of_buy_point(self):
        train_model = TrainModel()
        train_model.save_data('sz300100', '2024-12-06 09:37:00', '2024-12-06 09:41:00', train_model.BUY_POINT)
        train_model.save_data('sz002460', '2024-12-06 10:00:00', '2024-12-06 10:05:00', train_model.BUY_POINT)
        train_model.save_data('sz002213', '2024-12-06 10:00:00', '2024-12-06 10:05:00', train_model.BUY_POINT)

    def test_sell_point_predict(self):
        train_model = TrainModel()
        train_model.retrain_with_all_buy_data()

