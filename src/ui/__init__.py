"This package contains things that are useful for drawing things for the user interface."

import pygame as pg
from typing import Literal

from src.input_device import get_control_icon_name
from src.file_processing import assets






def load_icon(icon_name) -> pg.Surface:
    action_icon_name = get_control_icon_name(icon_name)
    if action_icon_name is not None:
        working_name = action_icon_name
    else:
        working_name = icon_name

    try:
        return assets.load_texture_map("icons")[working_name]
    except KeyError:
        raise ValueError(f"Invalid icon name '{icon_name}'")



def blit_to_center(source: pg.Surface, dest: pg.Surface, offset: pg.typing.Point = (0, 0)):
    blit_bos = (pg.Vector2(dest.size)-source.size)*0.5 + offset
    dest.blit(source, blit_bos)