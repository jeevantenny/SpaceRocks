import pygame as pg


from . import State




class BackgroundTint(State):
    def __init__(self, tint_color: pg.typing.ColorLike):
        super().__init__()
        self.__tint_color = tint_color

    def userinput(self, inputs):
        self.prev_state.userinput(inputs)
        
    def update(self):
        self.prev_state.update()

    def draw(self, surface, lerp_amount=0):
        self.prev_state.draw(surface, lerp_amount)
        surface.fill(self.__tint_color, special_flags=pg.BLEND_RGB_MULT)