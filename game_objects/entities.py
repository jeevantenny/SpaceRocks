import pygame as pg
from typing import Literal, Optional
import random

import config
import debug
from custom_types import Timer
from math_functions import unit_vector, sign, vector_direction
from input_device import InputInterpreter, controller_rumble

from file_processing import assets
from audio import soundfx

from . import GameObject
from .components import *
from .particles import ShipSmoke, DisplayPoint


__all__ = [
    "Spaceship",
    "playerShip",
    "Bullet",
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
        self.combo = 0

        self.__init_base()

                

    def __init_from_data__(self, object_data, group=None):
        super().__init_from_data__(object_data, group)

        self.score = object_data["score"]
        self.combo = object_data["combo"]

        self.__init_base()
        self._set_anim_state("main")



    def __init_base(self):
        self.health = True
        self.__thrust = False
        self.__thruster_audio_chan: pg.Channel | None = None
        self.__turn_direction: Literal[-1, 0, 1] = 0

        self._attack_types: list[type[GameObject]] = [Asteroid]


    def get_data(self):
        return super().get_data() | {"score": self.score,
                                     "combo": self.combo}




    def update(self) -> None:
        if self.__thrust:
            self.accelerate(pg.Vector2(0, -1).rotate(self.rotation))
            self.__release_smoke()
            if self.__thruster_audio_chan is None:
                self.__start_thrust_sound()
            else:
                self.__thruster_audio_chan.set_volume(pg.math.clamp(abs(self.rotation)*0.002+0.3, 0, 1))

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

        for obj in self.colliding_objects():
            if isinstance(obj, Asteroid) and obj.health:
                self.kill()
                break


        self.__thrust = False
        self.__turn_direction = 0
        


    def draw(self, surface, lerp_amount=0, offset=(0, 0)):
        super().draw(surface, lerp_amount, offset)
        if debug.debug_mode:
            lerp_pos = self._get_lerp_pos(lerp_amount)+offset
            pg.draw.line(surface, "green", lerp_pos, lerp_pos+self.get_lerp_rotation_vector(lerp_amount)*500)
                





    def shoot(self) -> None:
        direction = self.get_rotation_vector()
        self.primary_group.add(Bullet(self.position, direction, self, self._attack_types))
        if not self.__thrust:
            self.accelerate(-direction*0.5)

        self._queue_sound("entity.ship.shoot")


    
    def boost_speed(self) -> bool:
        return self._velocity.magnitude() > self._max_speed-3

    

    def on_collide(self, collided_with):
        if collided_with == "vertical_border":
            vel = self._velocity.x
        elif collided_with == "horizontal_border":
            vel = self._velocity.y
        else:
            return

    
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


    def __ship_got_hit(self, asteroid: "Asteroid") -> bool:
        if asteroid.health:
            if asteroid.size == 1 and self.boost_speed():
                self.score += asteroid.points
                self.primary_group.add(DisplayPoint(asteroid.get_display_point_pos(), asteroid.points))
                asteroid.kill()
                return False
            else:
                self.kill()
                return True
        else:
            return False
        




class PlayerShip(Spaceship):
    def __init__(self, position, **kwargs):
        super().__init__(position, **kwargs)
        self._attack_types: list[type[GameObject]] = [Asteroid, EnemyShip]



    def userinput(self, inputs: InputInterpreter):
        if self.health and not inputs.keyboard_mouse.hold_keys[pg.K_LCTRL]:            
            if inputs.check_input("ship_forward"):
                self._thrust()

            if inputs.check_input("left"):
                self._turn(-1)

            if inputs.check_input("right"):
                self._turn(1)
            
            if  inputs.check_input("shoot") and self.alive():
                self.shoot()


    def _thrust(self):
        super()._thrust()
        controller_rumble("ship_thrusters", 0.25, True)


    def shoot(self):
        super().shoot()
        controller_rumble("gun_fire")


    def kill(self):
        if not debug.Cheats.invincible:
            super().kill()
            controller_rumble("large_explosion_b", 0.9)






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
        turn_by = direction-self.rotation
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
        
        if abs(direction-self.rotation) < 10:
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






class Bullet(ObjectTexture, ObjectVelocity):
    draw_layer = 1
    visible_area = pg.Rect(0, 0, *pg.Vector2(config.WINDOW_SIZE)/config.PIXEL_SCALE).inflate(100, 100)

    __speed = 40
    __lifetime = 40
    _max_speed = 100 + __speed

    def __init__(self, position: pg.typing.Point, direction: pg.typing.Point, shooter: Spaceship, attack_types: list[type[GameObject]]):
        super().__init__(
            position=position,
            texture=assets.load_texture_map("particles")["bullet"]
        )

        self.shooter = shooter

        direction = unit_vector(pg.Vector2(direction))
        self.accelerate(direction*self.__speed+shooter.get_velocity())
        self.move(direction*5)

        self.set_rotation(-direction.angle_to((0, -1)))
        self.__attack_types = attack_types
        self.__distance_traveled = 0.0


    
    def __init_from_data__(self, object_data, group=None):
        super().__init_from_data__(object_data, assets.load_texture_map("particles")["bullet"], group)

        self.__attack_types = object_data["attack_types"]
        self.__shooter_id = object_data["shooter_id"]
        self.__distance_traveled = 0.0

    
    def post_init_from_data(self, object_dict):
        # Finds the shooter entity and assigns it to the shooter attribute.
        if self.__shooter_id in object_dict:
            self.shooter = object_dict[self.__shooter_id]
        else:
            raise Exception("Bullet cannot find shooter object.")


    
    def get_data(self):
        return super().get_data() | {"shooter_id": id(self.shooter),
                                     "attack_types": self.__attack_types}



    def update(self):
        super().update()
        self.__distance_traveled += self.__speed
        self.__lifetime -= 1
        if self.__lifetime == 0:
            self.kill()
            self.shooter.combo = 0
            # Combo goes back to zero if player misses.
            return


        hit = False
        for obj in self.primary_group:
            # If the game object is a type the bullet can attack and the object is
            # alive then damage or kill it.
            if (type(obj) in self.__attack_types
                and getattr(obj, 'health', True)
                and self.__collision_check(obj)
                ):
                if isinstance(obj, Asteroid):
                    self.damage_asteroid(obj)
                else:
                    obj.kill()
                hit = True

        if hit:
            self.kill()
            
        
    


    def draw(self, surface, lerp_amount=0, offset=(0, 0)):
        super().draw(surface, lerp_amount, offset)

        if debug.debug_mode:
            for line in self.__get_collision_lines(offset):
                pg.draw.line(surface, "blue", *line)





    def damage_asteroid(self, asteroid: "Asteroid") -> None:
        "Damages asteroid and increments the shooter's score and combo accordingly."
        asteroid.damage(1)
        asteroid.accelerate(self._velocity*0.1/asteroid.size)
        if not asteroid.health:
            # Score increments by asteroid's points + current combo amount
            self.shooter.score += asteroid.points + self.shooter.combo
            self.primary_group.add(DisplayPoint(asteroid.get_display_point_pos(), asteroid.points, self.shooter.combo))
            self.shooter.combo += 1




    def __collision_check(self, _object: GameObject) -> bool:
        for line in self.__get_collision_lines():
            if _object.rect.clipline(*line):
                return True
        
        return False
    

    def __get_collision_lines(self, blit_offset=(0, 0)) -> list[tuple[pg.Vector2, pg.Vector2]]:
        sideways: pg.Vector2 = self.get_rotation_vector().rotate(90)*9

        line_offset = -self.get_rotation_vector()*min(self.__distance_traveled*0.5, self.__speed*2)
        prev_pos = self.position-self._velocity+blit_offset

        return [
            (prev_pos+sideways, prev_pos+line_offset+sideways),
            (prev_pos-sideways, prev_pos+line_offset-sideways),
            (prev_pos, prev_pos+line_offset)
        ]
        
        


















class Asteroid(ObjectAnimation, ObjectCollision):
    size_data = {
        1: {
            "texture": "small",
            "hitbox": (16, 16),
            "health": 1,
            "points": 3
        },
        2: {
            "texture": "medium",
            "hitbox": (30, 30),
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

    def __init__(self,
                 position: pg.typing.Point,
                 velocity: pg.typing.Point,
                 size: Literal[1, 2, 3] = 1,
                 palette_swap: str | None = None):

        super().__init__(
            position=position,
            hitbox_size=self.size_data[size]["hitbox"],
            bounce=0.95,

            texture_map_path=self.__asset_key,
            anim_path=self.__asset_key,
            controller_path=self.__asset_key,
            palette_swap=palette_swap
        )

        self.size = size

        self.health = self.size_data[size]["health"]
        self.set_angular_vel(random.randint(-8, 8))
        self.accelerate(velocity)
        self.explode_pos: pg.Vector2 | None = None

        self.points = self.size_data[size]["points"]


    
    def __init_from_data__(self, object_data, group=None):
        super().__init_from_data__(object_data, group)

        self.size = object_data["size"]
        self._set_hitbox_size(self.size_data[self.size]["hitbox"])
        self.health = object_data["health"]
        self.explode_pos: pg.Vector2 | None = None
        
        self.points = self.size_data[self.size]["points"]



    def get_data(self):
        return super().get_data() | {"size": self.size,
                                     "health": self.health}

    
    def update(self):
        if self.health:  
            super().update()
        else:
            self._update_animations()
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
            self._queue_sound("entity.asteroid.small_explode")



    def do_collision(self):
        return bool(self.health)



    def kill(self, spawn_asteroids=True):
        self.health = 0
        self.explode_pos = self.position.copy()
        if spawn_asteroids and self.size > 1:
            self.__spawn_small_asteroid()

        if self.size == 1:
            self._queue_sound("entity.asteroid.small_explode", 0.7)
        elif self.size == 2:
            self._queue_sound("entity.asteroid.medium_explode", 0.7)

        self.save_entity_progress = False


    def __spawn_small_asteroid(self):
        positions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        positions = map(pg.Vector2, positions)
        rotate_angle = random.randint(1, 90)

        for pos in positions:
            pos.rotate_ip(rotate_angle)
            new_rock = Asteroid(self.position + pos*8, self._velocity + pos*3, self.size-1, self._palette_swap)
            new_rock.set_velocity(self._velocity+pos)
            self.add_to_groups(new_rock)