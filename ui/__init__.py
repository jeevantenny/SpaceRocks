import pygame as p
from typing import Literal

from input_device import get_action_icon_name

from file_processing import assets






def add_padding(text: str, length: int, side: Literal["left", "right"] = "right", pad_char=' ') -> str:
    "Returns string with a minimum length containing the text and padding."

    if side == "left":
        return f"{text}{pad_char*max(length-len(text), 0)}"
    
    else:
        return f"{pad_char*max(length-len(text), 0)}{text}"






def load_icon(icon_name) -> p.Surface:
    action_icon_name = get_action_icon_name(icon_name)
    if action_icon_name is not None:
        working_name = action_icon_name
    else:
        working_name = icon_name

    try:
        return assets.load_texture_map("icons")[working_name]
    except KeyError:
        raise ValueError(f"Invalid icon name '{icon_name}'")