from unittest import TestCase

from SimulatedClock import SimulatedClock


class TestSimulatedClock(TestCase):
    def test_next(self):
        clock = SimulatedClock(code='sz300001')
        date = clock.get_current_time()
        print(date)
        clock.next()
        print(clock.get_current_time())
