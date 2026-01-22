"Contains predefined fonts to be used in the game"

from .font_types import Font, IconFont, TextureFont




large_font = Font("assets/fonts/upheavtt.ttf", 20, 2)
small_font = Font("assets/fonts/Tiny5-Regular.ttf", 8, 1)
font_with_icons = IconFont(8, 1)
title_font = TextureFont("title_font", 10)


def init():
    title_font.init_texture_map()