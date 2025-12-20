import pygame as pg
from typing import Literal, Optional
import math
import random

import config
import debug

from src.custom_types import Timer
from src.math_functions import unit_vector, sign, vector_direction
from src.input_device import InputInterpreter, controller_rumble
from src.game_errors import InitializationError

from src.file_processing import load_json
from src.audio import soundfx

from src.ui import font

from . import GameObject
from .components import *
from .projectiles import Bullet
from .particles import ShipSmoke, DisplayText


__all__ = [
    "Spaceship",
    "playerShip",
    "Asteroid"
]



class Spaceship(ObjectAnimation, ObjectVelocity, ObjectHitbox):
    draw_layer = 2
    distance_based_sound=False
    _rotation_speed = 30
    __asset_key = "spaceship"

    def __init__(self, position):
        
        super().__init__(
            position=position,
            hitbox_size=(10, 10),

            texture_map_path=self.__asset_key,
            anim_path=self.__asset_key,
            controller_path=self.__asset_key
        )

        self.score = 0
        self.combo = 1.0

        self.__init_base()

                

    def __init_from_data__(self, object_data):
        self.__init__(object_data["position"])

        self.score = object_data["score"]
        self.combo = object_data["combo"]

        self._set_anim_state("main")

        self.set_velocity(object_data["velocity"])
        self.set_rotation(object_data["rotation"])



    def __init_base(self):
        self.health = True
        self.__thrust = False
        self.__thruster_audio_chan: pg.Channel | None = None
        self.__turn_direction: Literal[-1, 0, 1] = 0

        self._attack_types: list[type[GameObject]] = [Asteroid]


    def get_data(self):
        data = super().get_data()
        
        data.update({"position": tuple(self.position),
                     "velocity": tuple(self._velocity),
                     "rotation": self._rotation,
                     "score": self.score,
                     "combo": self.combo})
        
        return data




    def update(self) -> None:
        if self.__thrust:
            self.accelerate(pg.Vector2(0, -1).rotate(self._rotation))
            self.__release_smoke()
            if self.__thruster_audio_chan is None:
                self.__start_thrust_sound()
            else:
                self.__thruster_audio_chan.set_volume(pg.math.clamp(abs(self._rotation)*0.002+0.3, 0, 1))

        elif self.__thruster_audio_chan is not None:
            self.__stop_thruster_sound()


        if self._angular_vel*self.__turn_direction <= 0:
            self._angular_vel = 0
        if self.__turn_direction and abs(self._angular_vel) < self._rotation_speed:
            self._angular_vel += 8*self.__turn_direction
        

        super().update()

            
        
        if not self.health:
            if self.animations_complete:
                self.force_kill()
            return

        for obj in self.overlapping_objects():
            if isinstance(obj, Asteroid) and obj.health:
                self.kill()
                break


        self.__thrust = False
        self.__turn_direction = 0
        


    # def draw(self, surface, lerp_amount=0, offset=(0, 0)):
    #     super().draw(surface, lerp_amount, offset)
    #     if debug.debug_mode:
    #         lerp_pos = self._get_lerp_pos(lerp_amount)+offset
    #         pg.draw.line(surface, "green", lerp_pos, lerp_pos+self.get_lerp_rotation_vector(lerp_amount)*500)
                





    def shoot(self) -> Bullet:
        from .projectiles import Bullet
        direction = self.get_rotation_vector()
        bullet = Bullet(self.position, direction, self.get_velocity())
        self.primary_group.add(bullet)
        if not self.__thrust:
            self.accelerate(-direction*0.5)
        self._queue_sound("entity.ship.shoot", 0.8)

        return bullet


    
    def boost_speed(self) -> bool:
        return self._velocity.magnitude() > self._max_speed-3



    
    def kill(self):
        self.health = False
        self.__thrust = False
        self.clear_velocity()
        self.set_angular_vel(0)
        self._queue_sound("entity.asteroid.medium_explode")


    def force_kill(self):
        self.__stop_thruster_sound()
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
            position = self.position-direction*8+self._velocity
            self.primary_group.add(ShipSmoke(position, velocity))
        




