import pygame as p
from typing import Literal

from file_processing import assets






def add_padding(text: str, length: int, side: Literal["left", "right"] = "right", pad_char=' ') -> str:
    "Returns string with a minimum length containing the text and padding."

    if side == "left":
        return f"{text}{pad_char*max(length-len(text), 0)}"
    
    else:
        return f"{pad_char*max(length-len(text), 0)}{text}"