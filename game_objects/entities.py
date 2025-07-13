import pygame as p
import random
from typing import Literal
from functools import partial

import config

from custom_types import ActionKeys, HoldKeys, Coordinate
from math_functions import vector_min, unit_vector

from file_processing import assets

from . import GameObject, ObjectGroup
from .components import ObjectTexture, ObjectVelocity, ObjectCollision, BorderCollision





class Spaceship(GameObject):
    rotation_speed = 15
    max_speed = 15
    def __init__(self, position):
        super().__init__(position)

        self.texture = ObjectTexture(assets.load_texture("game_objects/spaceship.png"))
        self.velocity = ObjectVelocity()
        self.border_collision = BorderCollision((0, 0, *p.Vector2(config.WINDOW_SIZE)/config.PIXEL_SCALE), 0.1)

        self.get_velocity = partial(self.velocity.get_velocity, self)
        self.set_velocity = partial(self.velocity.set_velocity, self)

        self.size = (16, 16)


        self.score = 0


    

    
    def get_rect(self) -> p.FRect:
        rect = p.FRect(0, 0, *self.size)
        rect.center = self.position
        return rect
    


    def userinput(self, action_keys: ActionKeys, hold_keys: HoldKeys):
        if not hold_keys[p.K_LCTRL]:
            if hold_keys[p.K_w]:
                self.velocity.accelerate(self, p.Vector2(0, -1).rotate(self.get_rotation()))

            if hold_keys[p.K_a]:
                self.texture.set_angular_vel(self, -self.rotation_speed)

            if hold_keys[p.K_d]:
                self.texture.set_angular_vel(self, self.rotation_speed)
            
            if not (hold_keys[p.K_a] or hold_keys[p.K_d]):
                self.texture.set_angular_vel(self, 0)
            
            if hold_keys[p.K_s] and self.get_velocity().magnitude() > 3:
                obj_vel = self.get_velocity()
                self.velocity.accelerate(self, unit_vector(obj_vel)*-2)


            if action_keys[p.K_SPACE]:
                self.shoot()



    def shoot(self) -> None:
        self.group.add(Bullet(self.position, self.get_rotation_vector(), self))
        self.velocity.accelerate(self, -self.get_rotation_vector())


    def update(self):
        obj_vel = self.velocity.get_velocity(self)
        self.velocity.set_velocity(self, vector_min(obj_vel, unit_vector(obj_vel)*self.max_speed))
        self.velocity.update(self)
        self.border_collision.process_collision(self)


    def draw(self, surface: p.Surface, lerp_amount=0.0) -> None:
        self.texture.draw(self, surface, lerp_amount)






class Bullet(GameObject):
    speed = 40
    hitbox_size = (8, 8)
    visible_area = p.Rect(0, 0, *p.Vector2(config.WINDOW_SIZE)/config.PIXEL_SCALE)
    def __init__(self, position: Coordinate, direction: Coordinate, shooter: Spaceship):
        super().__init__(position, [
            ObjectVelocity(),
            ObjectTexture(assets.load_texture_map("particles.texture_map.json")["bullet"])
        ], shooter.group)

        self.shooter = shooter

        direction = unit_vector(p.Vector2(direction))
        self.accelerate(direction*self.speed)
        self.move(direction*5)

        self.set_rotation(-direction.angle_to((0, -1)))


    def update(self):
        if not self.visible_area.collidepoint(self.position):
            self.kill()
            return


        hit = False
        for obj in self.group.sprites():
            if isinstance(obj, Asteroid) and self.collision_check(obj):
                obj.damage(1)
                obj.accelerate(self.get_velocity()*0.1)
                if not obj.health:
                    self.shooter.score += obj.points
                hit = True

        if hit:
            self.kill()
            print(self.shooter.score)



    def collision_check(self, asteroid: "Asteroid") -> bool:
        sideways: p.Vector2 = self.get_rotation_vector().rotate(90)*8

        collision_lines = [
            (self.position+sideways, self.position-self.get_velocity()+sideways),
            (self.position-sideways, self.position-self.get_velocity()-sideways),
            (self.position, self.position-self.get_velocity())
        ]

        for line in collision_lines:
            if asteroid.get_rect().clipline(*line):
                return True
        
        return False
        












class Asteroid(GameObject):
    size_data = {
        1: {
            "texture": "small_rock",
            "hitbox": (16, 16),
            "health": 1,
            "points": 3
        },
        2: {
            "texture": "medium_rock",
            "hitbox": (32, 32),
            "health": 2,
            "points": 5
        },
        3: {
            "texture": "large_rock",
            "hitbox": (64, 64),
            "health": 4,
            "points": 8
        }
    }
    def __init__(self, position: Coordinate, velocity: Coordinate, window_border: p.typing.RectLike, size: Literal[1, 2, 3] = 1):
        super().__init__(position, [
            ObjectTexture(assets.load_texture(f"game_objects/{self.size_data[size]["texture"]}.png")),
            ObjectVelocity(),
            ObjectCollision(self.size_data[size]["hitbox"], 0.9),
            BorderCollision(window_border, 0.9)
        ])

        self.size = size

        self.health = self.size_data[size]["health"]
        self.set_angular_vel(random.randint(-8, 8))
        self.accelerate(velocity)

        self.points = self.size_data[size]["points"]

    
    def update(self):
        if not self.health:
            self.kill()


    def damage(self, amount: int) -> None:
        self.health -= min(self.health, amount)




    def kill(self):
        if self.size > 1:
            positions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
            positions = map(p.Vector2, positions)
            rotate_angle = random.randint(1, 90)

            for pos in positions:
                pos.rotate_ip(rotate_angle)
                new_rock = Asteroid(self.position + pos*12, self.get_velocity() + pos*3, self.get_bounding_area(), self.size-1)
                new_rock.set_velocity(self.get_velocity()+pos)
                self.group.add(new_rock)
            
            # input()
        
        super().kill()
