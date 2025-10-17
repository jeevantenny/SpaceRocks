import pygame as pg
from typing import Iterator, Self

from math_functions import clamp, format_angle

from audio import soundfx







class GameObject(soundfx.HasSoundQueue, pg.sprite.Sprite):
    save_entity_progress=True
    distance_based_sound=True

    def __init__(self, *, position: pg.typing.Point, group: "ObjectGroup | None" = None) -> None:
        if group:
            super().__init__(group)
        else:
            super().__init__()
        
        self.position = pg.Vector2(position)

        

    def __init_from_data__(self, object_data: dict, group: "ObjectGroup | None" = None) -> None:
        if not self.save_entity_progress:
            raise NotImplementedError(f"{type(self).__name__} should not be reconstructed from data.")

        if group:
            super().__init__(group)
        else:
            super().__init__()
        
        self.position = pg.Vector2(object_data["position"])


    def post_init_from_data(self, object_dict: dict[str, "GameObject"]) -> None:
        pass


    @classmethod
    def init_from_data(cls, object_data: dict, group: "ObjectGroup | None" = None) -> "GameObject":
        obj_cls = object_data["class"]
        obj: GameObject = obj_cls.__new__(obj_cls)
        obj.__init_from_data__(object_data)
        return obj



    def get_data(self) -> dict:
        if not self.save_entity_progress:
            raise NotImplementedError(f"{type(self).__name__} should not be saved in save data.")
        
        return {"id": id(self),
                "class": type(self),
                "position": tuple(self.position)}

        


    @property
    def primary_group(self) -> "ObjectGroup | None":
        if groups:=self.groups():
            return groups[0] # type: ignore
        

    def add_to_groups(self, _object: "GameObject") -> None:
        _object.add(*self.groups())
        


    def force_kill(self):
        super().kill()




    def set_position(self, value: pg.typing.Point) -> None:
        self.position = pg.Vector2(value)
        



    def move(self, displacement: pg.Vector2) -> None:
        self.position += displacement


    
    def distance_to(self, other: "GameObject | pg.Vector2") -> float:
        return self.position.distance_to(self.__get_other_pos(other))
    

    def angle_to(self, other: "GameObject | pg.Vector2") -> float:
        angle = pg.Vector2(0, -1).angle_to(self.__get_other_pos(other)-self.position)
        return format_angle(angle)


    
    def update(self) -> None:
        "Updates the position velocity and other properties of an entity in every tick."
        ...



    def process_collision(self) -> None:
        ...


    def draw(self, surface: pg.Surface, lerp_amount=0.0, offset: pg.typing.Point = (0, 0)) -> None:
        "Draws to the sprite onto a surface. The sprite must have a texture. "
        ...


    
    def __get_other_pos(self, other: "GameObject | pg.typing.Point") -> pg.Vector2:
        if isinstance(other, GameObject):
            return other.position
        else:
            return pg.Vector2(other)













class ObjectGroup[T=GameObject](soundfx.HasSoundQueue, pg.sprite.AbstractGroup):
    def __init__(self, full_volume_radius=180):
        super().__init__()

        self.__full_volume_radius = full_volume_radius
        self.__sound_curve_factor = 1/full_volume_radius



    def update(self, sound_focus: pg.typing.Point) -> None:
        for object in self.sprites():
            object.update() # type: ignore
            self.__process_entity_sound(object, sound_focus, object.clear_sound_queue())


    def __process_entity_sound(self, _object: T, sound_focus: pg.typing.Point, queue: soundfx.SoundQueue) -> None:
        if _object.distance_based_sound:
            volume = self.__get_sound_volume(_object.distance_to(sound_focus))
            if volume and queue:
                for sound_data in queue:
                    self._queue_sound(sound_data[0], sound_data[1]*volume)
        
        else:
            self._join_sound_queue(queue)


    def __get_sound_volume(self, distance: float) -> float:
        if distance <= self.__full_volume_radius:
            return 1.0
        else:
            return 1/(1+distance-self.__full_volume_radius)




    def draw(self, surface: pg.Surface, lerp_amount=0.0, offset: pg.typing.Point = (0, 0)) -> None: # type: ignore
        from .components import ObjectTexture, ObjectHitbox

        draw_order = sorted(
            self.get_type(ObjectTexture),
            key=lambda x: x.draw_layer
        )

        for obj in draw_order:
            obj.draw(surface, lerp_amount, offset)




    def move_all(self, displacement: pg.Vector2) -> None:
        for object in self.sprites():
            object.move(displacement) # type: ignore



    def accelerate_all(self, value: pg.Vector2) -> None:
        from .components import ObjectVelocity
        for object in self.sprites():
            if object.has_component(ObjectVelocity): # type: ignore
                object.accelerate(value) # type: ignore


    def sprites(self) -> list[T]:
        return super().sprites()



    def count(self) -> int:
        return len(self.sprites())
    

    def get_type[GET_TYPE](self, object_type: type[GET_TYPE]) -> list[GET_TYPE]:
        return list(filter(lambda x: isinstance(x, object_type), self.sprites()))
    

    def kill_type(self, object_type: type[GameObject]) -> None:
        if not issubclass(object_type, GameObject):
            raise ValueError(f"Class {object_type.__name__} is not a GameObject type.")
        
        for obj in self:
            if isinstance(obj, object_type):
                obj.force_kill()
    

    def kill_all(self) -> None:
        for obj in self:
            obj.force_kill() # type: ignore


    def __iter__(self) -> Iterator[T]:
        return iter(self.sprites())