"Contains functions that loads all assets required by the game."

import pygame as pg
from typing import overload
from functools import lru_cache

import debug
from src.custom_types import GameSound, TextureMap, AnimData, ControllerData

from . import load_json


asset_cache = lru_cache(8)


TEXTURES_DIR = "assets/textures"
TEXTURE_MAPS_DIR = "assets/texture_maps"

ANIMATIONS_DIR = "assets/animations"
ANIM_CONTROLLERS_DIR = "assets/anim_controllers"

SOUNDS_DIR = "assets/sounds"

COLORKEY = (255, 0, 255)


__sound_definition = load_json("assets/sound_definitions")


@asset_cache
def load_texture(path: str, palette_swap_name: str | None = None, file_type="png") -> pg.Surface:
    "Loads a texture from the textures folder as a pygame.Surface"
    texture_path = f"{TEXTURES_DIR}/{path}.{file_type}"
    texture = pg.image.load(texture_path).convert()
    if not debug.Cheats.ignore_colorkey:
        texture.set_colorkey(COLORKEY)
    if palette_swap_name is not None:
        texture = palette_swap(texture, palette_swap_name)
    # print(path, palette_swap_name)
    return texture






def colorkey_surface(size: pg.typing.Point) -> pg.Surface:
    "Creates a surface that is made transparent using the colorkey."
    surface = pg.Surface(size)
    if not debug.Cheats.ignore_colorkey:
        surface.set_colorkey(COLORKEY)
    surface.fill(COLORKEY)
    return surface



@asset_cache
def load_texture_map(path: str, palette_swap_name: str | None = None) -> TextureMap:
    mapping_data = load_json(f"{TEXTURE_MAPS_DIR}/{path}.texture_map")
    main_texture = load_texture(mapping_data["texture"], palette_swap_name)

    texture_map = {}
    for name, area in mapping_data["mappings"].items():
        texture_map[name] = main_texture.subsurface(area)
    
    return texture_map





@overload
def palette_swap(texture: pg.Surface, load_swap_file: str) -> pg.Surface: ...
@overload
def palette_swap(texture: pg.Surface, swap_colors: dict[str, str]) -> pg.Surface: ...

def palette_swap(texture: pg.Surface, swap_colors: dict[str, str] | str) -> pg.Surface:
    "Swaps all colors in a surface with a corresponding color if specified."

    if isinstance(swap_colors, str):
        swap_colors = load_json(f"assets/palette_swaps/{swap_colors}")
    
    masks: dict[pg.typing.ColorLike, pg.Mask] = {}

    for old_c, new_c in swap_colors.items():
        masks[new_c] = pg.mask.from_threshold(texture, old_c, (1, 1, 1, 255))
    

    texture_copy = texture.copy()
    for new_c, mask in masks.items():
        mask.to_surface(texture_copy, setcolor=new_c, unsetcolor=None)
    
    return texture_copy





@asset_cache
def load_anim_data(path: str) -> dict[str, AnimData]:
    return load_json(f"{ANIMATIONS_DIR}/{path}.animation")


@asset_cache
def load_anim_controller_data(path: str) -> ControllerData:
    return load_json(f"{ANIM_CONTROLLERS_DIR}/{path}.anim_controller")



@asset_cache
def load_sound(name: str) -> GameSound:
    "Loads a sound defined in sound definitions. (OGG file)"

    if name not in __sound_definition:
        raise ValueError(f"Invalid sound name '{name}'")
    
    sound_data = __sound_definition[name]
    
    sounds = []
    for path in sound_data["sounds"]:
        final_path = f"{SOUNDS_DIR}/{path}.{sound_data.get("file_type", "ogg")}"
        sounds.append(pg.Sound(final_path))

    return GameSound(name, sounds)



def load_music(path: str):
    "NOT IMPLEMENTED"
    raise NotImplementedError
    