class PlayerShip(Spaceship):
    progress_save_key="player_spaceship"

    def __init__(self, position):
        super().__init__(position)
        self._attack_types: list[type[GameObject]] = [Asteroid, EnemyShip]

        from .powerups import PowerUpGroup
        self.__powerups = PowerUpGroup()
        self.__invincibility_timer = Timer(1)

        self.__bullets_fired: set[Bullet] = set()
        
        # self.__powerups.add("SuperLaser")
        # self.__powerups.add("Shield")

    
    @property
    def invincible(self) -> bool:
        return not self.__invincibility_timer.complete


    def __init_from_data__(self, object_data):
        super().__init_from_data__(object_data)
        self._attack_types: list[type[GameObject]] = [Asteroid, EnemyShip]

        from .powerups import PowerUpGroup
        self.__powerups = PowerUpGroup()
        for powerup_name in object_data.get("powerups", []):
            self.__powerups.add(powerup_name)


    def get_data(self):
        data = super().get_data()
        data["powerups"] = [powerup.get_name() for powerup in self.__powerups]
        return data



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
        self.__invincibility_timer.update()

        for bullet in self.__bullets_fired.copy():
            if not bullet.alive():
                self.__bullets_fired.remove(bullet)
                self.__process_from_bullet(bullet)
                


    def draw(self, surface, lerp_amount=0, offset=(0, 0)):
        super().draw(surface, lerp_amount, offset)
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


    def __process_from_bullet(self, bullet: Bullet) -> None:
        if not bullet.hit_list:
            self.combo = 1.0
            return
        
        for asteroid in bullet.hit_list:
            if asteroid.health:
                continue

            points = math.ceil(asteroid.points * self.combo)
            self.score += points
            if self.combo >= 25:
                text_surface = font.small_font.render(f"+{points} MAX COMBO", 1, "#dd99ff", "#550055", False)
            elif self.combo > 1:
                text_surface = font.small_font.render(f"+{points} COMBO", cache=False)
            else:
                text_surface = font.small_font.render(f"+{points}", 1, "#eeeeee", "#004466", False)

            self.primary_group.add(DisplayText(asteroid.get_display_point_pos(), text_surface))
            self.combo = min(self.combo*1.1, 25)
        






class EnemyShip(Spaceship):
    "UNUSED."
    __pursuit_speed = 20
    def __init__(self, position):
        super().__init__(position)
        self._attack_types: list[type[GameObject]] = [Asteroid, PlayerShip]

        self.__player: Optional[PlayerShip] = None
        self.__target_angle = None
        self.__current_objective: Literal["track_player", "slow_down"] = "track_player"

        self.__shoot_cooldown = Timer(4)



    def get_data(self):
        raise NotImplementedError


    def __process_behavior(self) -> None:
        if self.__player is None:
            if self.primary_group is not None:
                self.__player = self.primary_group.get_type(PlayerShip)[0]
            else:
                return
                
        if self.health:
            player_distance = self.distance_to(self.__player)
            match self.__current_objective:
                case "track_player":
                    self._move_to_position(self.__player.position)
                    
                    # if player_distance < 100:
                    #     self._shoot_when_ready()
                    if self.get_speed() > 40:
                        self.__current_objective = "slow_down"
                        print(self.__current_objective)
                
                case "slow_down":
                    self._slow_down()
                    # if self.speed < 8:
                    #     self.__current_objective = "track_player"
                    #     print(self.__current_objective)
                    
            




    def __turn_to_position(self, position: pg.Vector2) -> Literal[-1, 0, 1]:
        return self.__turn_to_direction(self.angle_to(position))
        
    
    def __turn_to_direction(self, direction: float) -> Literal[-1, 0, 1]:
        turn_by = direction-self._rotation
        if abs(turn_by) > 5:
            turn_value = sign(turn_by)
            if abs(turn_by) > 180:
                turn_value *= -1
            self._turn(turn_value)
            return turn_value
        else:
            return 0


    
    def _move_in_direction(self, direction: float) -> None:
        if self.get_speed() == 0:
            thrust_dir = direction
        else:
            
            thrust_dir = direction
        
        if abs(direction-self._rotation) < 10:
            speed_in_direction = self._velocity.dot(pg.Vector2(0, -1).rotate(direction))
            if speed_in_direction < self.__pursuit_speed:
                self._thrust()

        self.__turn_to_direction(thrust_dir)


    def _move_to_position(self, position: pg.Vector2) -> None:
        self._move_in_direction(self.angle_to(position))



    def _slow_down(self) -> None:
        self._move_in_direction(vector_direction(-self._velocity))



    
    def _shoot_when_ready(self) -> None:
        if self.__shoot_cooldown.complete:
            self.shoot()
            self.__shoot_cooldown.start()
            





    def update(self):
        self.__process_behavior()
        super().update()
        self.__shoot_cooldown.update()

        if self.distance_to(self.__player) > 2000:
            print("Removed enemy ship")
            self.force_kill()
        
        


















