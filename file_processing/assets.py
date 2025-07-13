import pygame as p

from . import load_json




TEXTURES_DIR = "assets/textures/"
TEXTURE_MAP_DIR = "assets/texture_maps/"
SOUNDS_DIR = "assets/sounds/"

COLORKEY = (255, 0, 255)


def load_texture(path: str) -> p.Surface:
    "Loads a texture from the textures folder as a pygame.Surface."
    texture = p.image.load(f"{TEXTURES_DIR}{path}").convert()
    texture.set_colorkey(COLORKEY)
    return texture





def load_texture_map(path: str) -> dict[str, p.Surface]:
    mapping_data = load_json(f"{TEXTURE_MAP_DIR}{path}")
    texture = load_texture(mapping_data["texture"])

    texture_map = {}
    for name, area in mapping_data["mappings"].items():
        texture_map[name] = texture.subsurface(area)
    
    return texture_map






def load_sound(path: str) -> p.Sound:
    "Loads a sound from the sounds folder as a pygame.Sound."

    return p.Sound(f"{SOUNDS_DIR}{path}")