import debug

from src.custom_types import SaveData
from src.game_errors import SaveFileError
from src.file_processing import data
from src.misc import get_start_level, find_subclass_by_name

from . import State, StateStack, menus, info_states, boss_level, play_level

from .test_states import *




class Initializer:
    "This state will not be added to the state_stack. Instead it adds the relevant states needed when the game is opened."

    def __init__(self, state_stack: StateStack):
        state_stack.quit()
        if debug.Cheats.test_state is not None:
            find_subclass_by_name(State, debug.Cheats.test_state)(*debug.Cheats.test_state_args).add_to_stack(state_stack)
            return

        try:
            save_data = data.load_progress()
            save_error = False
        except SaveFileError as e:
            save_data = None
            save_error = True

        if save_data is None:
            self.main_title_screen(state_stack)
            if save_error:
                info_states.InfoState(
                    "SAVE FILE CORRUPTED",
                    "The previous save file got corrupted",
                    "Delete Save File<select>",
                    text_color_a="#aa0055"
                    ).add_to_stack(state_stack)
        
        else:
            self.continue_from_save(state_stack, save_data)

        if debug.Cheats.demo_mode:
            info_states.InfoState(
                "DEMO MODE",
                "User data is not saved or loaded from previous save"
                ).add_to_stack(state_stack)
    

    @classmethod
    def main_title_screen(self, state_stack: StateStack) -> None:
        play_level.PlayLevel(get_start_level()).add_to_stack(state_stack)
        menus.TitleScreen().add_to_stack(state_stack)

    
    @classmethod
    def continue_from_save(self, state_stack: StateStack, save_data: SaveData) -> None:
        play_level.PlayLevel.init_from_save(save_data).add_to_stack(state_stack)
        menus.PauseMenu().add_to_stack(state_stack)