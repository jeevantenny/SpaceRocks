import pygame as p
import random
from math import sin, pi
from typing import Literal
from functools import partial

import config
import debug
from custom_types import TextureMap
from math_functions import vector_min, unit_vector
from userinput import InputInterpreter
from input_feedback import controller_rumble
from misc import get_named_frames

from file_processing import assets, load_json
from audio import soundfx



from ui.font import SmallFont

from .components import *
from .particles import ShipSmoke


__all__ = [
    "Spaceship",
    "Bullet",
    "Asteroid",
    "DisplayPoint",
    "Crosshair"
]



class Spaceship(ObjectAnimation, BorderCollision):
    __rotation_speed = 30

    __texture_map_path = "spaceship.texture_map"
    __texture_map: TextureMap | None = None

    def __init__(self, position):
        if self.__texture_map is None:
            type(self).__texture_map = assets.load_texture_map(self.__texture_map_path)
        
        super().__init__(
            position=position,
            hitbox_size=(16, 16),
            bounding_area=(0, 0, *p.Vector2(config.WINDOW_SIZE)/config.PIXEL_SCALE),
            border_bounce=0.5,

            texture_map=self.__texture_map,
            anim_data=load_json(f"{self._anim_data_dir}/spaceship.animation"),
            controller_data=load_json(f"{self._controller_data_dir}/spaceship.anim_controller")
        )

        self.score = 0
        self.combo = 0
        self.__thrust = False
        self.operational = True


    


    def userinput(self, inputs: InputInterpreter):
        if not self.operational:
            return

        if not inputs.keyboard_mouse.hold_keys[p.K_LCTRL]:
            
            self.__thrust = inputs.check_input("ship_forward")

            if inputs.check_input("left") and -self._angular_vel < self.__rotation_speed:
                if self._angular_vel > 0:
                    self._angular_vel = 0
                
                self._angular_vel -= 5

            if inputs.check_input("right") and self._angular_vel < self.__rotation_speed:
                if self._angular_vel < 0:
                    self._angular_vel = 0
                
                self._angular_vel += 5
            

            
            if not (inputs.check_input("right") or inputs.check_input("left")):
                self._angular_vel = 0
            
            if not self.__thrust and inputs.check_input("ship_backward"):
                if self._velocity.magnitude() > 0.5:
                    self.accelerate(unit_vector(self._velocity)*-0.2)


            if  inputs.check_input("shoot") and self.alive():
                self.shoot()

                


    def update(self) -> None:
        if self.__thrust:
            self.accelerate(p.Vector2(0, -1).rotate(self.rotation))
            self.__release_smoke()
        
        super().update()
        
        if not self.operational:
            if self.animations_complete:
                self.force_kill()
            return

        for obj in self.colliding_objects():
            if isinstance(obj, Asteroid):
                if self.__ship_got_hit(obj):
                    break
        


    def draw(self, surface, lerp_amount=0):
        super().draw(surface, lerp_amount)

        
        if debug.debug_mode:
            lerp_pos = self._get_lerp_pos(lerp_amount)
            p.draw.line(surface, "green", lerp_pos, lerp_pos+self.get_lerp_rotation_vector(lerp_amount)*500)
                





    def shoot(self) -> None:
        direction = self.get_rotation_vector()
        self.group.add(Bullet(self.position, direction, self))
        if not self.__thrust:
            self.accelerate(-direction*0.5)

        soundfx.play_sound("entity.ship.shoot")
        controller_rumble("small_pulse")


    
    def boost(self) -> bool:
        return self._velocity.magnitude() > self._max_speed-3

    

    def on_collide(self, collided_with):
        if collided_with == "vertical_border":
            vel = self._velocity.x
        elif collided_with == "horizontal_border":
            vel = self._velocity.y
        else:
            return
        
        intensity = intensity = min(abs(vel)*0.15, 1)
        
        soundfx.play_sound("entity.ship.bounce", intensity)
        if intensity > 0.1:
            controller_rumble("small_pulse", intensity*0.5)


    
    def kill(self):
        self.operational = False
        self.__thrust = False
        self.clear_velocity()
        self.set_angular_vel(0)
    

    def __release_smoke(self) -> None:
        for _ in range(5):
            direction = self.get_rotation_vector()
            velocity = direction.rotate(random.randint(-15, 15))*random.randint(-15, -3)
            self.group.add(ShipSmoke(self.position-direction*16, velocity))


    def __ship_got_hit(self, asteroid: "Asteroid") -> bool:
        if asteroid.health:
            if asteroid.size == 1 and self.boost():
                self.score += asteroid.points
                self.group.add(DisplayPoint(asteroid.get_display_point_pos(), asteroid.points))
                asteroid.kill()
                return False
            else:
                self.kill()
                asteroid.damage(1)
                return True
        else:
            return False






