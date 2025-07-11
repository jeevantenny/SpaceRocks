import pygame as p
from typing import Literal

from custom_types import ActionKeys, HoldKeys, Coordinate
from math_functions import vector_min, unit_vector

from file_processing import assets

from . import GameObject
from .components import ObjectTexture, ObjectVelocity, ObjectCollision, BorderCollision





class Spaceship(GameObject):
    rotation_speed = 15
    max_speed = 15
    def __init__(self, position):
        super().__init__(position, [
            ObjectTexture(assets.load_texture("game_objects/spaceship.png")),
            ObjectVelocity(),
            ObjectCollision((16, 16)),
            BorderCollision((0, 0, 400, 300), 0.1)
        ])


    def userinput(self, action_keys: ActionKeys, hold_keys: HoldKeys):
        if hold_keys[p.K_w]:
            self.accelerate(p.Vector2(0, -1).rotate(self.get_rotation()))

        if hold_keys[p.K_a]:
            self.rotate(-self.rotation_speed)

        if hold_keys[p.K_d]:
            self.rotate(self.rotation_speed)
        
        if hold_keys[p.K_s] and self.get_velocity().magnitude() > 3:
            obj_vel = self.get_velocity()
            self.accelerate(unit_vector(obj_vel)*-2)


    def update(self):
        obj_vel = self.get_velocity()
        self.set_velocity(vector_min(obj_vel, unit_vector(obj_vel)*self.max_speed))





    def draw(self, surface: p.Surface, lerp_amount=0.0) -> None: ...

    def accelerate(self, amount: Coordinate) -> None: ...
    def rotate(self, amount: float) -> None: ...








class Asteroid(GameObject):
    def __init__(self, position, size: Literal[1, 2, 3] = 1):
        super().__init__(position, [
            ObjectTexture(assets.load_texture("game_objects/small_rock.png")),
            ObjectVelocity(),
            ObjectCollision((16, 16)),
            BorderCollision((0, 0, 400, 300), 0.9)
        ])

    
        