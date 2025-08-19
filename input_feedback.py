import pygame as p

from userinput import Controller



_controller_instance: Controller | None = None

def controller_rumble(pattern_name: str, intensity=0.5, wait_until_clear=False) -> None:
    if _controller_instance is not None:
        _controller_instance.rumble(pattern_name, intensity, wait_until_clear)