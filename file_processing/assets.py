import pygame as pg
from functools import lru_cache

from . import get_resource_path, load_json

from custom_types import GameSound


TEXTURES_DIR = "assets/textures"
TEXTURE_MAPS_DIR = "assets/texture_maps"

ANIMATIONS_DIR = "assets/animations"
ANIM_CONTROLLERS_DIR = "assets/anim_controllers"

SOUNDS_DIR = "assets/sounds"

COLORKEY = (255, 0, 255)


__sound_definition = load_json("assets/sounds")


@lru_cache(32)
def load_texture(path: str) -> pg.Surface:
    "Loads a texture from the textures folder as a pygame.Surface. (PNG file)"
    texture_path = get_resource_path(f"{TEXTURES_DIR}/{path}.png")
    texture = pg.image.load(texture_path).convert()
    texture.set_colorkey(COLORKEY)
    return texture






def colorkey_surface(size: pg.typing.Point, flags=0, depth=0, masks: pg.typing.ColorLike | None = None) -> pg.Surface:
    surface = pg.Surface(size)
    surface.set_colorkey(COLORKEY)
    surface.fill(COLORKEY)
    return surface



@lru_cache(32)
def load_texture_map(path: str) -> dict[str, pg.Surface]:
    mapping_data = load_json(f"{TEXTURE_MAPS_DIR}/{path}.texture_map")
    main_texture = load_texture(mapping_data["texture"])

    texture_map = {}
    for name, area in mapping_data["mappings"].items():
        texture_map[name] = main_texture.subsurface(area)
    
    return texture_map






@lru_cache(32)
def load_animations(path: str):
    return load_json(f"{ANIMATIONS_DIR}/{path}")


@lru_cache(32)
def load_anim_controllers(path: str):
    return load_json(f"{ANIM_CONTROLLERS_DIR}/{path}")



@lru_cache(32)
def load_sound(name: str) -> GameSound:
    "Loads a sound defined in sound definitions. (OGG file)"

    if name not in __sound_definition:
        raise ValueError(f"Invalid sound name '{name}'")
    
    sound_data = __sound_definition[name]
    
    sounds = [pg.Sound(f"{SOUNDS_DIR}/{path}.{sound_data.get("file_type", "ogg")}") for path in sound_data["sounds"]]

    return GameSound(name, sounds)



def load_music(path: str):
    pg.mixer_music.load(f"{SOUNDS_DIR}/{path}.ogg")
    
