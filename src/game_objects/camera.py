import pygame as pg

import debug
from src.math_functions import unit_vector, format_angle, sign
from src.file_processing import assets

from . import ObjectGroup
from .components import ObjectVelocity








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


    def get_target(self) -> pg.Vector2:
        return self.__target_pos.copy()


    def set_target(self, position: pg.typing.Point) -> None:
        self.__target_pos.xy = position

    
    def set_velocity(self, value: pg.typing.Point) -> None:
        self.__velocity.xy = value


    def reset_motion(self) -> None:
        self.set_velocity((0, 0))


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
            blit_offset = pg.Vector2(output_surface.size)*0.5 - self.__position
            self._draw_crosshair(output_surface, self.__target_pos+blit_offset)


    def _draw_crosshair(self, surface: pg.Surface, position: pg.typing.Point) -> None:
        pg.draw.line(surface, "black", position-(0, 4), position+(0, 4), 3)
        pg.draw.line(surface, "black", position-(4, 0), position+(4, 0), 3)
        pg.draw.line(surface, "white", position-(0, 3), position+(0, 3))
        pg.draw.line(surface, "white", position-(3, 0), position+(3, 0))
    


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








class RotoZoomCamera(Camera):
    __rotation_speed = 8
    __rotation_acceleration = 1
    def __init__(self, start_pos):
        super().__init__(start_pos)
        self.__rotation = 0
        self.__target_rotation = 0
        self.__angular_vel = 0
        self.__zoom = 1.0


    def get_rotation(self) -> int:
        return self.__rotation
    
    def get_lerp_rotation(self, lerp_amount: float) -> float:
        return format_angle(self.__rotation-self.__angular_vel*(1-lerp_amount))
    
    def set_rotation(self, value: int) -> None:
        self.__rotation = format_angle(int(value))

    def set_target_rotation(self, rotation: int) -> None:
        self.__target_rotation = format_angle(int(rotation))

    def set_angular_vel(self, value: int) -> None:
        self.__angular_vel = pg.math.clamp(value, -self.__rotation_speed, self.__rotation_speed)
        
    def get_zoom(self) -> float:
        return self.__zoom
    
    def set_zoom(self, zoom: float) -> None:
        if zoom < 0.5:
            raise ValueError("Camera zoom cannot be less than 0.5")
        self.__zoom = zoom
    
    def rotate(self, amount: int) -> None:
        self.set_rotation(self.__rotation+amount)

    def reset_motion(self) -> None:
        super().reset_motion()
        self.set_angular_vel(0)
    
    def update(self):
        super().update()
        difference = int(self.__target_rotation-self.__rotation)
        amount = abs(difference)
        direction = sign(difference)
        if amount > 180:
            amount = 360 - amount
            direction *= -1

        target_vel = direction*pg.math.clamp(int(amount*0.1), 1, self.__angular_vel*direction+1)
        self.set_angular_vel(target_vel)
        self.rotate(self.__angular_vel)



    def capture(self, output_surface, entities, lerp_amount=0):
        scaled_surface = assets.colorkey_surface(pg.Vector2(output_surface.size)*self.__zoom)
        camera_lerp_pos = self.lerp_position(lerp_amount)
        camera_lerp_rotation = self.get_lerp_rotation(lerp_amount)
        blit_offset = pg.Vector2(scaled_surface.size)*0.5 - camera_lerp_pos

        for entity in entities.get_draw_order():
            if isinstance(entity, ObjectVelocity):
                entity_pos: pg.Vector2 = entity.get_lerp_pos(lerp_amount)
            else:
                entity_pos = entity.position

            blit_pos = entity_pos - camera_lerp_pos
            blit_pos.rotate_ip(-camera_lerp_rotation)
            blit_pos += camera_lerp_pos - entity_pos + blit_offset
            entity.draw(
                scaled_surface, lerp_amount,
                blit_pos,
                -camera_lerp_rotation if not entity.ignore_camera_rotation else 0)
            
        output_surface.blit(pg.transform.scale(scaled_surface, output_surface.size))

        if debug.Cheats.show_bounding_boxes:
            crosshair_pos = (self.get_target()-self.position).rotate(-self.__rotation) + pg.Vector2(output_surface.size)*0.5
            self._draw_crosshair(output_surface, crosshair_pos)
    