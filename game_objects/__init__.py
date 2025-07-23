import pygame as p
from typing import Iterable, Callable, TypeGuard
from functools import partial

from game_errors import MissingComponentError




def run_functions(functions: Iterable[Callable], *args, **kwargs) -> None:
    "Runs all functions in list with same arguments."

    for func in functions:
        func(*args, **kwargs)



class GameObject(p.sprite.Sprite):

    def __init__(self, *, position: p.typing.Point, group: "ObjectGroup | None" = None) -> None:
        if group:
            super().__init__(group)
        else:
            super().__init__()
        
        self.position = p.Vector2(position)

        


    @property
    def group(self) -> "ObjectGroup | None":
        if groups:=self.groups():
            return groups[0]
        


    def force_kill(self):
        super().kill()




    def set_position(self, value: p.typing.Point) -> None:
        self.position = p.Vector2(value)
        




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



    def update(self) -> None:
        for object in self.sprites():
            object.update()



    def draw(self, surface: p.Surface, lerp_amount: float) -> None:
        top_sprites = []
        from .entities import DisplayPoint
        for obj in self.sprites():
            if hasattr(obj, "draw"):
                if obj.draw_in_front:
                    top_sprites.append(obj)
                else:
                    obj.draw(surface, lerp_amount)
        
        for obj in top_sprites:
            obj.draw(surface, lerp_amount)




    def move_all(self, displacement: p.Vector2) -> None:
        for object in self.sprites():
            object.move(displacement)



    def accelerate_all(self, value: p.Vector2) -> None:
        from .components import ObjectVelocity
        for object in self.sprites():
            if object.has_component(ObjectVelocity):
                object.accelerate(value)


    def sprites(self) -> list[GameObject]:
        return super().sprites()



    def count(self) -> int:
        return len(self.sprites())