class Asteroid(ObjectAnimation, ObjectCollision):
    progress_save_key = "asteroid"

    __asteroid_data = load_json("data/asteroids")
    __asset_key = "asteroid"

    # Lower max speed for asteroids ensure that they are never to fast to dodge
    _max_speed = 10


    def __new__(cls, *args, **kwargs):
        if cls.__asteroid_data is None:
            raise InitializationError(f"No asteroid data has been defined. Could not create Asteroid object.")
        return super().__new__(cls)


    def __init__(self,
                 position: pg.typing.Point,
                 velocity: pg.typing.Point,
                 id: str):
        
        self.__setup_id(id)

        super().__init__(
            position=position,
            hitbox_size=self.__hitbox_size,
            bounce=0.95,

            texture_map_path=self.__data["texture_map"],
            anim_path=self.__asset_key,
            controller_path=self.__asset_key,
            palette_swap=self.__data.get("palette")
        )

        self.set_angular_vel(random.randint(-8, 8))
        self.accelerate(velocity)



    
    def __init_from_data__(self, object_data):
        self.__init__(
            object_data["position"],
            object_data["velocity"],
            object_data["asteroid_id"]
        )

        self.set_rotation(object_data["rotation"])
        self.set_angular_vel(object_data["angular_vel"])
        self.health = object_data["health"]

        # To address an issue where asteroids will show wrong texture when loaded from
        # save file and when the pause menu is showing.
        self._do_transition()



    def __setup_id(self, id: str) -> None:
        self.__id = id
        self.__data: dict[str, str | int] = self.__asteroid_data[id]
        self.health = self.__data["health"]



    @property
    def size(self) -> int:
        return self.__data["size_value"]
    
    @property
    def points(self) -> int:
        return self.__data["points"]
    
    @property
    def subrock(self) -> str | None:
        return self.__data.get("subrock")
    
    @property
    def __knockback_amount(self) -> float:
        return self.__data.get("knockback_amount", 1.0)
    
    @property
    def __hitbox_size(self) -> tuple[int, int]:
        return self.__data["hitbox_size"], self.__data["hitbox_size"]




    def get_data(self):
        data = super().get_data()
        data.update({"velocity": tuple(self._velocity),
                     "asteroid_id": self.__id,
                     "rotation": self._rotation,
                     "angular_vel": self._angular_vel,
                     "health": self.health})
        return data

    
    def update(self):
        if self.health:  
            super().update()
        else:
            self._update_animations()
            self.set_velocity((0, 0))
            self.set_angular_vel(0)
            if self.animations_complete:
                self.force_kill()


    def get_display_point_pos(self) -> tuple[float, float]:
        return (self.rect.centerx, self.rect.top)


    def damage(self, amount: int, knockback: pg.Vector2 | None = None) -> None:
        self.health -= min(self.health, amount)
        if not self.health:
            self.kill()
        else:
            self._queue_sound("entity.asteroid.small_explode")
            if knockback:
                self.accelerate(knockback*self.__knockback_amount)



    def do_collision(self):
        return bool(self.health)



    def kill(self, spawn_subrocks=True):
        self.health = 0
        if spawn_subrocks and self.subrock is not None:
            self.__spawn_subrock()

        if self.size == 1:
            self._queue_sound("entity.asteroid.small_explode", 0.7)
        elif self.size == 2:
            self._queue_sound("entity.asteroid.medium_explode", 0.7)

        self.save_entity_progress = False


    def __spawn_subrock(self):
        positions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        positions = map(pg.Vector2, positions)

        for pos in positions:
            pos.rotate_ip(self._rotation)
            new_rock = Asteroid(self.position + pos*8, self._velocity + pos*3, self.subrock)
            new_rock.set_velocity(self._velocity+pos)
            self.add_to_groups(new_rock)