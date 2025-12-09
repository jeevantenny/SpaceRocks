import debug

from src.game_errors import SaveFileError
from src.file_processing import data
from src.misc import get_start_level, find_subclass_by_name

from . import State, StateStack, play, menus, info_states, boss_level

from .test_states import *




class Initializer:
    "This state will not be added to the state_stack. Instead it adds the relevant states needed when the game is opened."

    def __init__(self, state_stack: StateStack):
        if debug.Cheats.test_state is not None:
            find_subclass_by_name(State, debug.Cheats.test_state)().add_to_stack(state_stack)
            return

        try:
            save_data = data.load_progress()
        except SaveFileError as e:
            save_data = None
            print(*e.args)


        if save_data is None:
            play.Play(get_start_level()).add_to_stack(state_stack)
            menus.TitleScreen().add_to_stack(state_stack)
        
        else:
            play.Play.init_from_save(save_data).add_to_stack(state_stack)
            menus.BackgroundTint("#666666").add_to_stack(state_stack)
            menus.PauseMenu().add_to_stack(state_stack)
        
        if debug.Cheats.demo_mode:
            info_states.DemoState().add_to_stack(state_stack)