import pygame as p
from typing import Iterable, Callable
from functools import partial

from custom_types import Coordinate
from game_errors import MissingComponentError

from .components import ObjectComponent, ObjectVelocity, ObjectTexture




def run_functions(functions: Iterable[Callable], *args, **kwargs) -> None:
    "Runs all functions in list with same arguments."

    for func in functions:
        func(*args, **kwargs)



class GameObject(p.sprite.Sprite):

    def __init__(self, position: Coordinate, components: Iterable[ObjectComponent] = [], groups: Iterable["ObjectGroup"] = []) -> None:
        super().__init__(*groups)
        
        self.position = p.Vector2(position)

        self.components: set[type[ObjectComponent]] = set()
        print(type(self).__name__, self.__dict__)
        for comp in sorted(components, key=lambda x: x.priority):
            self.add_component_methods(comp)
            self.components.add(type(comp))
        
        for comp in self.components:
            dependencies = set(comp.dependencies)

            if (missing:=dependencies.difference(self.components)):
                raise MissingComponentError(missing, comp)


    @property
    def test_property(self) -> None: pass


    def add_component_methods(self, component: ObjectComponent) -> None:
        for method in component.add_methods:
            name = method.__name__
            new_method = partial(method, self)
            if name in self.__dict__ or name in self.__class__.__dict__:
                current_method = self.__getattribute__(name)
                joined_method = partial(run_functions, [current_method, new_method])
                self.__setattr__(name, joined_method)
            else:
                self.__setattr__(name, new_method)
                



    def has_component(self, component: type[ObjectComponent]) -> bool:
        return component in self.components



    def move(self, displacement: p.Vector2) -> None:
        self.position += displacement


    
    def update(self) -> None:
        "Updates the position velocity and other properties of an entity in every tick."
        ...












class ObjectGroup(p.sprite.AbstractGroup):
    def __init__(self):
        super().__init__()




    def move_all(self, displacement: p.Vector2) -> None:
        for object in self.sprites():
            object.move(displacement)



    def accelerate_all(self, value: p.Vector2) -> None:
        for object in self.sprites():
            if object.has_component(ObjectVelocity):
                object.accelerate(value)



    def update_all(self) -> None:
        for object in self.sprites():
            object.update()



    def draw_all(self, surface: p.Surface) -> None:
        for object in self.sprites():
            if object.has_component(ObjectTexture):
                object.draw(surface)