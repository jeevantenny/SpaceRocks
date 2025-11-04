import pygame as pg

from src import ui


from . import PassThroughState




class BackgroundTint(PassThroughState):
    "Tints the state behind it to a certain color."

    def __init__(self, tint_color: pg.typing.ColorLike, pop_when_at_top=True):
        super().__init__()
        self.__tint_color = tint_color
        self.__pop_when_at_top = pop_when_at_top
        
    def update(self):
        super().update()
        
        if self.__pop_when_at_top and self.state_stack.top_state is self:
            self.state_stack.pop()

    def draw(self, surface, lerp_amount=0):
        super().draw(surface, lerp_amount)
        surface.fill(self.__tint_color, special_flags=pg.BLEND_RGB_MULT)





class ShowLevelName(PassThroughState):
    "Shows the name of the current level."

    def __init__(self, level_name: str):
        super().__init__()
        self.__title = ui.elements.AltTitleText(level_name, "show_level_name_b")
    

    def update(self):
        super().update()
        self.__title.update()

        if self.__title.animations_complete and self.is_top_state():
            self.state_stack.pop()

    def draw(self, surface, lerp_amount=0):
        super().draw(surface, lerp_amount)
        ui.blit_to_center(self.__title.render(), surface, (0, -40))
        