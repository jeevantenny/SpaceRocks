import debug

from src.game_errors import SaveFileError
from src.file_processing import data

from . import State, StateStack
from .menus import TitleScreen, PauseMenu
from .play import Play
from .visuals import BackgroundTint
from .info_states import DemoState

from .test_states import *




class Initializer:
    "This state will not be added to the state_stack. Instead it adds the relevant states needed when the game is opened."

    def __init__(self, state_stack: StateStack):
        if debug.Cheats.test_state:
            TestElementList().add_to_stack(state_stack)
            return

        try:
            save_data = data.load_progress()
        except SaveFileError as e:
            save_data = None
            print(*e.args)

        if save_data is None:
            Play("level_1").add_to_stack(state_stack)
            TitleScreen().add_to_stack(state_stack)
        
        else:
            Play.init_from_save(save_data).add_to_stack(state_stack)
            BackgroundTint("#666666").add_to_stack(state_stack)
            PauseMenu().add_to_stack(state_stack)
        
        if debug.Cheats.demo_mode:
            DemoState().add_to_stack(state_stack)