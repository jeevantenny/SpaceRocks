import pygame as pg

from . import State, StateStack
from .menus import TitleScreen, PauseMenu
from .play import Play

from file_processing import data




class Initializer:
    "This state will not be added to the state_stack. Instead it adds the relevant states needed when the game is opened."

    def __init__(self, state_stack: StateStack):
        save_data = data.load_progress()

        if save_data is None:
            Play("level_2").add_to_stack(state_stack)
            TitleScreen().add_to_stack(state_stack)
        
        else:
            Play.init_from_save(save_data).add_to_stack(state_stack)
            PauseMenu().add_to_stack(state_stack)