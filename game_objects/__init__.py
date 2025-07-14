import pygame as p
from typing import Iterable, Callable, TypeGuard
from functools import partial

from custom_types import Coordinate
from game_errors import MissingComponentError




def run_functions(functions: Iterable[Callable], *args, **kwargs) -> None:
    "Runs all functions in list with same arguments."

    for func in functions:
        func(*args, **kwargs)



class GameObject(p.sprite.Sprite):

    def __init__(self, *, position: Coordinate, group: "ObjectGroup | None" = None) -> None:
        if group:
            super().__init__(group)
        else:
            super().__init__()
        
        self.position = p.Vector2(position)

        print(type(self).__name__, self.__dict__)
        


    @property
    def group(self) -> "ObjectGroup | None":
        if groups:=self.groups():
            return groups[0]
        


    def force_kill(self):
        super().kill()
        




    def move(self, displacement: p.Vector2) -> None:
        self.position += displacement


    
    def update(self) -> None:
        "Updates the position velocity and other properties of an entity in every tick."
        ...



    def process_collision(self) -> None:
        ...


    def draw(self, surface: p.Surface, lerp_amount=0.0) -> None:
        "Draws to the sprite onto a surface. The sprite must have a texture. "
        ...













class ObjectGroup(p.sprite.AbstractGroup):
    def __init__(self):
        super().__init__()




    def move_all(self, displacement: p.Vector2) -> None:
        for object in self.sprites():
            object.move(displacement)



    def accelerate_all(self, value: p.Vector2) -> None:
        # for object in self.sprites():
        #     if object.has_component(ObjectVelocity):
        #         object.accelerate(value)
        ...



    def update(self) -> None:
        for object in self.sprites():
            object.update()



    def draw(self, surface: p.Surface, lerp_amount: float) -> None:
        for obj in self.sprites():
            if hasattr(obj, "draw"):
                obj.draw(surface, lerp_amount)