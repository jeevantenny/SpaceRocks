import pygame as pg
from typing import Iterable, Iterator, Callable

from math_functions import clamp, format_angle

from audio import soundfx







class GameObject(soundfx.HasSoundQueue, pg.sprite.Sprite):

    def __init__(self, *, position: pg.typing.Point, group: "ObjectGroup | None" = None) -> None:
        if group:
            super().__init__(group)
        else:
            super().__init__()
        
        self.position = pg.Vector2(position)

        


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
    def __init__(self, full_volume_radius=200):
        super().__init__()

        self.__full_volume_radius = full_volume_radius
        self.__sound_curve_factor = 1/full_volume_radius



    def update(self, sound_focus: pg.typing.Point) -> None:
        for object in self.sprites():
            object.update() # type: ignore
            self.__process_entity_sound(object, sound_focus, object.clear_sound_queue())


    def __process_entity_sound(self, _object: T, sound_focus: pg.typing.Point, queue: soundfx.SoundQueue) -> None:
        volume = self.__get_sound_volume(_object.distance_to(sound_focus))
        # if _object.__class__.__name__ == "Spaceship":
        #     print(volume)

        if volume and queue:
            for sound_data in queue:
                self._queue_sound(sound_data[0], sound_data[1]*volume)


    def __get_sound_volume(self, distance: float) -> float:
        if distance == 0:
            return 1
        else:
            return clamp(1/(self.__sound_curve_factor*(distance-self.__full_volume_radius)+1)**2, 0.0, 1.0)




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