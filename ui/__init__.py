import pygame as p
from functools import partial

from file_processing import assets






class Font:
    font_path: str
    _shadow_offset: int
    _base_size: int

    def __init__(self):
        self._font = partial(p.font.Font, self.font_path)
    

    def render(self, text: str, size=1, color_a: p.typing.ColorLike ="white", color_b: p.typing.ColorLike =(100, 0, 0), padding=0) -> p.Surface:

        sized_font = self._font(self._base_size*size)

        main = sized_font.render(text, False, color_a, assets.COLORKEY)
        main.set_colorkey(assets.COLORKEY)
        background = sized_font.render(text, False, color_b, assets.COLORKEY)
        
        surface = p.Surface(main.get_size()+p.Vector2(1, 1)*self._shadow_offset)
        surface.fill(assets.COLORKEY)

        surface.blit(background, p.Vector2(1, 1)*self._shadow_offset)
        surface.blit(main, (0, 0))
        surface.set_colorkey(assets.COLORKEY)

        
        return p.transform.scale_by(surface, size)





class LargeFont(Font):
    font_path = "assets/fonts/upheavtt.ttf"
    _shadow_offset = 2
    _base_size = 20
    







class SmallFont(Font):
    font_path = "assets/fonts/tiny5-Regular.ttf"
    _shadow_offset = 1
    _base_size = 8
