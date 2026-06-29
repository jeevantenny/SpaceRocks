import pygame as pg

from src.file_processing import assets
from src.custom_types import Timer
from src.game_objects.powerups import PowerUp, PowerUpGroup

from . import font, effects, render_status_bar
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
    

    def render(self) -> pg.Surface | None:
        if not self.__powerups:
            return None

        output = assets.colorkey_surface(self.size)
        for i, powerup in enumerate(self.__powerups):
            output.blit(self.__render_powerup(powerup), (0, i*23))
        return output
    



class HudMessage(UIElement):
    def __init__(self):
        super().__init__()
        self.__message_queue: list[tuple[str, int]] = []
        self.__message_text: effects.AnimatedText | None = None
        self.__timer = Timer(1)
        self.__state = 0
    
    def queue_message(self, message: str, duration=40) -> None:
        self.__message_queue.append((message, duration))
    
    def update(self):
        match self.__state:
            case 0:
                if self.__message_queue:
                    self.__set_message(*self.__message_queue.pop(0))
                    self.__state = 1
            case 1:
                if self.__message_text.animations_complete:
                    self.__timer.start()
                    self.__state = 2
            case 2:
                if self.__timer.complete:
                    self.__message_text.set_effect("main_exit")
                    self.__state = 3
            case 3:
                if self.__message_text.animations_complete:
                    self.__state = 0
        
        self.__timer.update()
        if self.__message_text is not None:
            self.__message_text.update()
    
    def render(self):
        if self.__state == 0:
            return None
        elif self.__message_text is not None:
            return self.__message_text.render()


    def __set_message(self, message: str, duration: int) -> None:
        self.__message_text = effects.AnimatedText(message, "main_entrance_b", font.large_font)
        self.__timer = Timer(duration).start()
        