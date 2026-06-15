import pygame as pg
import math
import random
from typing import Literal

import debug

from src.math_functions import sign
from src.custom_types import Timer
from src.input_device import controller_rumble, InputInterpreter
from src.ui import font



from .components import ObjectAnimation, ObjectHitbox, ObjectCollision, Obstacle
from .enemies import Enemy
from .projectiles import PlayerBullet
from .particles import ShipSmoke, DisplayText








class Spaceship(ObjectAnimation, ObjectHitbox, ObjectCollision):
    _layer = 10
    _rotation_speed = 30
    _thrust_power = 1
    __asset_key = "spaceship"

    def __init__(self, position):
        
        super().__init__(
            position=position,
            hitbox_size=(8, 8),
            radius=3,
            bounce=0.8,

            texture_map_path=self.__asset_key,
            anim_path=self.__asset_key,
            controller_path=self.__asset_key
        )

        self.health = True
        self.__thrust = False
        self.__turn_direction: Literal[-1, 0, 1] = 0



    
    @property
    def thrust(self) -> bool:
        return self.__thrust

                

    def __init_from_data__(self, object_data):
        self.__init__(object_data["position"])

        self._set_anim_state("main")

        self.set_velocity(object_data["velocity"])
        self.set_rotation(object_data["rotation"])



    def get_data(self):
        data = super().get_data()
        data.update({"position": tuple(self.position),
                     "velocity": tuple(self._velocity),
                     "rotation": self._rotation})
        return data




    def update(self) -> None:
        if self.__thrust:
            self.accelerate(pg.Vector2(0, -self._thrust_power).rotate(self._rotation))
            self.__release_smoke()
            self._queue_sound("entity.ship.boost", pg.math.clamp(abs(self._rotation-180)*0.002+0.4, 0, 0.8), True)

        if self.health:
            if self._angular_vel*self.__turn_direction <= 0:
                self._angular_vel = 0
            if self.__turn_direction and abs(self._angular_vel) < self._rotation_speed:
                self._angular_vel += 8*self.__turn_direction
        else:
            self._angular_vel = 0

        super().update()

            
        
        if not self.health:
            if self.animations_complete:
                self.force_kill()
            return


        self.__thrust = False
        self.__turn_direction = 0
                





    def shoot(self) -> PlayerBullet:
        from .projectiles import PlayerBullet
        direction = self.get_rotation_vector()
        bullet = PlayerBullet(self.position+direction*12, direction, self.get_velocity())
        self.primary_group.add(bullet)
        if not self.__thrust:
            self.accelerate(-direction*0.5)
        self._queue_sound("entity.ship.shoot", 0.8)

        return bullet


    
    def boost_speed(self) -> bool:
        return self._velocity.magnitude() > self._max_speed-3



    def on_collide(self, collided_with):
        if isinstance(collided_with, Obstacle) and collided_with.health:
            self.kill()
            if isinstance(collided_with, Enemy):
                collided_with.damage(1)

    
    def kill(self):
        if self.health:
            self.__thrust = False
            self.clear_velocity()
            self.set_angular_vel(0)
            self._queue_sound("entity.asteroid.medium_explode")

        self.health = False


    def force_kill(self):
        self.health = False
        super().force_kill()


    def _thrust(self) -> None:
        self.__thrust = True


    def _turn(self, direction: Literal[-1, 1]) -> None:
        self.__turn_direction = sign(self.__turn_direction+direction)

    

    def __release_smoke(self) -> None:
        for _ in range(5):
            direction = self.get_rotation_vector()
            velocity = direction.rotate(random.randint(-15, 15))*random.randint(-15, -3)+self._velocity
            position = self.position-direction*16+self._velocity
            self.primary_group.add(ShipSmoke(position, velocity))
        




class PlayerShip(Spaceship):
    distance_based_sound=False
    progress_save_key="player_spaceship"

    def __init__(self, position):
        super().__init__(position)
        from .powerups import PowerUpGroup
        self.__powerups = PowerUpGroup()
        self.__invincibility_timer = Timer(1)

    
    @property
    def invincible(self) -> bool:
        return not self.__invincibility_timer.complete


    def __init_from_data__(self, object_data):
        super().__init_from_data__(object_data)

        from .powerups import PowerUpGroup
        self.__powerups = PowerUpGroup()
        for powerup_name in object_data.get("powerups", []):
            self.__powerups.add(powerup_name)

        self._do_transition()
        self._skip_animation_to_end()


    def get_data(self):
        data = super().get_data()
        data.update({"powerups": [powerup.get_name() for powerup in self.__powerups]})
        return data



    def userinput(self, inputs: InputInterpreter):
        if self.health and not inputs.keyboard_mouse.hold_keys[pg.KMOD_CTRL]:            
            if inputs.check_input("ship_forward"):
                self._thrust()

            if inputs.check_input("ship_left"):
                self._turn(-1)

            if inputs.check_input("ship_right"):
                self._turn(1)
            
            if inputs.check_input("shoot") and self.alive():
                self.shoot()

            self.__powerups.userinput(inputs)

    
    def update(self):
        super().update()
        self.__powerups.update(self)
        self._join_sound_queue(self.__powerups.clear_sound_queue())

        self.__invincibility_timer.update()
                


    def draw(self, surface, lerp_amount=0, offset=(0, 0), rotation=0):
        super().draw(surface, lerp_amount, offset, rotation)
        self.__powerups.draw(self, surface, lerp_amount, offset)


    def _thrust(self):
        super()._thrust()
        controller_rumble("ship_thrusters", 0.25, True)


    def shoot(self) -> PlayerBullet:
        controller_rumble("gun_fire")
        return super().shoot()


    def do_collision(self):
        return super().do_collision() and not self.invincible


    
    def invincibility_frames(self, amount=30) -> None:
        self.__invincibility_timer = Timer(amount).start()


    def kill(self):
        if self.health and self.__invincibility_timer.complete and not self.__powerups.kill_protection(self):
            if debug.Cheats.invincible:
                self.invincibility_frames()
            else:
                super().kill()
                controller_rumble("large_explosion_b", 0.9)


    def has_powerup(self, powerup_name: str) -> None:
        return self.__powerups.includes(powerup_name)
    

    def acquire_powerup(self, powerup_name: str) -> None:
        if not self.has_powerup(powerup_name):
            self.__powerups.add(powerup_name)


    def remove_powerup(self, powerup) -> None:
        self.__powerups.remove(powerup)