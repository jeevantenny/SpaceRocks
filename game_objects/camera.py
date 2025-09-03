import pygame as pg

from . import ObjectGroup


import debug
from math_functions import clamp, unit_vector








class Camera:
    __max_speed = 1000
    __wander_radius = 20
    def __init__(self, start_pos: pg.typing.Point):
        self.__position = pg.Vector2(start_pos)
        self.__velocity = pg.Vector2(0, 0)
        self.__following = True
        self.__target_pos = self.position



    
    @property
    def position(self) -> pg.Vector2:
        return self.__position.copy()



    def set_target(self, position: pg.typing.Point) -> None:
        self.__target_pos = pg.Vector2(position)


    def update(self) -> None:
        displacement = self.__target_pos-self.position
        direction = unit_vector(displacement)
        distance = displacement.magnitude()

        if self.__following:
            if distance < 5:
                self.set_position(self.__target_pos)
                self.__following = False
                self.clear_velocity()
            else:
                self.__velocity = direction*clamp((distance-self.__wander_radius)*0.2, 0, self.__max_speed)

        else:
            if distance > self.__wander_radius:
                self.__following = True

        
        self.__position += self.__velocity

    


    def capture(self, surface: pg.Surface, entities: ObjectGroup, lerp_amount=0.0) -> None:
        lerp_pos = self.lerp_position(lerp_amount)
        blit_offset = pg.Vector2(surface.size)*0.5 - lerp_pos

        entities.draw(surface, lerp_amount, blit_offset)
        if debug.debug_mode:
            pg.draw.rect(surface, "red", (*blit_offset, *surface.size), 1)
            pg.draw.circle(surface, "white", self.__target_pos+blit_offset, 2)
    


    def set_position(self, value: pg.typing.Point) -> None:
        self.__position = pg.Vector2(value)


    def lerp_position(self, lerp_amount: float) -> pg.Vector2:
        return self.position + self.__velocity*lerp_amount


    def clear_velocity(self) -> None:
        self.__velocity *= 0