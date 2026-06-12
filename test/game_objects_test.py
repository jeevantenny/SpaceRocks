import pygame as pg
import unittest
from unittest.mock import patch, MagicMock

from src.game_objects import GameObject
from src.game_objects.spaceship import PlayerShip





class TestObject(GameObject):
    progress_save_key="test_game_object"

    def __init__(self, position: pg.typing.Point, a, b, c):
        super().__init__(position=position)

        self.a, self.b, self.c = 0, 0, 0


    def __init_from_data__(self, object_data):
        self.__init__(object_data["position"], object_data["a"], object_data["b"], object_data["c"])
    

    def get_data(self):
        return super().get_data() | {"a": self.a, "b": self.b, "c": self.c}




class GameObjectTest(unittest.TestCase):
    game_object: GameObject


    def test_init(self):
        game_object = GameObject(position=(80, 90))
        self.assertEqual(game_object.position.x, 80)
        self.assertEqual(game_object.position.y, 90)



    def test_init_from_data(self):
        object1 = TestObject((80, 90), 6, 3, 5)

        data = object1.get_data()
        object2 = GameObject.init_from_data(data)

        self.assertIsInstance(object2, TestObject)
        self.assertEqual(object2.position.x, 80)
        self.assertEqual(object2.position.y, 90)
        self.assertEqual(object2.a, object1.a)
        self.assertEqual(object2.b, object1.b)
        self.assertEqual(object2.c, object1.c)