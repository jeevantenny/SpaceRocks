import pygame as p
import random
from math import sin, pi
from typing import Literal
from functools import partial

import config
import debug

from custom_types import Coordinate, TextureMap
from math_functions import vector_min, unit_vector

from userinput import InputInterpreter

from file_processing import assets, load_json

from ui import SmallFont

from .components import *


__all__ = [
    "Spaceship",
    "Bullet",
    "Asteroid",
    "DisplayPoint",
    "Crosshair"
]



class Spaceship(ObjectVelocity, ObjectAnimation, BorderCollision):
    rotation_speed = 15

    __texture_map_path = "spaceship.texture_map.json"
    __texture_map: TextureMap | None = None

    def __init__(self, position):
        if self.__texture_map is None:
            type(self).__texture_map = assets.load_texture_map(self.__texture_map_path)
        
        super().__init__(
            position=position,
            hitbox_size=(16, 16),
            bounding_area=(0, 0, *p.Vector2(config.WINDOW_SIZE)/config.PIXEL_SCALE),
            border_bounce=0.1,

            texture_map=self.__texture_map,
            anim_data=load_json("assets/animations/spaceship.animation.json")["animations"],
            controller_data=load_json("assets/anim_controllers/spaceship.anim_controller.json")
        )

        self.score = 0
        self.combo = 0

        # self.crosshair = Crosshair(self.position)
        self.thrust = False


    

    
    def get_rect(self) -> p.FRect:
        rect = p.FRect(0, 0, *self.size)
        rect.center = self.position
        return rect
    


    def userinput(self, inputs: InputInterpreter):

        if not inputs.keyboard_mouse.hold_keys[p.K_LCTRL]:
            
            self.thrust = inputs.check_input("ship_forward")

            if  inputs.check_input("left"):
                self.angular_vel = -self.rotation_speed

            if inputs.check_input("right"):
                self.angular_vel = self.rotation_speed
            
            if not ( inputs.check_input("right") or  inputs.check_input("left")):
                self.set_angular_vel(0)
            
            if inputs.check_input("ship_backward") and self._velocity.magnitude() > 3:
                self.accelerate(unit_vector(self._velocity)*-2)


            if  inputs.check_input("shoot") and self.alive():
                self.shoot()
                if inputs.current_input_type == "controller":
                    inputs.controller.rumble(0.2, 0.1, 1)



    def shoot(self) -> None:
        direction = self.get_rotation_vector()
        self.group.add(Bullet(self.position, direction, self))
        if not self.thrust:
            self.accelerate(-direction)


    def update(self):
        if self.thrust:
            self.accelerate(p.Vector2(0, -1).rotate(self.rotation))
        
        # if self.crosshair not in self.group:
        #     self.group.add(self.crosshair)
        
        super().update()

        # crosshair_line = (self.position, self.position+self.get_rotation_vector()*sum(config.PIXEL_WINDOW_SIZE))

        # asteroid_in_line_of_site = False
        # crosshair_asteroids: list[Asteroid] = []
        for obj in self.colliding_objects():
            if isinstance(obj, Asteroid):
                if obj.health:
                    if obj.size == 1 and self._velocity.magnitude() > self.max_speed-3:
                        self.score += obj.points
                        self.group.add(DisplayPoint(obj.get_display_point_pos(), obj.points))
                        obj.kill()
                    else:
                        self.kill()
                        obj.damage(1)
                        break

                # if self.asteroid_in_crosshair(obj, crosshair_line):
                #     asteroid_in_line_of_site = True
                #     crosshair_asteroids.append(obj)

        # self.crosshair.visible = asteroid_in_line_of_site
        # if asteroid_in_line_of_site:
        #     self.crosshair.set_position(min(crosshair_asteroids, key=lambda x: (self.position-x.position).magnitude()).position)



    def asteroid_in_crosshair(self, asteroid: "Asteroid", crosshair_line) -> bool:
        check_rect = asteroid.rect
        check_rect.center = asteroid.position + (asteroid.get_velocity()-self._velocity)*int((asteroid.position-self.position).magnitude()/Bullet.speed)
        
        return check_rect.clipline(*crosshair_line) or asteroid.rect.clipline(*crosshair_line)
        


    def draw(self, surface, lerp_amount=0):
        super().draw(surface, lerp_amount)
        
        if debug.debug_mode:
            p.draw.line(surface, "green", self.position, self.position+self.get_lerp_rotation_vector(lerp_amount)*sum(config.PIXEL_WINDOW_SIZE))






