import pygame as pg

from src.custom_types import Timer
from src.ui import blit_to_center, font, effects

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





class ShowText(PassThroughState):
    "Shows text above previous state at the center of the screen."

    def __init__(self, text: str, offset=(0, 0)):
        super().__init__()
        self.__text = effects.AnimatedText(text, "show_level_name_b", font.large_font)
        self.__offset = offset
    

    def update(self):
        super().update()
        self.__text.update()

        if self.__text.animations_complete and self.is_top_state():
            self.state_stack.pop()

    def draw(self, surface, lerp_amount=0):
        super().draw(surface, lerp_amount)
        blit_to_center(self.__text.render(), surface, self.__offset)
        



class Freeze(PassThroughState):
    def __init__(self, ticks: int):
        super().__init__()
        self.__timer = Timer(ticks, exec_after=self.state_stack.pop()).start()
    

    def update(self):
        if self.is_top_state():
            self.__timer.update()
