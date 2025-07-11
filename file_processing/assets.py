import pygame as p




TEXTURES_DIR = "assets/textures/"
SOUNDS_DIR = "assets/sounds/"




def load_texture(path: str) -> p.Surface:
    "Loads a texture from the textures folder as a pygame.Surface."

    return p.image.load(f"{TEXTURES_DIR}{path}").convert()





def load_sound(path: str) -> p.Sound:
    "Loads a sound from the sounds folder as a pygame.Sound."

    return p.Sound(f"{SOUNDS_DIR}{path}")