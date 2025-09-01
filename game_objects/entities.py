import pygame as pg
import random
from math import sin, pi
from typing import Literal

import config
import debug
from math_functions import clamp, unit_vector
from input_device import InputInterpreter, controller_rumble

from file_processing import assets
from audio import soundfx



from ui.font import SmallFont

from .components import *
from .particles import ShipSmoke


__all__ = [
    "Spaceship",
    "Bullet",
    "Asteroid",
    "DisplayPoint"
]



class Spaceship(ObjectAnimation, BorderCollision):
    draw_layer = 2
    __rotation_speed = 30
    __asset_key = "spaceship"
    _max_speed = 100

    def __init__(self, position):
        
        super().__init__(
            position=position,
            hitbox_size=(16, 16),
            bounding_area=(0, 0, *pg.Vector2(config.WINDOW_SIZE)/config.PIXEL_SCALE),
            border_bounce=0.5,

            texture_map=assets.load_texture_map(self.__asset_key),
            anim_data=assets.load_anim_data(self.__asset_key),
            controller_data=assets.load_anim_controller_data(self.__asset_key)
        )

        self.score = 0
        self.combo = 0
        self.operational = True

        self.__thrust = False
        self.__thruster_audio_chan: pg.Channel | None = None


    


    def userinput(self, inputs: InputInterpreter):
        if not self.operational:
            return

        if not inputs.keyboard_mouse.hold_keys[pg.K_LCTRL]:
            
            self.__thrust = inputs.check_input("ship_forward")

            if inputs.check_input("left") and -self._angular_vel < self.__rotation_speed:
                if self._angular_vel > 0:
                    self._angular_vel = 0
                
                self._angular_vel -= 5

            if inputs.check_input("right") and self._angular_vel < self.__rotation_speed:
                if self._angular_vel < 0:
                    self._angular_vel = 0
                
                self._angular_vel += 5
            

            # If both left and right are clicked or neither is
            if inputs.check_input("right") == inputs.check_input("left"):
                self._angular_vel = 0
            
            # if not self.__thrust and inputs.check_input("ship_backward"):
            #     if self._velocity.magnitude() > 0.5:
            #         self.accelerate(unit_vector(self._velocity)*-0.2)


            if  inputs.check_input("shoot") and self.alive():
                self.shoot()

                


    def update(self) -> None:
        if self.__thrust:
            self.accelerate(pg.Vector2(0, -1).rotate(self.rotation))
            self.__release_smoke()
            if self.__thruster_audio_chan is None:
                self.__thruster_audio_chan = soundfx.play_sound("entity.ship.boost", 0.6, -1)
            else:
                self.__thruster_audio_chan.set_volume(clamp(abs(self.rotation)*0.002+0.3, 0, 1))

        elif self.__thruster_audio_chan is not None:
            self.__thruster_audio_chan.fadeout(100)
            self.__thruster_audio_chan = None
        
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
            pg.draw.line(surface, "green", lerp_pos, lerp_pos+self.get_lerp_rotation_vector(lerp_amount)*500)
                





    def shoot(self) -> None:
        direction = self.get_rotation_vector()
        self.group.add(Bullet(self.position, direction, self))
        if not self.__thrust:
            self.accelerate(-direction*0.5)

        soundfx.play_sound("entity.ship.shoot")
        controller_rumble("gun_fire")


    
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
        soundfx.play_sound("entity.asteroid.medium_explode", 1.0)
    

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
                return True
        else:
            return False






class Bullet(ObjectTexture, ObjectVelocity):
    _max_speed = 40
    draw_layer = 1
    hitbox_size = (8, 8)
    visible_area = pg.Rect(0, 0, *pg.Vector2(config.WINDOW_SIZE)/config.PIXEL_SCALE).inflate(100, 100)

    __lifetime = 15

    def __init__(self, position: pg.typing.Point, direction: pg.typing.Point, shooter: Spaceship):
        super().__init__(
            position=position,
            texture=assets.load_texture_map("particles")["bullet"]
        )

        self.shooter = shooter

        direction = unit_vector(pg.Vector2(direction))
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
                pg.draw.line(surface, "blue", *line)





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
    

    def __get_collision_lines(self) -> list[tuple[pg.Vector2, pg.Vector2]]:
        sideways: pg.Vector2 = self.get_rotation_vector().rotate(90)*8

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

    __asset_key = "asteroid"

    def __init__(self, position: pg.typing.Point, velocity: pg.typing.Point, size: Literal[1, 2, 3] = 1):
        super().__init__(
            position=position,
            hitbox_size=self.size_data[size]["hitbox"],
            bounce=0.95,

            texture_map=assets.load_texture_map(self.__asset_key),
            anim_data=assets.load_anim_data(self.__asset_key),
            controller_data=assets.load_anim_controller_data(self.__asset_key)
        )

        self.size = size

        self.health = self.size_data[size]["health"]
        self.set_angular_vel(random.randint(-8, 8))
        self.accelerate(velocity)
        self.explode_pos: pg.Vector2 | None = None

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
            self.__spawn_small_asteroid()

        if self.size == 1:
            soundfx.play_sound("entity.asteroid.small_explode", 0.7)
        elif self.size == 2:
            soundfx.play_sound("entity.asteroid.medium_explode", 0.7)


    def __spawn_small_asteroid(self):
        positions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        positions = map(pg.Vector2, positions)
        rotate_angle = random.randint(1, 90)

        for pos in positions:
            pos.rotate_ip(rotate_angle)
            new_rock = Asteroid(self.position + pos*8, self._velocity + pos*3, self.size-1)
            new_rock.set_velocity(self._velocity+pos)
            for group in self.groups():
                group.add(new_rock)











class DisplayPoint(ObjectTexture, ObjectHitbox):
    draw_layer = 5
    __safe_area = pg.Rect(0, 3, config.PIXEL_WINDOW_WIDTH, config.PIXEL_WINDOW_HEIGHT-3)

    def __init__(self, position: pg.typing.Point, points: int, combo=0):
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