class Bullet(ObjectVelocity, ObjectTexture, ObjectHitbox):
    speed = 40
    hitbox_size = (8, 8)
    visible_area = p.Rect(0, 0, *p.Vector2(config.WINDOW_SIZE)/config.PIXEL_SCALE)

    def __init__(self, position: Coordinate, direction: Coordinate, shooter: Spaceship):
        super().__init__(
            position=position,
            texture=assets.load_texture_map("particles.texture_map.json")["bullet"],
            hitbox_size = (20, 20)
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
        for obj in self.colliding_objects():
            if isinstance(obj, Asteroid):
                self.damage_asteroid(obj)
                hit = True

        if hit:
            self.kill()


    def damage_asteroid(self, asteroid: "Asteroid") -> None:
        asteroid.damage(1)
        asteroid.accelerate(self.get_velocity()*0.1)
        if not asteroid.health:
            self.shooter.score += asteroid.points + self.shooter.combo
            self.group.add(DisplayPoint(asteroid.get_display_point_pos(), asteroid.points, self.shooter.combo))
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
        












class Asteroid(ObjectVelocity, ObjectAnimation, ObjectCollision, BorderCollision):
    size_data = {
        1: {
            "texture": "small",
            "hitbox": (13, 13),
            "health": 1,
            "points": 3
        },
        2: {
            "texture": "medium",
            "hitbox": (28, 28),
            "health": 2,
            "points": 5
        },
        3: {
            "texture": "large",
            "hitbox": (60, 60),
            "health": 4,
            "points": 8
        }
    }

    __texture_map_path = "asteroid.texture_map.json"
    __texture_map: TextureMap | None = None

    def __init__(self, position: Coordinate, velocity: Coordinate, window_border: p.typing.RectLike, size: Literal[1, 2, 3] = 1):
        if self.__texture_map is None:
            type(self).__texture_map = assets.load_texture_map(self.__texture_map_path)

        texture_map = {
            name.removeprefix(f"{self.size_data[size]["texture"]}_"): texture
            for name, texture in self.__texture_map.items()
        }

        super().__init__(
            position=position,
            hitbox_size=self.size_data[size]["hitbox"],
            bounce=0.95,
            bounding_area=window_border,
            border_bounce=0.95,

            texture_map=texture_map,
            anim_data=load_json("assets/animations/asteroid.animation.json")["animations"],
            controller_data=load_json("assets/anim_controllers/asteroid.anim_controller.json")
        )

        self.size = size

        self.health = self.size_data[size]["health"]
        self.set_angular_vel(random.randint(-8, 8))
        self.accelerate(velocity)
        self.explode_pos: p.Vector2 | None = None

        self.points = self.size_data[size]["points"]

    
    def update(self):
        if self.health:  
            super().update()
        else:
            self.update_animations()
            self.set_velocity((0, 0))
            self.set_angular_vel(0)
            self.set_position(self.explode_pos)
            if self.animations_complete:
                self.force_kill()


    def get_display_point_pos(self) -> tuple[float, float]:
        return (self.rect.centerx, self.rect.top)


    def damage(self, amount: int) -> None:
        self.health -= min(self.health, amount)
        if not self.health:
            self.kill()



    def do_collision(self):
        return bool(self.health)



    def kill(self):
        self.health = 0
        self.explode_pos = self.position.copy()
        if self.size > 1:
            positions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
            positions = map(p.Vector2, positions)
            rotate_angle = random.randint(1, 90)

            for pos in positions:
                pos.rotate_ip(rotate_angle)
                new_rock = Asteroid(self.position + pos*8, self.get_velocity() + pos*3, self.get_bounding_area(), self.size-1)
                new_rock.set_velocity(self.get_velocity()+pos)
                self.group.add(new_rock)





class Crosshair(ObjectTexture):
    draw_in_front = True
    __texture_map_path = "crosshair.texture_map.json"
    def __init__(self, position: Coordinate):
        super().__init__(
            position=position,
            texture=assets.load_texture_map(self.__texture_map_path)["crosshair_a"]
        )

        self.visible = False


    
    def draw(self, surface, lerp_amount=0):
        if self.visible:
            super().draw(surface, lerp_amount)







class DisplayPoint(ObjectTexture):
    draw_in_front = True

    def __init__(self, position: Coordinate, points: int, combo=0):
        text = f"+{points+combo}"
        if combo:
            text += " COMBO"

        super().__init__(
            position=position,
            texture=SmallFont().render(text, color_a=(221, 102, 68) if combo else (238, 238, 238), color_b="black")
        )

        self.duration = 12



    def update(self):
        super().update()
        if self.duration <= 0:
            self.kill()
        
        self.duration -= 1
        self.position.y -= sin(self.duration*pi/12)*2