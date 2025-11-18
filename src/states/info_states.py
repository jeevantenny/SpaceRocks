import pygame as pg

from src.ui import font, blit_to_center
from src.file_processing import data

from . import State





class DemoState(State):
    def userinput(self, inputs):
        if inputs.keyboard_mouse.tap_keys.get(pg.K_RETURN):
            self.state_stack.pop()



    def debug_info(self):
        return "Press Enter to start"
    

    def draw(self, surface, lerp_amount=0):
        surface.fill("black")
        blit_to_center(font.large_font.render("DEMO MODE"), surface)
        blit_to_center(font.small_font.render("Press enter to start"), surface, (0, 30))



class NoMoreLevels(State):
    def userinput(self, inputs):
        if inputs.keyboard_mouse.tap_keys.get(pg.K_RETURN):
            self.state_stack.force_quit()
            data.delete_progress()

            from .init_state import Initializer
            Initializer(self.state_stack)


    def draw(self, surface, lerp_amount=0):
        surface.fill("black")
        blit_to_center(font.large_font.render("THAT WAS THE LAST LEVEL"), surface)
        blit_to_center(font.small_font.render("More levels will be developed -- Press enter to restart"), surface, (0, 30))
        blit_to_center(font.small_font.render("Thanks for playing :)"), surface, (0, 40))


    def debug_info(self):
        return "Thanks for checking out debug mode!"




class DeleteUserDataOption(State):

    def userinput(self, inputs):
        tap_keys = inputs.keyboard_mouse.tap_keys
        hold_keys = inputs.keyboard_mouse.hold_keys

        if tap_keys[pg.K_ESCAPE]:
            self.state_stack.pop()

        if hold_keys[pg.KMOD_ALT] and hold_keys[pg.KMOD_SHIFT] and tap_keys[pg.K_d]:
            data.delete_user_data()
            self.state_stack.force_quit()
            self.state_stack.push(UserDataDeleted())


    
    def draw(self, surface, lerp_amount=0):
        surface.fill("black")
        blit_to_center(font.large_font.render("DELETE USER DATA?", 1, "#aa0055"), surface, (0, -20))
        blit_to_center(font.small_font.render("Are you sure you want to delete all user data?", 1, "#aa0055"), surface, (0, 10))
        blit_to_center(font.small_font.render("If so press ALT + SHIFT + D", 1, "#aa0055"), surface, (0, 20))
        blit_to_center(font.small_font.render("Press ESC to cancel"), surface, (0, 30))





class UserDataDeleted(State):
    def __init__(self):
        super().__init__()
        self.__info_text = pg.Surface((1, 1))

    def userinput(self, inputs):
        if inputs.check_input("select"):
            self.state_stack.pop()
            from .init_state import Initializer
            Initializer(self.state_stack)
        
        self.__info_text = font.font_with_icons.render("Press<select> to go to main menu")
    

    def draw(self, surface, lerp_amount=0):
        surface.fill("black")
        blit_to_center(font.large_font.render("USER DATA DELETED", 1, "#aa0055"), surface)
        blit_to_center(self.__info_text, surface, (0, 30))