import pygame as pg

from . import State
from .menus import TitleScreen, PauseMenu
from .play import Play

from file_processing import data




class Initializer(State):
    "This state will not be added to the state_stack. Instead it adds the relevant states needed when the game is opened."

    def __init__(self, state_stack = None):
        save_data = data.load_progress()

        if save_data is None:
            Play("level_1", state_stack)
            TitleScreen(state_stack)
        
        else:
            Play.init_from_save(save_data, state_stack)
            PauseMenu(state_stack)