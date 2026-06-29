import pygame as pg
import unittest
from unittest.mock import Mock

from src.custom_types import Timer



class TestTimer(unittest.TestCase):

    def test_init(self):
        timer = Timer(25, True)
        self.assertEqual(timer.running, False)
        self.assertEqual(timer.duration, 25)
        self.assertEqual(timer.loop, True)
        self.assertEqual(timer.countdown, 0.0)
        self.assertEqual(timer.complete, True)
        self.assertEqual(timer.completion_amount, 1.0)

    def test_start(self):
        timer = Timer(25, True)
        self.assertEqual(timer.countdown, 0)
        timer.start()
        self.assertEqual(timer.countdown, 25)

    
    def test_running(self):
        timer = Timer(25)
        self.assertEqual(timer.running, False)
        timer.start()
        self.assertEqual(timer.running, True)
        timer.restart()
        self.assertEqual(timer.running, True)
        timer.stop()
        self.assertEqual(timer.running, False)

    def test_advance(self):
        timer = Timer(25).start()
        timer.advance(20)
        self.assertEqual(timer.countdown, 5)

    def test_advance_underflow(self):
        timer = Timer(25).start()
        timer.advance(30)
        self.assertEqual(timer.countdown, 0)

    def test_advance_overflow(self):
        timer = Timer(25).start()
        timer.advance(5)
        timer.advance(-10)
        self.assertEqual(timer.countdown, 25)

    def test_advance_loop(self):
        timer = Timer(25, True).start()
        timer.advance(30)
        self.assertEqual(timer.countdown, 20)
        timer.advance(-30)
        self.assertEqual(timer.countdown, 25)
    
    def test_update(self):
        timer = Timer(25)
        timer.update()
        self.assertEqual(timer.countdown, 0)
        # start method wasn't called so timer value should not decrement
        timer.start()
        timer.update()
        self.assertEqual(timer.countdown, 24)
        # Timer has started so time should decrement
    
    def test_update_speed_multiplier(self):
        timer = Timer(25).start()
        timer.update(3)
        self.assertEqual(timer.countdown, 22)
        timer.update(0.2)
        self.assertEqual(timer.countdown, 21.8)
    
    def test_callback(self):
        f = Mock()
        timer = Timer(25, exec_after=f).start()
        timer.update()
        timer.advance(24)
        f.assert_not_called()
        # Timer reached 0 but callback function should only be
        # invocated in update method.
        timer.update()
        f.assert_called_once_with()
    
    def test_callback_with_underflow(self):
        f = Mock()
        timer = Timer(25, True, f).start()
        timer.advance(100)
        f.assert_not_called()
        timer.update()
        f.assert_called_once_with()
        # Even though the time advanced 4 times the timer's duration
        # the callback function should only be invocated once.

    def test_restart(self) -> None:
        timer = Timer(25).start()
        timer.advance(20)
        timer.restart()
        self.assertEqual(timer.running, True)
        self.assertEqual(timer.countdown, 25)

    def test_stop(self) -> None:
        f = Mock()
        timer = Timer(25, exec_after=f).start()
        self.assertEqual(timer.running, True)
        timer.stop()
        self.assertEqual(timer.running, False)
        self.assertEqual(timer.complete, True)
        f.assert_not_called()
