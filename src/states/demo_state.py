import pygame as pg

from src import ui

from . import State





class DemoState(State):
    def userinput(self, inputs):
        if inputs.keyboard_mouse.action_keys.get(pg.K_RETURN):
            self.state_stack.pop()



    def debug_info(self):
        return "Press Enter to start"
    

    def draw(self, surface, lerp_amount=0):
        ui.blit_to_center(ui.font.large_font.render("DEMO MODE"), surface)
        ui.blit_to_center(ui.font.small_font.render("Press enter to start"), surface, (0, 30))