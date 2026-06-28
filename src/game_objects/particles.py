"Game objects that don't effect the behavior of other objects but are used for visual effects."

import pygame as pg
from functools import partial
import random
from math import sin, pi
from typing import Callable

from src.custom_types import Timer

from . import ObjectGroup
from .components import *


__all__ = [
    "ShipSmoke",
    "DisplayText"
]


type ParticleFactory = Callable[[pg.typing.Point, pg.typing.Point, int, int], "Particle"]


class Particle(ObjectVelocity, ObjectAnimation):
    progress_save_key = "particle"

    @classmethod
    def get_factory(cls, texture_map_path: str, draw_layer: int, persistent=False) -> ParticleFactory:
        return partial(cls, texture_map_path, draw_layer=draw_layer, persistent=persistent)

    def __init__(
            self,
            texture_map_path: str,
            position: pg.typing.Point,
            velocity: pg.typing.Point,
            lifetime: int,
            rotation=0,
            draw_layer=0,
            persistent=False
        ):

        super().__init__(
            position=position,
            velocity=velocity,
            texture_map_path=texture_map_path,
            anim_path="basic",
            controller_path="basic"
        )

        self.__texture_map_path = texture_map_path
        self.__lifetime = Timer(lifetime, exec_after=self.kill).start()
        self.set_angular_vel(rotation)

        self._layer = draw_layer
        if not persistent:
            self.progress_save_key = None

    
    def __init_from_data__(self, object_data):
        self.__init__(
            object_data["texture_map_path"],
            object_data["position"],
            object_data["velocity"],
            object_data["lifetime"],
            object_data["angular_vel"],
            object_data["draw_layer"],
            True
        )
        self._advance_animation(object_data["time_elapsed"])
    

    def get_data(self):
        data = super().get_data()
        data.update({
            "texture_map_path": self.__texture_map_path,
            "position": tuple(self.position),
            "velocity": tuple(self._velocity),
            "lifetime": self.__lifetime.countdown,
            "angular_vel": self._angular_vel,
            "draw_layer": self._layer,
            "time_elapsed": self.__lifetime.time_elapsed
        })
        return data


    def update(self):
        super().update()
        self.__lifetime.update()
    




class Emitter:
    def __init__(
            self,
            particle_factory: ParticleFactory,
            object_group: ObjectGroup,
            spawn_interval: int,
            speed: int | tuple[int, int],
            lifetime: int | tuple[int, int],
            rotation: int | tuple[int, int] = 0
            ):
        self.__particle_factory = particle_factory
        self.__object_group = object_group
        self.__spawn_interval = Timer(spawn_interval)

        self.__speed = speed
        self.__lifetime = lifetime
        self.__rotation = rotation

    def emit(self, origin: pg.typing.Point, velocity_offset: pg.typing.Point = (0, 0)) -> None:
        self.__spawn_interval.update()
        if self.__spawn_interval.complete:
            self.__spawn_particle(origin, velocity_offset)
            self.__spawn_interval.restart()


    def __spawn_particle(self, origin: pg.typing.Point, velocity_offset: pg.typing.Point) -> None:
        velocity = pg.Vector2(0, self.__get_speed())
        velocity.rotate_ip(random.randint(0, 356))

        particle = self.__particle_factory(
            origin,
            velocity+velocity_offset,
            self.__get_lifetime(),
            self.__get_rotation()
        )
        self.__object_group.add(particle)
    

    def __get_speed(self) -> int:
        if isinstance(self.__speed, int):
            return self.__speed
        else:
            return random.randint(*self.__speed)
    
    def __get_lifetime(self) -> int:
        if isinstance(self.__lifetime, int):
            return self.__lifetime
        else:
            return random.randint(*self.__lifetime)
    
    def __get_rotation(self) -> int:
        if isinstance(self.__rotation, int):
            return self.__rotation
        else:
            return random.randint(*self.__rotation)





class ShipSmoke(ObjectAnimation, ObjectVelocity):
    "The smoke particle produced by the spaceship."
    save_entity_progress=True
    _layer=6

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
    _layer = 5
    ignore_camera_rotation=True

    def __init__(self, position: pg.typing.Point, text_surface: pg.Surface, y_offset=0):
        super().__init__(
            position=position,
            texture=text_surface
        )
        
        self.__lifetime = 12
        self.__y_offset = y_offset



    def update(self):
        super().update()

        self.__lifetime -= 1
        if self.__lifetime == 0:
            self.kill()
        
        self.position.y -= sin(self.__lifetime*pi/12)*2

    def _get_blit_pos(self, offset, lerp_amount=0):
        return super()._get_blit_pos(offset, lerp_amount) - (0, self.__y_offset)