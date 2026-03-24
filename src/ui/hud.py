import pygame as pg

from src.file_processing import assets


    


class ProgressBar:
    "Shows how much of a level the player has completed."

    def __init__(self):
        texture_map = assets.load_texture_map("ui_elements")
        self.__base_texture = texture_map["progress_bar_base"]
        self.__overlay_texture = texture_map["progress_bar_overlay"]

    
    def render(self, amount: float) -> pg.Surface:
        "Render progress bar for the given amount between 0 and 1."

        amount = pg.math.clamp(amount, 0, 1)
        output = self.__base_texture.copy()
        overlay = self.__overlay_texture.subsurface(0, 0, int(88*amount), 8)
        output.blit(overlay, (1, 1))
        return output
    


class LivesIndicator:
    "Shows how many loves the player has left during boss battle."

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