from unittest import TestCase

from train_model import TrainModel


class TestTrainModel(TestCase):
    def test_select_count(self):
        train_model = TrainModel()
        print(train_model.select_count())

    def test_create_directories_if_not_exists(self):
        train_model = TrainModel()
        train_model.create_directories_if_not_exists()
