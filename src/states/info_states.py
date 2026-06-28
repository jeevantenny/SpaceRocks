import pygame as pg
from typing import Callable

from src.ui import font, blit_to_center
from src.file_processing import data
from src.game_objects.powerups import PowerUp

from . import State
from .visuals import add_background_tint






class InfoState(State):
    def __init__(self,
                 title: str, subtitle: str, prompt = "Continue<select>",
                 background_color="#000000",
                 text_color_a="#dd6644", text_color_b="#550011",
                 confirm_action: Callable[[], None] = None,
                 can_escape=False):
        super().__init__()
        self.title = title
        self.__subtitle = subtitle
        self.__prompt = prompt
        self.__background_color = background_color
        self.__text_colors = text_color_a, text_color_b
        self.__confirm_action = confirm_action
        self.__can_escape = can_escape
    
    def userinput(self, inputs):
        if inputs.check_input("select"):
            self.state_stack.pop()
            if self.__confirm_action is not None:
                self.__confirm_action()
        
        elif self.__can_escape and inputs.check_input("back"):
            self.state_stack.pop()


    def debug_info(self):
        return self.__prompt
    
    def draw(self, surface, lerp_amount=0):
        surface.fill(self.__background_color)
        if self.__subtitle:
            offset = -10
        else:
            offset = -5

        blit_to_center(font.large_font.render(self.title, 1, *self.__text_colors), surface, (0, offset))
        offset += 20
        if self.__subtitle:
            blit_to_center(font.small_font.render(self.__subtitle, 1, *self.__text_colors), surface, (0, offset))
            offset += 30
        else:
            offset += 15
        
        blit_to_center(font.icon_font.render(self.__prompt), surface, (0, offset))

        if self.__can_escape:
            surface.blit(font.icon_font.render("Back<back>"), (10, surface.height-18))




class PowerupInfo(State):
    def __init__(self, powerup_type: type[PowerUp], background_tint_color: pg.typing.ColorLike = "#777777"):
        super().__init__()
        self.__powerup_name = powerup_type.get_display_name()
        self.__info_text = powerup_type.get_info_text()
        self.__usage_instr = powerup_type.get_usage_instr()
        self.__tint_color = background_tint_color


    def userinput(self, inputs):
        if inputs.check_input("select"):
            self.state_stack.pop()
    

    def draw(self, surface, lerp_amount=0):
        self.prev_state.draw(surface)
        add_background_tint(surface, self.__tint_color)
        blit_to_center(font.large_font.render(self.__powerup_name), surface, (0, -20))
        blit_to_center(font.small_font.render(self.__info_text), surface, (0, 0))
        if self.__usage_instr is not None:
            blit_to_center(font.icon_font.render(self.__usage_instr), surface, (0, 20))
        blit_to_center(font.icon_font.render("OK<select>"), surface, (0, 50))




class DeleteUserDataOption(State):

    def userinput(self, inputs):
        tap_keys = inputs.keyboard_mouse.tap_keys
        hold_keys = inputs.keyboard_mouse.hold_keys

        if inputs.check_input("back"):
            self.state_stack.pop()

        if hold_keys[pg.KMOD_ALT] and hold_keys[pg.KMOD_SHIFT] and tap_keys[pg.K_d]:
            data.delete_user_data()
            self.state_stack.force_quit()

            from .init_state import Initializer

            InfoState(
                "USER DATA DELETED",
                "",
                "Main Menu<select>",
                text_color_a="#aa0055",
                confirm_action=lambda: Initializer.main_title_screen(self.state_stack)
                ).add_to_stack(self.state_stack)


    
    def draw(self, surface, lerp_amount=0):
        surface.fill("black")
        blit_to_center(font.large_font.render("DELETE USER DATA?", color_a="#aa0055"), surface, (0, -20))
        blit_to_center(font.small_font.render("Are you sure you want to delete all user data?", color_a="#aa0055"), surface, (0, 5))
        blit_to_center(font.small_font.render("If so press ALT + SHIFT + D", color_a="#aa0055"), surface, (0, 15))
        blit_to_center(font.icon_font.render("Back<back>"), surface, (0, 35))
