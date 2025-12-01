import pygame as pg
import random

from src.game_errors import InitializationError
from src.file_processing import load_json

from .components import ObjectAnimation, ObjectCollision


__all__ = [
    "Asteroid"
]
        






class Asteroid(ObjectAnimation, ObjectCollision):
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






