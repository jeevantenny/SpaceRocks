import pygame as pg

from src.file_processing import assets
from src.game_objects.powerups import PowerUp, PowerUpGroup

from . import font, render_status_bar
from .elements import UIElement
    


class ProgressBar(UIElement):
    "Shows how much of a level the player has completed."

    def __init__(self):
        texture_map = assets.load_texture_map("ui_elements")
        self.__base_texture = texture_map["progress_bar_base"]
        self.__overlay_texture = texture_map["progress_bar_overlay"]

    
    def render(self, amount: float) -> pg.Surface:
        "Render progress bar for the given amount between 0 and 1."
        return render_status_bar(self.__base_texture, self.__overlay_texture, amount)
    


class LivesIndicator(UIElement):
    "Shows how many lives the player has left during a level."

    __texture_size = 16
    __padding = 5

    def __init__(self, max_lives: int):
        texture_map = assets.load_texture_map("ui_elements")
        self.__icon_texture = texture_map["lives_icon"]
        self.__blank_texture = texture_map["lives_empty"]
        self.__max_lives = max_lives

        self.__output_texture_size = (self.__texture_size*self.__max_lives + self.__padding*(self.__max_lives-1), self.__texture_size)


    def render(self, lives: int) -> pg.Surface:
        output = assets.colorkey_surface(self.__output_texture_size)
        for i in range(self.__max_lives):
            if i >= self.__max_lives - lives:
                texture = self.__icon_texture
            else:
                texture = self.__blank_texture

            output.blit(texture, (i*(self.__texture_size+self.__padding), 0))
        
        return output
    



class PowerupList(UIElement):
    """Show all powerups that the player currently has."""

    def __init__(self, powerup_group: PowerUpGroup):
        self.__powerups = powerup_group

        texture_map = assets.load_texture_map("ui_elements")
        self.__base_texture = texture_map["powerup_base"]
        self.__overlay_texture = texture_map["powerup_overlay"]

        self.__powerup_textures = assets.load_texture_map("powerups")


    @property
    def size(self):
        return (80, max(len(self.__powerups)*23 - 2, 1))
    

    def update_powerup_group(self, powerup_group: PowerUpGroup) -> None:
        self.__powerups = powerup_group
    

    def __render_powerup(self, powerup: PowerUp) -> pg.Surface:
        output = render_status_bar(self.__base_texture, self.__overlay_texture, powerup.indicator_slider_amount())
        output.blit(self.__powerup_textures[powerup.texture_key], (2, 2))
        text = font.small_font.render(powerup.get_display_name(), color_a="#eedd88", color_b="#550011")
        output.blit(text, (21, 5))
        return output
    

    def render(self) -> pg.Surface:
        output = assets.colorkey_surface(self.size)
        for i, powerup in enumerate(self.__powerups):
            output.blit(self.__render_powerup(powerup), (0, i*23))
        return output
    