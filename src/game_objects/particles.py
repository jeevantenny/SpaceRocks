"Game objects that don't effect the behavior of other objects but are used for visual effects."

import pygame as pg
import random
from math import sin, pi

from src.custom_types import Timer

from .components import *


__all__ = [
    "ShipSmoke",
    "DisplayText"
]



class ShipSmoke(ObjectAnimation, ObjectVelocity):
    "The smoke particle produced by the spaceship."

    progress_save_key="ship_thruster_smoke"

    def __init__(self, position: pg.typing.Point, velocity: pg.typing.Point):
        
        super().__init__(
            position=position,
            texture_map_path="smoke",
            anim_path="basic",
            controller_path="basic"
        )

        self.accelerate(velocity)
        self._angular_vel = random.randint(-6, 6)
        self.__lifetime = Timer(random.randint(12, 18), exec_after=self.kill).start()

    
    def __init_from_data__(self, object_data):
        self.__init__(object_data["position"], object_data["velocity"])
        self._angular_vel = object_data["angular_vel"]
        self.__lifetime = Timer(object_data["total_time"], exec_after=self.kill).start()
        self.__lifetime.advance(object_data["time_elapsed"])
        self._advance_animation(object_data["time_elapsed"])
    

    def get_data(self):
        data = super().get_data()
        data.update({
            "position": tuple(self.position),
            "velocity": tuple(self._velocity),
            "angular_vel": self._angular_vel,
            "total_time": self.__lifetime.duration,
            "time_elapsed": self.__lifetime.time_elapsed
        })
        return data


    def update(self):
        super().update()
        self.__lifetime.update()











class DisplayText(ObjectTexture):
    "Shows how many points were obtained from destroying an asteroid."
    save_entity_progress=False
    draw_layer = 5

    def __init__(self, position: pg.typing.Point, text_surface: pg.Surface):
        super().__init__(
            position=position,
            texture=text_surface
        )
        
        self.__lifetime = 12



    def update(self):
        super().update()

        self.__lifetime -= 1
        if self.__lifetime == 0:
            self.kill()
        
        self.position.y -= sin(self.__lifetime*pi/12)*2