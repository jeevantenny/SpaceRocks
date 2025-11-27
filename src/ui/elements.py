import pygame as pg
from typing import Iterable

from src.custom_types import Animation, AnimController
from src.input_device import InputInterpreter
from src.file_processing import assets

from . import font




class UIElement:
    def __init__(self, label: str | None = None) -> None:
        self._label = label

    @property
    def size(self) -> pg.typing.Point: ...

    def get_label(self) -> str:
        return self._label

    def userinput(self, inputs: InputInterpreter) -> None:
        pass

    def update(self) -> None:
        pass

    def render(self) -> pg.Surface: ...




class ElementList:
    __padding = 5
    def __init__(self, elements: Iterable[UIElement] | None = None, wrap_list=False):
        self.__container = list(elements)
        self.__current = 0
        self.__wrap_list = wrap_list
    
    def userinput(self, inputs: InputInterpreter) -> None:
        if self.__container:
            if inputs.check_input("up"):
                self.__current -= 1
            if inputs.check_input("down"):
                self.__current += 1

            if self.__wrap_list:
                self.__current %= len(self.__container)
            else:
                self.__current = pg.math.clamp(self.__current, 0, len(self.__container)-1)

            self.__container[self.__current].userinput(inputs)


    def update(self) -> None:
        for element in self.__container:
            element.update()


    def draw(self, subsurface: pg.Surface) -> None:
        # subsurface.fill("blue")
        y_offset = self.__padding
        for i, element in enumerate(self.__container):
            if i == self.__current:
                subsurface.fill("#550011", (0, y_offset-self.__padding*0.5, subsurface.width, 13+self.__padding))
            
            position = (subsurface.width-element.size[0]-self.__padding, y_offset)
            label = element.get_label()
            if label is not None:
                label_pos = (self.__padding, y_offset+2)
                subsurface.blit(font.small_font.render(label), label_pos)
            subsurface.blit(element.render(), position)

            y_offset += 13 + self.__padding




class Slider(UIElement):
    __size = (75, 12)
    def __init__(self, slider_range: tuple[int, int], value: int, step=1, name: str | None = None):
        self.__min, self.__max = slider_range
        if self.__max <= self.__min:
            raise ValueError("First value in range must be less than second value")

        if self.__min <= value <= self.__max:
            self.__value = value
        else:
            raise ValueError(f"Starting value must be within slider_range {slider_range}, not {value}")
        
        self.__inverse_of_range = 1/(self.__max-self.__min)


        self.__step = step
        if name is None:
            self._label = "Slider"
        else:
            self._label = name

        texture_map = assets.load_texture_map("ui_elements")
        self.__base_texture = texture_map["slider_base"]
        self.__bar_texture = texture_map["slider_bar"]
        self.__handle_texture = texture_map["slider_handle"]


    @property
    def size(self) -> pg.typing.Point:
        return self.__size
    
    @property
    def value(self) -> int:
        return self.__value
    
    def get_label(self):
        return f"{self._label}: {self.__value}"
    
    def slider_amount(self) -> float:
        "Returns how full the slider is from 0.0 to 1.0."
        return (self.__value-self.__min)*self.__inverse_of_range
    
    def userinput(self, inputs):
        if inputs.check_input("left"):
            self.__value -= self.__step
        if inputs.check_input("right"):
            self.__value += self.__step
        self.__value = pg.math.clamp(self.__value, self.__min, self.__max)
    
    def render(self):
        surface = self.__base_texture.copy()
        bar_area = (0, 0, 3+(self.__size[0]-7)*self.slider_amount(), self.__size[1])
        surface.blit(self.__bar_texture.subsurface(bar_area))
        handle_pos = (2+(self.__size[0]-16)*self.slider_amount(), 2)
        surface.blit(self.__handle_texture, handle_pos)
        return surface
        
    
    

class Toggle(UIElement):
    __size = (31, 13)

    def __init__(self, on=False, label: str | None = None):
        super().__init__(label)
        self.__on = on
        self.__texture_map = assets.load_texture_map("ui_elements")
        self.__controller = AnimController(
            assets.load_anim_controller_data("toggle"),
            Animation.load_from_dict(assets.load_anim_data("ui_elements"))
        )


    @property
    def size(self) -> pg.typing.Point:
        return self.__size
    
    @property
    def on(self) -> bool:
        return self.__on

    
    def userinput(self, inputs):
        if (inputs.check_input("select")
            or (not self.__on and inputs.check_input("right"))
            or (self.__on and inputs.check_input("left"))):
            self.__on = not self.__on
        
    
    def update(self):
        self.__controller.update(self)

    def render(self):
        return self.__controller.get_frame(self.__texture_map)