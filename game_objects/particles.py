import pygame as pg
import random

from file_processing import assets, load_json


from .components import *




class ShipSmoke(ObjectAnimation, ObjectVelocity):
    save_entity_progress=False
    def __init__(self, position: pg.typing.Point, velocity: pg.typing.Point):
        
        super().__init__(
            position=position,
            texture_map_path="smoke",
            anim_path="basic",
            controller_path="basic"
        )

        self.accelerate(velocity)
        self._angular_vel = random.randint(-6, 6)
        self.__lifetime = random.randint(12, 18)


    def update(self):
        super().update()
        self.__lifetime -= 1
        if self.__lifetime == 0:
            self.kill()