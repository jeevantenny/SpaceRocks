import pygame as pg
import unittest

from src.game import GameEngine



class TestEngine(unittest.TestCase):
    game: GameEngine

    def setUp(self):
        self.game = GameEngine().start()

    def tearDown(self):
        self.game.quit()

    @unittest.skip
    def test_pygame_initialization(self):
        """Verify that the engine modules core initialized correctly."""
        self.assertTrue(pg.get_init())
        self.assertTrue(pg.display.get_init())