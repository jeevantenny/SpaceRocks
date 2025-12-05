import pygame as pg

import debug
from src.math_functions import unit_vector

from . import ObjectGroup








class Camera:
    "Moves to target position and captures an area of the world every frame."
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
        "Updates position of camera for every game tick."
        displacement = self.__target_pos-self.position
        direction = unit_vector(displacement)
        distance = displacement.magnitude()

        if self.__following:
            if distance < 5:
                self.set_position(self.__target_pos)
                self.__following = False
                self.clear_velocity()
            else:
                self.__velocity = direction*pg.math.clamp((distance-self.__wander_radius)*0.2, 0, self.__max_speed)

        else:
            if distance > self.__wander_radius:
                self.__following = True

        
        self.__position += self.__velocity

    


    def capture(self, output_surface: pg.Surface, entities: ObjectGroup, lerp_amount=0.0) -> None:
        "Draws game objects relative to the camera and blit them to the output surface."
        lerp_pos = self.lerp_position(lerp_amount)
        blit_offset = pg.Vector2(output_surface.size)*0.5 - lerp_pos

        entities.draw(output_surface, lerp_amount, blit_offset)
        if debug.Cheats.show_bounding_boxes:
            pg.draw.rect(output_surface, "red", (*blit_offset, *output_surface.size), 1)
            self.__draw_target_crosshair(output_surface)


    def __draw_target_crosshair(self, surface: pg.Surface) -> None:
        blit_offset = pg.Vector2(surface.size)*0.5 - self.position
        pos = self.__target_pos + blit_offset
        # pg.draw.circle(surface, "white", self.__target_pos+offset, 2)

        pg.draw.line(surface, "black", pos-(0, 4), pos+(0, 4), 2)
        pg.draw.line(surface, "black", pos-(4, 0), pos+(4, 0), 2)
        pg.draw.line(surface, "white", pos-(0, 3), pos+(0, 3))
        pg.draw.line(surface, "white", pos-(3, 0), pos+(3, 0))
    


    def set_position(self, value: pg.typing.Point) -> None:
        self.__position = pg.Vector2(value)

    
    def get_visible_area(self, area_size: pg.typing.Point) -> pg.Rect:
        rect = pg.Rect((0, 0), area_size)
        rect.center = self.position
        return rect


    def lerp_position(self, lerp_amount: float) -> pg.Vector2:
        "Position of camera after taking interpolation into account."
        return self.position + self.__velocity*lerp_amount


    def clear_velocity(self) -> None:
        self.__velocity *= 0