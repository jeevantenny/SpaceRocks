import pygame as p
from functools import partial

import game_errors

from file_processing import get_resource_path, assets







class Font:
    font_path: str
    _shadow_offset: int
    _base_size: int
    _font: partial[p.Font] | None = None

    def __init__(self):
        "To initialize font. Only needed to be used once."

        if self._font is None:
            type(self)._font = partial(p.font.Font, get_resource_path(self.font_path))
    
    @classmethod
    def render(cls, text: str, size=1, color_a: p.typing.ColorLike ="#dd6644", color_b: p.typing.ColorLike ="#550011") -> p.Surface:
        if cls._font is None:
            raise game_errors.InitializationError(cls)

        sized_font = cls._font(cls._base_size*size)

        main = sized_font.render(text, False, color_a, assets.COLORKEY)
        main.set_colorkey(assets.COLORKEY)
        background = sized_font.render(text, False, color_b, assets.COLORKEY)
        
        surface = p.Surface(main.get_size()+p.Vector2(1, 1)*cls._shadow_offset)
        surface.fill(assets.COLORKEY)

        surface.blit(background, p.Vector2(1, 1)*cls._shadow_offset*size)
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




LargeFont()
SmallFont()