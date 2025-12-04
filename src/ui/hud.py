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