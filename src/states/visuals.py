import pygame as pg

from src.ui import blit_to_center, font, elements
from src.custom_types import Timer

from . import PassThroughState




class BackgroundTint(PassThroughState):
    "Tints the state behind it to a certain color."

    def __init__(self, tint_color: pg.typing.ColorLike, pop_when_at_top=True):
        super().__init__()
        self.__tint_color = tint_color
        self.__pop_when_at_top = pop_when_at_top
        
    def update(self):
        super().update()
        
        if self.__pop_when_at_top and self.is_top_state():
            self.state_stack.pop()

    def draw(self, surface, lerp_amount=0):
        super().draw(surface, lerp_amount)
        surface.fill(self.__tint_color, special_flags=pg.BLEND_RGB_MULT)





class ShowLevelName(PassThroughState):
    "Shows the name of the current level."

    def __init__(self, level_name: str):
        super().__init__()
        self.__title = elements.AltTitleText(level_name, "show_level_name_b")
    

    def update(self):
        super().update()
        self.__title.update()

        if self.__title.animations_complete and self.is_top_state():
            self.state_stack.pop()

    def draw(self, surface, lerp_amount=0):
        super().draw(surface, lerp_amount)
        blit_to_center(self.__title.render(), surface, (0, -40))
        



class Freeze(PassThroughState):
    def __init__(self, ticks: int):
        super().__init__()
        self.__timer = Timer(ticks, exec_after=self.state_stack.pop()).start()
    

    def update(self):
        if self.is_top_state():
            self.__timer.update()
