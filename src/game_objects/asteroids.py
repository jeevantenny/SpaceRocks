import pygame as pg
import random

from src.file_processing import load_json

from .components import ObjectAnimation, Obstacle


__all__ = [
    "Asteroid"
]






class Asteroid(Obstacle, ObjectAnimation):
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
        separation = self.__asteroid_data[self.subrock]["collision_radius"] + 1

        for pos in positions:
            pos.rotate_ip(self._rotation)
            new_rock = Asteroid(self.position + pos*separation, self._velocity + pos*3, self.subrock)
            new_rock.set_velocity(self._velocity+pos)
            self.add_to_groups(new_rock)




