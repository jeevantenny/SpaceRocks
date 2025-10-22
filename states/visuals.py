import pygame as pg


from . import State




class BackgroundTint(State):
    def __init__(self, tint_color: pg.typing.ColorLike, pop_when_at_top=True):
        super().__init__()
        self.__tint_color = tint_color
        self.__pop_when_at_top = pop_when_at_top

    def userinput(self, inputs):
        self.prev_state.userinput(inputs)
        
    def update(self):
        self.prev_state.update()
        
        if self.__pop_when_at_top and self.state_stack.top_state is self:
            self.state_stack.pop()

    def draw(self, surface, lerp_amount=0):
        self.prev_state.draw(surface, lerp_amount)
        surface.fill(self.__tint_color, special_flags=pg.BLEND_RGB_MULT)