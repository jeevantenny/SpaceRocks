import pygame as p
import random
from math import sin, pi
from typing import Literal
from functools import partial

import config

from custom_types import Coordinate
from math_functions import vector_min, unit_vector

from userinput import InputInterpreter

from file_processing import assets

from ui import SmallFont

from . import GameObject, ObjectGroup
from .components import ObjectVelocity, ObjectTexture, ObjectCollision, BorderCollision





class Spaceship(ObjectVelocity, ObjectTexture, BorderCollision):
    rotation_speed = 15
    def __init__(self, position):
        super().__init__(
            position=position,
            hitbox_size=(16, 16),
            texture=assets.load_texture("game_objects/spaceship.png"),
            bounding_area=(0, 0, *p.Vector2(config.WINDOW_SIZE)/config.PIXEL_SCALE),
            border_bounce=0.1
        )

        self.score = 0
        self.combo = 0


    

    
    def get_rect(self) -> p.FRect:
        rect = p.FRect(0, 0, *self.size)
        rect.center = self.position
        return rect
    


    def userinput(self, inputs: InputInterpreter):
        if not inputs.keyboard_mouse.hold_keys[p.K_LCTRL]:
            if inputs.check_input("ship_forward"):
                self.accelerate(p.Vector2(0, -1).rotate(self.rotation))

            if  inputs.check_input("left"):
                self.angular_vel = -self.rotation_speed

            if inputs.check_input("right"):
                self.angular_vel = self.rotation_speed
            
            if not ( inputs.check_input("right") or  inputs.check_input("left")):
                self.set_angular_vel(0)
            
            if inputs.keyboard_mouse.hold_keys[p.K_s] and self._velocity.magnitude() > 3:
                self.accelerate(unit_vector(self._velocity)*-2)


            if  inputs.check_input("shoot") and self.alive():
                self.shoot()



    def shoot(self) -> None:
        direction = self.get_rotation_vector()
        self.group.add(Bullet(self.position, direction, self))
        self.accelerate(-direction)


    def update(self):
        super().update()

        for obj in self.colliding_objects():
            if isinstance(obj, Asteroid):
                self.kill()






class Bullet(ObjectVelocity, ObjectTexture):
    speed = 40
    hitbox_size = (8, 8)
    visible_area = p.Rect(0, 0, *p.Vector2(config.WINDOW_SIZE)/config.PIXEL_SCALE)

    def __init__(self, position: Coordinate, direction: Coordinate, shooter: Spaceship):
        super().__init__(
            position=position,
            texture=assets.load_texture_map("particles.texture_map.json")["bullet"]
        )

        self.shooter = shooter

        direction = unit_vector(p.Vector2(direction))
        self.accelerate(direction*self.speed)
        self.move(direction*5)

        self.set_rotation(-direction.angle_to((0, -1)))


    def update(self):
        super().update()
        if not self.visible_area.collidepoint(self.position):
            self.kill()
            self.shooter.combo = 0
            return


        hit = False
        for obj in self.group.sprites():
            if isinstance(obj, Asteroid) and self.collision_check(obj):
                self.damage_asteroid(obj)
                hit = True

        if hit:
            self.kill()
            print(self.shooter.score)


    def damage_asteroid(self, asteroid: "Asteroid") -> None:
        asteroid.damage(1)
        asteroid.accelerate(self.get_velocity()*0.1)
        if not asteroid.health:
            self.shooter.score += asteroid.points + self.shooter.combo
            self.group.add(DisplayPoint(asteroid.position, asteroid.points, self.shooter.combo))
            self.shooter.combo += 1




    def collision_check(self, asteroid: "Asteroid") -> bool:
        sideways: p.Vector2 = self.get_rotation_vector().rotate(90)*8

        collision_lines = [
            (self.position+sideways, self.position-self.get_velocity()+sideways),
            (self.position-sideways, self.position-self.get_velocity()-sideways),
            (self.position, self.position-self.get_velocity())
        ]

        for line in collision_lines:
            if asteroid.rect.clipline(*line):
                return True
        
        return False
        












class Asteroid(ObjectVelocity, ObjectTexture, ObjectCollision, BorderCollision):
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
        super().__init__(
            position=position,
            texture=assets.load_texture(f"game_objects/{self.size_data[size]["texture"]}.png"),
            hitbox_size=self.size_data[size]["hitbox"],
            bounce=0.95,
            bounding_area=window_border,
            border_bounce=0.95
        )

        self.size = size

        self.health = self.size_data[size]["health"]
        self.set_angular_vel(random.randint(-8, 8))
        self.accelerate(velocity)

        self.points = self.size_data[size]["points"]

    
    def update(self):
        super().update()
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
                new_rock = Asteroid(self.position + pos*8, self.get_velocity() + pos*3, self.get_bounding_area(), self.size-1)
                new_rock.set_velocity(self.get_velocity()+pos)
                self.group.add(new_rock)
            

        super().kill()







class DisplayPoint(ObjectTexture):
    def __init__(self, position: Coordinate, points: int, combo=0):
        text = f"+{points+combo}"
        if combo:
            text += " COMBO"

        super().__init__(
            position=position,
            texture=SmallFont().render(text, color_a=(200, 50, 100) if combo else "white", color_b="black")
        )

        self.duration = 12



    def update(self):
        super().update()
        if self.duration <= 0:
            self.kill()
        
        self.duration -= 1
        self.position.y -= sin(self.duration*pi/12)*2