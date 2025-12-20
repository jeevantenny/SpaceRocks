"Game objects represent objects that exist within the game world plus the Camera."

import pygame as pg
from typing import Iterator

from src.math_functions import format_angle
from src.states import State, StateStack

from src.audio import soundfx







class GameObject(soundfx.HasSoundQueue, pg.sprite.Sprite):
    """
    The base class all game objects inherit from.

    Game objects represent objects that exist within the game world
    """
    progress_save_key: str | None = None
    distance_based_sound=True
    ignore_camera_rotation=False

    __object_type_list: dict[str, type["GameObject"]] = {}

    def __init__(self, *, position: pg.typing.Point, group: "ObjectGroup | None" = None) -> None:
        if group:
            super().__init__(group)
        else:
            super().__init__()
        
        self.position = pg.Vector2(position)


    def __init_subclass__(cls):
        super().__init_subclass__()
        if cls.progress_save_key is not None:
            GameObject.__object_type_list[cls.progress_save_key] = cls

        

    def __init_from_data__(self, object_data: dict) -> None:
        "Alternate way to create game objects using data from save file."

        if not self.progress_save_key:
            raise NotImplementedError(f"{type(self).__name__} should not be reconstructed from data.")




    def post_init_from_data(self, object_dict: dict[str, "GameObject"]) -> None:
        "Called after init_from_save to resolve links between multiple game objects."
        pass




    @classmethod
    def init_from_data(cls, object_data: dict) -> "GameObject":
        "Called on GameObject class to create object from save data."

        obj_cls = GameObject.__object_type_list[object_data["save_key"]]
        obj: GameObject = obj_cls.__new__(obj_cls)
        obj.__init_from_data__(object_data)
        return obj

        


    @property
    def primary_group(self) -> "ObjectGroup | None":
        "The first group in the list of groups that the game object is part of (if any)."
        if groups:=self.groups():
            return groups[0] # type: ignore
        

    @property
    def host_state(self) -> State | None:
        if self.primary_group is not None:
            return self.primary_group.host_state
        else:
            return None



    def get_data(self) -> dict:
        """
        Returns information about game object as a dictionary that can be stored in save file. This data is
        passed into the init_from_data method to recreate the object when loading game from a save file.
        """

        if not self.progress_save_key:
            raise NotImplementedError(f"{type(self).__name__} should not be saved in save data.")
        
        return {"id": id(self),
                "save_key": type(self).progress_save_key,
                "position": tuple(self.position)}
        

    def add_to_groups(self, _object: "GameObject") -> None:
        _object.add(*self.groups())
        

    def kill(self):
        """
        Removes the game object from all groups. A object may not be removed immediately. Some objects may
        display a kill animation before being removed from the group.
        """
        super().kill()


    def force_kill(self):
        "Bypasses the main kill method and removed the game object from the group immediately."
        super().kill()




    def set_position(self, value: pg.typing.Point) -> None:
        self.position = pg.Vector2(value)
        



    def move(self, displacement: pg.Vector2) -> None:
        self.position += displacement


    
    def distance_to(self, other: "GameObject | pg.Vector2") -> float:
        return self.position.distance_to(self.__get_other_pos(other))
    

    def angle_to(self, other: "GameObject | pg.Vector2") -> float:
        "Gets the angle from the current game object;s position to other relative to (0, -1)."
        angle = pg.Vector2(0, -1).angle_to(self.__get_other_pos(other)-self.position)
        return format_angle(angle)


    
    def update(self) -> None:
        "Updates the position velocity and other properties of an entity in every tick."
        ...



    def process_collision(self) -> None:
        ...


    def draw(self, surface: pg.Surface, lerp_amount=0.0, offset: pg.typing.Point = (0, 0), rotation=0) -> None:
        "Draws to the sprite onto a surface. The sprite must have a texture. "
        ...


    
    def __get_other_pos(self, other: "GameObject | pg.typing.Point") -> pg.Vector2:
        if isinstance(other, GameObject):
            return other.position
        else:
            return pg.Vector2(other)













class ObjectGroup[T=GameObject](soundfx.HasSoundQueue, pg.sprite.AbstractGroup):
    "A way of grouping game objects for calling basic methods on all objects simultaneously."

    def __init__(self, full_volume_radius=180, host_state: State | None = None):
        super().__init__()

        self.__full_volume_radius = full_volume_radius
        self.__host_state = host_state
        self.__subgroups: set[ObjectSubgroup] = set()


    @property
    def host_state(self) -> State | None:
        return self.__host_state

    
    def get_host_state_stack(self) -> StateStack | None:
        if self.__host_state is None:
            return None
        else:
            return self.__host_state.state_stack


    def update(self, sound_focus: pg.typing.Point) -> None:
        for obj in self.sprites():
            if obj.primary_group is not None:
                obj.update() # type: ignore
                self.__process_entity_sound(obj, sound_focus, obj.clear_sound_queue())


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
        "Draws all objects in group to surface with some offset."

        for obj in self.get_draw_order():
            obj.draw(surface, lerp_amount, offset)


    def get_draw_order(self) -> list[T]:
        "Return the order in which sprites should be drawn."
        from .components import ObjectTexture
        return sorted(
            self.get_type(ObjectTexture),
            key=lambda x: x.draw_layer
        )





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
        "Force kills all objects in this group and any other group those objects belong to."
        for obj in self:
            obj.force_kill() # type: ignore


    def remove(self, *sprites):
        for subgroup in self.__subgroups:
            subgroup.remove(*sprites)
        super().remove(*sprites)


    def make_subgroup(self) -> "ObjectSubgroup":
        return ObjectSubgroup(self, self.__full_volume_radius, self.__host_state)

    def add_subgroup_internal(self, subgroup: "ObjectSubgroup") -> None:
        self.__subgroups.add(subgroup)


    def __iter__(self) -> Iterator[T]:
        return iter(self.sprites())
    



class ObjectSubgroup(ObjectGroup):
    """
    A sprite group that contains a subset of sprites from another group. Any sprites added to
    a subgroup will also be added to the supergroup. Any sprites removed
    """

    def __init__(self, super_group: ObjectGroup, full_volume_radius=180, host_state: State | None = None):
        super().__init__(full_volume_radius, host_state)
        super_group.add_subgroup_internal(self)
        self.__super_group = super_group

    def add(self, *sprites):
        self.__super_group.add(*sprites)
        super().add(*sprites)


    def remove(self, *sprites) -> None:
        "Removed sprite from group and parent group if it exists in this group."
        for sprite in sprites:
            if self.has_internal(sprite):
                self.__super_group.remove(sprite)
        
        super().remove(*sprites)