import pygame as pg

from . import State





class DemoState(State):
    def userinput(self, inputs):
        if inputs.keyboard_mouse.action_keys.get(pg.K_RETURN):
            self.state_stack.pop()



    def debug_info(self):
        return "Press Enter to continue"