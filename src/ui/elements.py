import pygame as pg
from typing import Iterable

from src.input_device import InputInterpreter
from src.file_processing import assets

from . import font




class UIElement:
    def __init__(self, label: str | None = None) -> None:
        self.label = label

    @property
    def size(self) -> pg.typing.Point: ...

    def userinput(self, inputs: InputInterpreter) -> None:
        pass

    def update(self) -> None:
        pass

    def render(self) -> pg.Surface: ...




class ElementList:
    __padding = 5
    def __init__(self, elements: Iterable[UIElement] | None = None):
        self.__container = list(elements)
        self.__current = 0
    
    def userinput(self, inputs: InputInterpreter) -> None:
        if self.__container:
            if inputs.check_input("up"):
                self.__current -= 1
            if inputs.check_input("down"):
                self.__current += 1

            self.__current %= len(self.__container)

            self.__container[self.__current].userinput(inputs)


    def draw(self, subsurface: pg.Surface) -> None:
        # subsurface.fill("blue")
        y_offset = self.__padding
        for i, element in enumerate(self.__container):
            if i == self.__current:
                subsurface.fill("#550011", (0, y_offset-self.__padding*0.5, subsurface.width, element.size[1]+self.__padding))
            
            position = (subsurface.width-element.size[0]-self.__padding, y_offset)
            if element.label is not None:
                label_pos = (self.__padding, y_offset+2)
                subsurface.blit(font.small_font.render(element.label), label_pos)
            subsurface.blit(element.render(), position)
            y_offset += element.size[1] + self.__padding




class Slider(UIElement):
    __size = (100, 30)
    def __init__(self, range: tuple[int, int]):
        self.__min, self.__max = range
        texture_map = assets.load_texture_map("ui_elements")
        self.__base_texture = texture_map["slider_base"]
        self.__handle_texture = texture_map["slider_handle"]

    @property
    def size(self) -> pg.typing.Point:
        return self.__size
    
    def render(self):
        surface = assets.colorkey_surface(self.__size)
        
    
    

class Toggle(UIElement):
    __size = (31, 13)

    def __init__(self, on=False, label: str | None = None):
        super().__init__(label)
        self.__on = on
        self.__texture_map = assets.load_texture_map("ui_elements")


    @property
    def size(self) -> pg.typing.Point:
        return self.__size
    
    @property
    def on(self) -> bool:
        return self.__on

    def set(self, value: bool) -> None:
        self.__on = value

    
    def userinput(self, inputs):
        if inputs.check_input("select"):
            self.__on = not self.__on

    def render(self):
        if self.__on:
            return self.__texture_map["toggle_4"]
        else:
            return self.__texture_map["toggle_1"]