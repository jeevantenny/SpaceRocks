import pygame as pg
import math
import random
from typing import Literal

import debug

from src.math_functions import sign
from src.custom_types import Timer
from src.input_device import controller_rumble, InputInterpreter
from src.audio import soundfx
from src.ui import font



from . import GameObject
from .components import ObjectAnimation, ObjectHitbox, ObjectCollision
from .obstacles import Asteroid
from .projectiles import PlayerBullet
from .particles import ShipSmoke, DisplayText








class Spaceship(ObjectAnimation, ObjectHitbox, ObjectCollision):
    draw_layer = 10
    _rotation_speed = 30
    _thrust_power = 1
    __asset_key = "spaceship"

    def __init__(self, position):
        
        super().__init__(
            position=position,
            hitbox_size=(16, 16),
            radius=3,
            bounce=0.8,

            texture_map_path=self.__asset_key,
            anim_path=self.__asset_key,
            controller_path=self.__asset_key
        )

        self.health = True
        self.__thrust = False
        self.__thruster_audio_chan: pg.Channel | None = None
        self.__turn_direction: Literal[-1, 0, 1] = 0

        self._attack_types: list[type[GameObject]] = [Asteroid]



    
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
            if self.__thruster_audio_chan is None:
                self.__start_thrust_sound()
            else:
                self.__thruster_audio_chan.set_volume(pg.math.clamp(abs(self._rotation-180)*0.002+0.3, 0, 1))

        elif self.__thruster_audio_chan is not None:
            self.__stop_thruster_sound()

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
        bullet = PlayerBullet(self.position, direction, self.get_velocity())
        self.primary_group.add(bullet)
        if not self.__thrust:
            self.accelerate(-direction*0.5)
        self._queue_sound("entity.ship.shoot", 0.8)

        return bullet


    
    def boost_speed(self) -> bool:
        return self._velocity.magnitude() > self._max_speed-3



    def on_collide(self, collided_with):
        if isinstance(collided_with, Asteroid):
            self.kill()

    
    def kill(self):
        self.health = False
        self.__thrust = False
        self.clear_velocity()
        self.set_angular_vel(0)
        self._queue_sound("entity.asteroid.medium_explode")


    def force_kill(self):
        self.__stop_thruster_sound()
        self.health = False
        super().force_kill()


    def _thrust(self) -> None:
        self.__thrust = True


    def _turn(self, direction: Literal[-1, 1]) -> None:
        self.__turn_direction = sign(self.__turn_direction+direction)


    def __start_thrust_sound(self) -> None:
        self.__stop_thruster_sound()
        self.__thruster_audio_chan = soundfx.play_sound("entity.ship.boost", 0.7, -1)



    def __stop_thruster_sound(self) -> None:
        if self.__thruster_audio_chan is not None:
            self.__thruster_audio_chan.fadeout(100)
            self.__thruster_audio_chan = None

    

    def __release_smoke(self) -> None:
        for _ in range(5):
            direction = self.get_rotation_vector()
            velocity = direction.rotate(random.randint(-15, 15))*random.randint(-15, -3)+self._velocity
            position = self.position-direction*16+self._velocity
            self.primary_group.add(ShipSmoke(position, velocity))
        




