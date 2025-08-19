import pygame as p

from math_functions import clamp

from file_processing import assets



def play_sound(name: str, volume=1.0) -> p.Channel:
    sound = assets.load_sound(name)
    return sound.play(clamp(volume, 0, 1))