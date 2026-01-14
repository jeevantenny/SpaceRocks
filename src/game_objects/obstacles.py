import pygame as pg
import random

import debug

from src.custom_types import Timer
from src.game_errors import InitializationError
from src.file_processing import load_json, assets

from . import GameObject
from .components import ObjectAnimation, ObjectTexture, ObjectVelocity, ObjectHitbox, ObjectCollision
from .projectiles import EnemyBullet


__all__ = [
    "Asteroid"
]




class Damageable(ObjectHitbox):
    "Objects that take damage from attacks and lose Health. Once health depletes they will be killed."
    def __init__(self, *, health=1, points=0, point_display_height=0, **kwargs):
        super().__init__(**kwargs)
        self._health = health
        self.__points = points
        self.__point_display_height = point_display_height
    
    @property
    def points(self) -> int:
        return self.__points

    @property
    def health(self) -> int:
        return self._health

    @property
    def point_display_height(self) -> int:
        return self.__point_display_height


    def damage(self, amount: int) -> None:
        if not self._health:
            return
        self._health -= min(self._health, amount)
        if not self._health:
            self.kill()


    def force_kill(self):
        self._health = 0
        super().force_kill()






class Asteroid(Damageable, ObjectAnimation, ObjectCollision):
    progress_save_key = "asteroid"

    __asteroid_data = load_json("data/asteroids")
    __asset_key = "asteroid"
    __hitbox_padding = 10 # Used to increase the size of damage_rect relative to default hitbox

    # Lower max speed for asteroids ensure that they are never to fast to dodge
    _max_speed = 10


    def __init__(self,
                 position: pg.typing.Point,
                 velocity: pg.typing.Point,
                 id: str):
        
        self.__setup_id(id)

        super().__init__(
            position=position,
            hitbox_size=(self.__hitbox_size[0]+self.__hitbox_padding, self.__hitbox_size[1]+self.__hitbox_padding),
            bounce=1.0,
            radius=self.__data["collision_radius"],

            health=self.__data["health"],
            points=self.__data["points"],
            point_display_height=self.size*6,

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
        self._health = object_data["health"]

        # To address an issue where asteroids will show wrong texture when loaded from
        # save file and when the pause menu is showing.
        self._do_transition()



    def __setup_id(self, id: str) -> None:
        self.__id = id
        self.__data: dict[str, str | int] = self.__asteroid_data[id]


    @property
    def size(self) -> int:
        return self.__data["size_value"]
    
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
            if self.animations_complete:
                self.force_kill()



    def damage(self, amount: int, knockback: pg.Vector2 | None = None) -> None:
        if knockback:
            self.accelerate(knockback*self.__knockback_amount)
        super().damage(amount)
        if self._health:
            self._queue_sound("entity.asteroid.small_explode")



    def do_collision(self):
        return bool(self._health)



    def kill(self, spawn_subrocks=True):
        self._health = 0
        if spawn_subrocks and self.subrock is not None:
            self.__spawn_subrock()

        if self.size == 1:
            self._queue_sound("entity.asteroid.small_explode", 0.7)
        elif self.size == 2:
            self._queue_sound("entity.asteroid.medium_explode", 0.7)

        self.set_velocity((0, 0))
        self.set_angular_vel(0)
        self.save_entity_progress = False


    def __spawn_subrock(self):
        positions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        positions = map(pg.Vector2, positions)

        for pos in positions:
            pos.rotate_ip(self._rotation)
            new_rock = Asteroid(self.position + pos*8, self._velocity + pos*3, self.subrock)
            new_rock.set_velocity(self._velocity+pos)
            self.add_to_groups(new_rock)






class EnemyShip(Damageable, ObjectAnimation, ObjectHitbox, ObjectCollision):
    progress_save_key=None
    ignore_camera_rotation=True
    draw_layer=9

    __move_speed = 4
    __rotation_speed = 8
    __player_shoot_range = 170
    __asteroid_shoot_range = 60
    __shoot_deviation = 30

    def __init__(self, position: pg.typing.Point):
        super().__init__(
            position=position,
            hitbox_size=(32, 32),
            radius=9,
            
            texture_map_path="enemies",
            anim_path="saucer",
            controller_path="enemy",

            points=50
        )

        self.__player_ship = None
        self.__speed = 0
        self.__shoot_interval = Timer(22)
        self.__start_attack_delay = Timer(35).start()

        self.set_angular_vel(self.__rotation_speed)

    def update(self):
        super().update()

        if not self._health:
            if self.animations_complete:
                self.force_kill()
            return

        self.__shoot_interval.update()
        self.__start_attack_delay.update()
    
        for obj in self.primary_group:
            if (isinstance(obj, Asteroid)
                and obj.health
                and self.__shoot_interval.time_elapsed > 6
                and self.distance_to(obj) < self.__asteroid_shoot_range):
                self.__shoot(obj.position-self.position)
        

        if self.__player_ship is None:
            from .spaceship import PlayerShip
            for obj in self.primary_group:
                if isinstance(obj, PlayerShip):
                    self.__player_ship = obj
                    break

        

        elif self.__player_ship.health:
            displacement = self.__player_ship.position-self.position
            distance = displacement.magnitude()
            
            if distance > 50:
                self.__speed = min(self.__speed+1, self.__move_speed)
            else:
                self.__speed = max(self.__speed-1, 0)
            
            if self.__speed:
                velocity = displacement.copy()
                velocity.scale_to_length(self.__speed)
                self.set_velocity(velocity)
            else:
                self.clear_velocity()
            

            if self.__start_attack_delay.complete and self.__shoot_interval.complete and distance < self.__player_shoot_range:
                self.__shoot(displacement.rotate(random.randint(-self.__shoot_deviation, self.__shoot_deviation)))
            
            # if self.colliderect(self.__player_ship.rect):
            #     self.__player_ship.kill()
            #     self.kill()


    def on_collide(self, collided_with):
        from .spaceship import PlayerShip
        if isinstance(collided_with, (Asteroid, PlayerShip)):
            self.kill()



    def kill(self):
        self._health = 0
        self.clear_velocity()
        self.set_angular_vel(0)
        self._queue_sound("entity.asteroid.medium_explode")
        


        

    

    def __shoot(self, direction: pg.Vector2) -> None:
        self.primary_group.add(EnemyBullet(self.position, direction, self._velocity))
        self.__shoot_interval.restart()
        self._queue_sound("entity.ship.shoot", 0.8)
