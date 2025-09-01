import pygame as pg
from typing import Literal
from functools import partial

from . import load_icon

import game_errors
from custom_types import TextureMap
from input_device import get_action_icon_name

from file_processing import get_resource_path, assets







class Font:
    font_path: str
    _shadow_offset: int
    _base_size: int
    _font: partial[pg.Font] | None = None

    def __init__(self):
        "To initialize font. Only needed to be used once."

        if self._font is None:
            type(self)._font = partial(pg.font.Font, get_resource_path(self.font_path))
    
    @classmethod
    def render(cls, text: str, size=1, color_a: pg.typing.ColorLike="#dd6644", color_b: pg.typing.ColorLike="#550011") -> pg.Surface:
        if cls._font is None:
            raise game_errors.InitializationError(cls)

        sized_font = cls._font(cls._base_size*size)

        main = sized_font.render(text, False, color_a, assets.COLORKEY)
        main.set_colorkey(assets.COLORKEY)
        background = sized_font.render(text, False, color_b, assets.COLORKEY)
        
        surface = pg.Surface(main.get_size()+pg.Vector2(1, 1)*cls._shadow_offset)
        surface.fill(assets.COLORKEY)

        surface.blit(background, pg.Vector2(1, 1)*cls._shadow_offset*size)
        surface.blit(main, (0, 0))
        surface.set_colorkey(assets.COLORKEY)

        
        return surface





class LargeFont(Font):
    font_path = "assets/fonts/upheavtt.ttf"
    _shadow_offset = 2
    _base_size = 20
    


class SmallFont(Font):
    font_path = "assets/fonts/tiny5-Regular.ttf"
    _shadow_offset = 1
    _base_size = 8



class FontWithIcons(Font):
    font_path = "assets/fonts/tiny5-Regular.ttf"
    _shadow_offset = 1
    _base_size = 8



    @classmethod
    def render(cls, text, size=1):
        elements = cls.__get_text_elements(text)
        surface_width = sum([e.width+1 for e in elements])+1
        surface = assets.colorkey_surface((surface_width, 10))
        # surface.fill("green")

        x_offset = 0
        for e in elements:
            surface.blit(e, (x_offset, 0))
            x_offset += e.width+1
        
        return pg.transform.scale_by(surface, size)
    

    @classmethod
    def __get_text_elements(cls, text: str) -> list[pg.Surface]:
        elements = []
        back_pt = 0
        front_pt = 0
        icon_mode = False

        while back_pt < len(text):
            if icon_mode:
                front_pt = text.find('>', back_pt)
            else:
                front_pt = text.find('<', back_pt)
                if front_pt == -1:
                    elements.append(super().render(text[back_pt:]))
                    return elements
            
            block = text[back_pt:front_pt]

            if block != "":
                if icon_mode:
                    elements.append(load_icon(block))
                else:
                    elements.append(super().render(block))
            
            back_pt = front_pt+1
            icon_mode = not icon_mode
        
        return elements








def init():
    LargeFont()
    SmallFont()
    FontWithIcons()