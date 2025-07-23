import pygame as p
from functools import lru_cache

from . import get_resource_path, load_json




TEXTURES_DIR = "assets/textures"
TEXTURE_MAPS_DIR = "assets/texture_maps"

ANIMATIONS_DIR = "assets/animations"
ANIM_CONTROLLERS_DIR = "assets/anim_controllers"
SOUNDS_DIR = "assets/sounds"

COLORKEY = (255, 0, 255)


@lru_cache(32)
def load_texture(path: str) -> p.Surface:
    "Loads a texture from the textures folder as a pygame.Surface."
    texture_path = get_resource_path(f"{TEXTURES_DIR}/{path}")
    texture = p.image.load(texture_path).convert()
    texture.set_colorkey(COLORKEY)
    return texture




@lru_cache(32)
def load_texture_map(path: str) -> dict[str, p.Surface]:
    mapping_data = load_json(f"{TEXTURE_MAPS_DIR}/{path}")
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




def load_sound(path: str) -> p.Sound:
    "Loads a sound from the sounds folder as a pygame.Sound."

    sound_path = get_resource_path(f"{SOUNDS_DIR}/{path}")
    return p.Sound(sound_path)