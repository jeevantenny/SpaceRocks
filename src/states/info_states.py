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
        surface.fill("black")
        ui.blit_to_center(ui.font.large_font.render("DEMO MODE"), surface)
        ui.blit_to_center(ui.font.small_font.render("Press enter to start"), surface, (0, 30))



class NoMoreLevels(State):
    def userinput(self, inputs):
        if inputs.keyboard_mouse.action_keys.get(pg.K_RETURN):
            from .play import Play
            self.state_stack.quit()
            self.state_stack.push(Play("level_1"))
        

    def draw(self, surface, lerp_amount=0):
        surface.fill("black")
        ui.blit_to_center(ui.font.large_font.render("THAT WAS THE LAST LEVEL"), surface)
        ui.blit_to_center(ui.font.small_font.render("More levels will be developed -- Press enter to restart"), surface, (0, 30))
        ui.blit_to_center(ui.font.small_font.render("Thanks for playing :)"), surface, (0, 40))


    def debug_info(self):
        return "Thanks for checking out debug mode!"