class Bullet(ObjectTexture, ObjectVelocity):
    _max_speed = 40
    hitbox_size = (8, 8)
    visible_area = p.Rect(0, 0, *p.Vector2(config.WINDOW_SIZE)/config.PIXEL_SCALE).inflate(100, 100)

    __lifetime = 15

    def __init__(self, position: p.typing.Point, direction: p.typing.Point, shooter: Spaceship):
        super().__init__(
            position=position,
            texture=assets.load_texture_map("particles.texture_map")["bullet"]
        )

        self.shooter = shooter

        direction = unit_vector(p.Vector2(direction))
        self.accelerate(direction*self._max_speed)
        self.move(direction*5)

        self.set_rotation(-direction.angle_to((0, -1)))

        self.__start_pos = self.position.copy()


    def update(self):
        super().update()
        self.__lifetime -= 1
        if self.__lifetime == 0:
            self.kill()
            self.shooter.combo = 0
            return


        hit = False
        for obj in self.group.sprites():
            if (isinstance(obj, Asteroid)
                and obj.health
                and self.__collision_check(obj)
                ):
                self.damage_asteroid(obj)
                hit = True

        if hit:
            self.kill()
            
        
    


    def draw(self, surface, lerp_amount=0):
        super().draw(surface, lerp_amount)

        if debug.debug_mode:
            for line in self.__get_collision_lines():
                p.draw.line(surface, "blue", *line)





    def damage_asteroid(self, asteroid: "Asteroid") -> None:
        asteroid.damage(1)
        asteroid.accelerate(self._velocity*0.1/asteroid.size)
        if not asteroid.health:
            self.shooter.score += asteroid.points + self.shooter.combo
            self.group.add(DisplayPoint(asteroid.get_display_point_pos(), asteroid.points, self.shooter.combo))
            self.shooter.combo += 1




    def __collision_check(self, asteroid: "Asteroid") -> bool:
        for line in self.__get_collision_lines():
            if asteroid.rect.clipline(*line):
                return True
        
        return False
    

    def __get_collision_lines(self) -> list[tuple[p.Vector2, p.Vector2]]:
        sideways: p.Vector2 = self.get_rotation_vector().rotate(90)*8

        line_offset = -self._velocity*2*(self.__lifetime <= type(self).__lifetime-3)
        prev_pos = self.position-self._velocity

        return [
            (prev_pos+sideways, prev_pos+line_offset+sideways),
            (prev_pos-sideways, prev_pos+line_offset-sideways),
            (prev_pos, prev_pos+line_offset)
        ]
        
        


















class Asteroid(ObjectAnimation, ObjectCollision):
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
            "health": 10,
            "points": 8
        }
    }

    __texture_map_path = "asteroid.texture_map"
    __texture_map: TextureMap | None = None

    def __init__(self, position: p.typing.Point, velocity: p.typing.Point, size: Literal[1, 2, 3] = 1):
        super().__init__(
            position=position,
            hitbox_size=self.size_data[size]["hitbox"],
            bounce=0.95,

            texture_map=assets.load_texture_map(self.__texture_map_path),
            anim_data=load_json(f"{self._anim_data_dir}/asteroid.animation"),
            controller_data=load_json(f"{self._controller_data_dir}/asteroid.anim_controller")
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
        else:
            soundfx.play_sound("entity.asteroid.small_explode")



    def do_collision(self):
        return bool(self.health)



    def kill(self, spawn_asteroids=True):
        self.health = 0
        self.explode_pos = self.position.copy()
        if spawn_asteroids and self.size > 1:
            positions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
            positions = map(p.Vector2, positions)
            rotate_angle = random.randint(1, 90)

            for pos in positions:
                pos.rotate_ip(rotate_angle)
                new_rock = Asteroid(self.position + pos*8, self._velocity + pos*3, self.size-1)
                new_rock.set_velocity(self._velocity+pos)
                self.group.add(new_rock)

        if self.size == 1:
            soundfx.play_sound("entity.asteroid.small_explode", 0.7)
        elif self.size == 2:
            soundfx.play_sound("entity.asteroid.medium_explode", 0.7)





class Crosshair(ObjectTexture):
    draw_in_front = True
    __texture_map_path = "crosshair.texture_map"
    def __init__(self, position: p.typing.Point):
        super().__init__(
            position=position,
            texture=assets.load_texture_map(self.__texture_map_path)["crosshair_a"]
        )

        self.visible = False


    
    def draw(self, surface, lerp_amount=0):
        if self.visible:
            super().draw(surface, lerp_amount)







class DisplayPoint(ObjectTexture, ObjectHitbox):
    draw_in_front = True
    __safe_area = p.Rect(0, 3, config.PIXEL_WINDOW_SIZE[0], config.PIXEL_WINDOW_SIZE[1]-3)

    def __init__(self, position: p.typing.Point, points: int, combo=0):
        text = f"+{points+combo}"
        if combo:
            text = f"COMBO {text}"

        texture = SmallFont.render(text, color_a="#dd6644" if combo else "#eeeeee")

        super().__init__(
            position=position,
            texture=texture,
            hitbox_size=texture.size
        )
        

        self.__stay_in_view()

        self.__lifetime = 12



    def update(self):
        super().update()

        self.__lifetime -= 1
        if self.__lifetime == 0:
            self.kill()
        
        self.position.y -= sin(self.__lifetime*pi/12)*2
    



    def __stay_in_view(self) -> None:
        self.set_position(self.rect.inflate(1, 1).clamp(self.__safe_area).center)