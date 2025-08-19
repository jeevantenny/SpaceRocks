import pygame as p
import random

from file_processing import assets, load_json


from .components import *




class ShipSmoke(ObjectAnimation, ObjectVelocity):
    __texture_map_path = "particles.texture_map"
    def __init__(self, position: p.typing.Point, velocity: p.typing.Point):
        texture_map = {}
        for name, texture in assets.load_texture_map(self.__texture_map_path).items():
            if "smoke" in name:
                texture_map[name.removeprefix("smoke")] = texture
        
        super().__init__(
            position=position,
            texture_map=texture_map,
            anim_data=load_json(f"{self._anim_data_dir}/basic.animation"),
            controller_data=load_json(f"{self._controller_data_dir}/basic.anim_controller")
        )

        self.accelerate(velocity)
        self._angular_vel = random.randint(-6, 6)
        self.__lifetime = random.randint(12, 18)


    def update(self):
        super().update()
        self.__lifetime -= 1
        if self.__lifetime == 0:
            self.kill()