class PlayerShip(Spaceship):
    distance_based_sound=False
    progress_save_key="player_spaceship"

    __max_combo=10
    __max_combo_points=500

    def __init__(self, position):
        super().__init__(position)
        self._attack_types: list[type[GameObject]] = [Asteroid]

        from .powerups import PowerUpGroup
        self.__powerups = PowerUpGroup()
        self.__invincibility_timer = Timer(1)

        self.__bullets_fired: set[PlayerBullet] = set()
        self.__score_limit: int | None = None

        self.score = 0
        self.combo = 1.0
        
        # self.__powerups.add("SuperLaser")
        # self.__powerups.add("Shield")

    
    @property
    def invincible(self) -> bool:
        return not self.__invincibility_timer.complete


    def __init_from_data__(self, object_data):
        super().__init_from_data__(object_data)
        self._attack_types: list[type[GameObject]] = [Asteroid]

        self.score = object_data["score"]
        self.combo = object_data["combo"]

        from .powerups import PowerUpGroup
        self.__powerups = PowerUpGroup()
        for powerup_name in object_data.get("powerups", []):
            self.__powerups.add(powerup_name)

        self._do_transition()
        self._skip_animation_to_end()


    def get_data(self):
        data = super().get_data()
        data.update({"score": self.score,
                     "combo": self.combo,
                     "powerups": [powerup.get_name() for powerup in self.__powerups]})
        return data
    

    def set_score_limit(self, limit: int) -> None:
        self.__score_limit = limit
        self.score = min(self.score, limit)



    def userinput(self, inputs: InputInterpreter):
        if self.health and not inputs.keyboard_mouse.hold_keys[pg.KMOD_CTRL]:            
            if inputs.check_input("ship_forward"):
                self._thrust()

            if inputs.check_input("ship_left"):
                self._turn(-1)

            if inputs.check_input("ship_right"):
                self._turn(1)
            
            if  inputs.check_input("shoot") and self.alive():
                self.shoot()

            self.__powerups.userinput(inputs)

    
    def update(self):
        super().update()
        self.__powerups.update(self)
        self._join_sound_queue(self.__powerups.clear_sound_queue())

        self.__invincibility_timer.update()

        for bullet in self.__bullets_fired.copy():
            if not bullet.alive():
                self.__bullets_fired.remove(bullet)
                self.__process_from_bullet(bullet)
                


    def draw(self, surface, lerp_amount=0, offset=(0, 0), rotation=0):
        super().draw(surface, lerp_amount, offset, rotation)
        self.__powerups.draw(self, surface, lerp_amount, offset)


    def _thrust(self):
        super()._thrust()
        controller_rumble("ship_thrusters", 0.25, True)


    def shoot(self):
        bullet = super().shoot()
        self.__bullets_fired.add(bullet)
        controller_rumble("gun_fire")


    
    def invincibility_frames(self, amount=30) -> None:
        self.__invincibility_timer = Timer(amount).start()


    def kill(self):
        if self.__invincibility_timer.complete and not (self.__powerups.kill_protection(self) or debug.Cheats.invincible):
            super().kill()
            controller_rumble("large_explosion_b", 0.9)


    def has_powerup(self, powerup_name: str) -> None:
        return self.__powerups.includes(powerup_name)
    

    def acquire_powerup(self, powerup_name: str) -> None:
        if not self.has_powerup(powerup_name):
            self.__powerups.add(powerup_name)


    def remove_powerup(self, powerup) -> None:
        self.__powerups.remove(powerup)
    

    def take_points(self, points: int) -> int:
        """
        Takes points and adds to the PlayerShips's score based on the current combo. Returns how
        many points were added to the score.
        """

        combo_points = math.ceil(points * self.combo)
        if combo_points > self.__max_combo_points:
            add_points = max(points, self.__max_combo_points)
        else:
            add_points = combo_points

        if self.__score_limit is not None:
            add_points = min(add_points, self.__score_limit-self.score)

        self.score += add_points
        if not debug.Cheats.no_point_combo:
            self.combo = min(self.combo*1.1, self.__max_combo)

        return add_points


    def __process_from_bullet(self, bullet: PlayerBullet) -> None:
        if self.score == self.__score_limit:
            return

        if not bullet.hit_list:
            self.combo = 1.0
            return
        
        for obj in bullet.hit_list:
            if not obj._health:
                prev_combo = self.combo
                points = self.take_points(obj.points)

                if prev_combo > 1:
                    text_surface = font.small_font.render(f"+{points} COMBO", cache=False)
                else:
                    text_surface = font.small_font.render(f"+{points}", 1, "#eeeeee", "#004466", False)

                self.primary_group.add(DisplayText(obj.position, text_surface, obj.point_display_height))