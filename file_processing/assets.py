import pygame as pg
from functools import lru_cache

from . import get_resource_path, load_json

from custom_types import GameSound


asset_cache = lru_cache(32)


TEXTURES_DIR = "assets/textures"
TEXTURE_MAPS_DIR = "assets/texture_maps"

ANIMATIONS_DIR = "assets/animations"
ANIM_CONTROLLERS_DIR = "assets/anim_controllers"

SOUNDS_DIR = "assets/sounds"

COLORKEY = (255, 0, 255)


__sound_definition = load_json("assets/sounds")


@asset_cache
def load_texture(path: str, file_type="png") -> pg.Surface:
    "Loads a texture from the textures folder as a pygame.Surface"
    texture_path = get_resource_path(f"{TEXTURES_DIR}/{path}.{file_type}")
    texture = pg.image.load(texture_path).convert()
    texture.set_colorkey(COLORKEY)
    return texture






def colorkey_surface(size: pg.typing.Point) -> pg.Surface:
    surface = pg.Surface(size)
    surface.set_colorkey(COLORKEY)
    surface.fill(COLORKEY)
    return surface



@asset_cache
def load_texture_map(path: str) -> dict[str, pg.Surface]:
    mapping_data = load_json(f"{TEXTURE_MAPS_DIR}/{path}.texture_map")
    main_texture = load_texture(mapping_data["texture"])

    texture_map = {}
    for name, area in mapping_data["mappings"].items():
        texture_map[name] = main_texture.subsurface(area)
    
    return texture_map






@asset_cache
def load_anim_data(path: str):
    return load_json(f"{ANIMATIONS_DIR}/{path}.animation")


@asset_cache
def load_anim_controller_data(path: str):
    return load_json(f"{ANIM_CONTROLLERS_DIR}/{path}.anim_controller")



@asset_cache
def load_sound(name: str) -> GameSound:
    "Loads a sound defined in sound definitions. (OGG file)"

    if name not in __sound_definition:
        raise ValueError(f"Invalid sound name '{name}'")
    
    sound_data = __sound_definition[name]
    
    sounds = [pg.Sound(f"{SOUNDS_DIR}/{path}.{sound_data.get("file_type", "ogg")}") for path in sound_data["sounds"]]

    return GameSound(name, sounds)



def load_music(path: str):
    pg.mixer_music.load(f"{SOUNDS_DIR}/{path}.ogg")
    
