import pygame as pg
import random

from src.custom_types import Timer
from .asteroids import Asteroid
from .projectiles import EnemyBullet

from .components import ObjectAnimation, ObjectHitbox, Obstacle















class Enemy(Obstacle, ObjectAnimation):
    _layer = 9

    def __init__(self, *, health=1, points=0, point_display_height=0, **kwargs):
        super().__init__(health=health, points=points, point_display_height=point_display_height, **kwargs)
        self._player_ship = None


    
    def _get_player(self):
        from .spaceship import PlayerShip

        for obj in self.primary_group:
            if isinstance(obj, PlayerShip):
                return obj






class EnemyShip(Enemy):
    progress_save_key="enemy_ship"
    ignore_camera_rotation=True
    _layer=9

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

            points=200
        )

        self.__speed = 0
        self.__move_direction = pg.Vector2()
        self.__shoot_interval = Timer(22)
        self.__start_attack_delay = Timer(35).start()

        self.set_angular_vel(self.__rotation_speed)


    def __init_from_data__(self, object_data):
        self.__init__(object_data["position"])


    def update(self):
        super().update()

        if not self.has_health():
            if self.animations_complete:
                self.force_kill()
            return

        self.__shoot_interval.update()
        self.__start_attack_delay.update()
    
        for obj in self.primary_group:
            if (isinstance(obj, Asteroid)
                and obj.health
                and self.within_distance(obj, self.__asteroid_shoot_range)):
                if self.__shoot_interval.time_elapsed > 8:
                    self.__shoot(obj.position-self.position)
                
                self.__decrease_speed()
                break
        else:
            if self._player_ship is None:
                self._player_ship = self._get_player()


            elif self._player_ship.health:
                displacement = self._player_ship.position-self.position
                
                if self.within_distance(self._player_ship, 50):
                    self.__decrease_speed()
                else:
                    self.__increase_speed()
                

                if self.__start_attack_delay.complete and self.__shoot_interval.complete and self.within_distance(self._player_ship, self.__player_shoot_range):
                    self.__shoot(displacement.rotate(random.randint(-self.__shoot_deviation, self.__shoot_deviation)))
                
                self.__move_direction = displacement


        if self.__move_direction and self.__speed > 0:
            self.__move_direction.scale_to_length(self.__speed)
            self.set_velocity(self.__move_direction)
        elif self._velocity:
            self.clear_velocity()


    def on_collide(self, collided_with):
        if isinstance(collided_with, Asteroid) and collided_with.has_health():
            self.kill()



    def kill(self):
        self.set_health(0)
        self.clear_velocity()
        self.set_angular_vel(0)
        self._queue_sound("entity.asteroid.medium_explode")


    def __increase_speed(self) -> None:
        self.__speed = min(self.__speed+0.5, self.__move_speed)
    
    def __decrease_speed(self) -> None:
        self.__speed = max(self.__speed-0.5, 0)
        

    

    def __shoot(self, direction: pg.Vector2) -> None:
        self.primary_group.add(EnemyBullet(self.position, direction, self._velocity))
        self.__shoot_interval.restart()
        self._queue_sound("entity.ship.shoot", 0.8)

