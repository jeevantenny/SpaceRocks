import pygame as pg
from functools import partial, lru_cache

from . import load_icon

import game_errors
from custom_types import TextureMap, Animation

from file_processing import get_resource_path, assets







class Font:
    def __init__(self, font_path: str, base_size: int, shadow_offset: int):
        self.__font = partial(pg.font.Font, get_resource_path(font_path))
        self.__base_size =base_size
        self.__shadow_offset = shadow_offset

    
    def render(self, text: str, size=1, color_a: pg.typing.ColorLike="#dd6644", color_b: pg.typing.ColorLike="#550011", cache=True) -> pg.Surface:
        if cache:
            return self.__render_cached(text, size, color_a, color_b)
        else:
            return self.__render(text, size, color_a, color_b)

        
    
    def __render(self, text: str, size=1, color_a: pg.typing.ColorLike="#dd6644", color_b: pg.typing.ColorLike="#550011") -> pg.Surface:
        if self.__font is None:
            raise game_errors.InitializationError(self)

        sized_font = self.__font(self.__base_size*size)

        main = sized_font.render(text, False, color_a, assets.COLORKEY)
        main.set_colorkey(assets.COLORKEY)
        background = sized_font.render(text, False, color_b, assets.COLORKEY)
        
        surface = assets.colorkey_surface(main.get_size()+pg.Vector2(1, 1)*self.__shadow_offset)
        surface.blit(background, pg.Vector2(1, 1)*self.__shadow_offset*size)
        surface.blit(main, (0, 0))

        return surface


    @lru_cache(8)
    def __render_cached(self, text, size, color_a, color_b) -> pg.Surface:
        return self.__render(text, size, color_a, color_b)






class TextureFont:
    def __init__(self, texture_map_name: str, space_width: int, letter_spacing=1, case_sensitive=False):
        self.__texture_map_name = texture_map_name
        self.__space_width = space_width
        self.__letter_spacing = letter_spacing
        self.__case_sensitive = case_sensitive

    
    def init_texture_map(self) -> None:
        self.__texture_map = assets.load_texture_map(self.__texture_map_name)





    @lru_cache(3)
    def render(self, text: str) -> pg.Surface:
        width = height = 0
        if not self.__case_sensitive:
            text = text.lower()

        glyphs = []
        
        for char in text:
            if char == ' ':
                width += self.__space_width-self.__letter_spacing
                continue

            glyph = self.__texture_map[char]
            height = max(height, glyph.height)
            glyphs.append((glyph, width))
            width += glyph.width+self.__letter_spacing

        surface = assets.colorkey_surface((width, height))
        # surface.fill("white")

        for glyph, x in glyphs:
            surface.blit(glyph, (x, 0))


        return surface

            
        








class IconFont(Font):

    def __init__(self, base_size, shadow_offset):
        super().__init__("assets/fonts/tiny5-Regular.ttf", base_size, shadow_offset)

    def render(self, text, size=1):
        elements = self.__get_text_elements(text)
        surface_width = sum([e.width+1 for e in elements])+1
        surface_height = max(elements, key=lambda x: x.height).height
        surface = assets.colorkey_surface((surface_width, surface_height))

        x_offset = 0
        for e in elements:
            surface.blit(e, (x_offset, (surface_height-e.height)*0.5))
            x_offset += e.width+1
        
        return pg.transform.scale_by(surface, size) if size != 1 else surface
    

    def __get_text_elements(self, text: str) -> list[pg.Surface]:
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