import pygame as p

from . import State






class PauseMenu(State):
    def __init__(self, state_stack = None):
        super().__init__(state_stack)



    def userinput(self, inputs):
        if inputs.check_input("escape"):
            self.state_stack.pop()

    


    def draw(self, surface, lerp_amount=0):
        self.prev_state.draw(surface)
        surface.fill((50, 50, 50), special_flags=p.BLEND_SUB)
