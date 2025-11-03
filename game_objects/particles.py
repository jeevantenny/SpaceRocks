"Game objects that don't effect the behavior of other objects but are used for visual effects."

import pygame as pg
import random
from math import sin, pi

from ui.font import small_font

from .components import *


__all__ = [
    "ShipSmoke",
    "DisplayPoint"
]



class ShipSmoke(ObjectAnimation, ObjectVelocity):
    "The smoke particle produced by the spaceship."
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











class DisplayPoint(ObjectTexture):
    "Shows how many points were obtained from destroying an asteroid."
    save_entity_progress=False
    draw_layer = 5

    def __init__(self, position: pg.typing.Point, points: int, combo=0):
        text = f"+{points+combo}"
        if combo:
            text = f"COMBO {text}"

        texture = small_font.render(text, color_a="#dd6644" if combo else "#eeeeee", cache=False)

        super().__init__(
            position=position,
            texture=texture
        )
        
        self.__lifetime = 12



    def update(self):
        super().update()

        self.__lifetime -= 1
        if self.__lifetime == 0:
            self.kill()
        
        self.position.y -= sin(self.__lifetime*pi/12)*2