"Contains functions that load data required by the game."

import os
import pickle
from functools import lru_cache

import debug

from src.custom_types import LevelData, SaveData
from src.game_errors import SaveFileError, LevelDataError

from . import load_json, save_json, get_resource_path


data_cache = lru_cache(1)

HIGHSCORE_DATA_PATH = "user_data/highscore"
SETTINGS_DATA_PATH = "user_data/settings"
LEVELS_DIR = "data/levels"

SAVE_DATA_PATH = "user_data/progress.bin"

__demo_highscore = 0


if not (os.path.exists("user_data") or debug.Cheats.demo_mode):
    os.makedirs("user_data")




def load_level(name: str) -> LevelData:
    """
    Loads a level data json file as a LevelData object.

    Raises ValueError if name is invalid.  
    Raises LevelDataError if level data is missing required properties.
    """

    try:
        level_data = load_json(f"{LEVELS_DIR}/{name}")
    except FileNotFoundError:
        raise ValueError(f"Invalid level name '{name}'")
    try:

        asteroid_weights = ([], [])
        for a_name, a_weight in level_data["spawn_asteroids"].items():
            asteroid_weights[0].append(a_name)
            asteroid_weights[1].append(a_weight)

        powerups_weights = ([], [])
        for p_name, p_weight in level_data.get("spawn_powerups", {}).items():
            powerups_weights[0].append(p_name)
            powerups_weights[1].append(p_weight)

        level_data_obj = LevelData(
            level_name=             name,
            base_color=             level_data.get("base_color", "#000000"),
            parl_a=                 level_data.get("parl_a", "backgrounds/space_background"),
            parl_b=                 level_data.get("parl_b", "backgrounds/space_background_big"),
            background_palette=     level_data["background_palette"],
            background_tint=        level_data.get("background_tint", "#4E6382"),

            asteroid_density=       tuple(level_data["asteroid_density"]),
            asteroid_speed=         tuple(level_data["asteroid_speed"]),
            asteroid_frequency=     level_data.get("asteroid_frequency", 0.2),
            asteroid_spawn_weights= asteroid_weights,

            powerup_frequency=      level_data.get("powerup_frequency", 0.0),
            powerup_spawn_weights=  powerups_weights,

            score_range=            tuple(level_data["score_range"]),
            next_level=             level_data["next_level"]
        )
    except KeyError as e:
        raise LevelDataError(name, e.args[0])

    return level_data_obj










def load_highscore(path=HIGHSCORE_DATA_PATH) -> int:
    "Loads the last saved highscore achieved by the player"

    # Loads temporary highscore in demo mode
    if debug.Cheats.demo_mode:
        global __demo_highscore
        return __demo_highscore
    
    try:
        return load_json(path, False)["highscore"]
    except FileNotFoundError:
        return 0


def save_highscore(value: int, path=HIGHSCORE_DATA_PATH) -> None:
    "Saved an integer value as the highscore."

    # Highscore is saved temporarily in variable
    if debug.Cheats.demo_mode:
        global __demo_highscore
        __demo_highscore = value
        return

    try:
        data = load_json(path, False)
    except FileNotFoundError:
        data = {}
    
    data["highscore"] = int(value)
    save_json(data, path)



def load_progress() -> SaveData | None:
    "Loads the player's from save data as a SaveData object. Returns None if there us no progress saved."

    #Does not load progress in demo mode
    if debug.Cheats.demo_mode:
        return None

    try:
        with open(SAVE_DATA_PATH, "rb") as fp:
            save_data = pickle.load(fp)
            if not isinstance(save_data, SaveData):
                raise SaveFileError
            return save_data
    
    except (FileNotFoundError, EOFError):
        return None
    
    except (pickle.UnpicklingError, SaveFileError):
        raise SaveFileError("Save data got corrupted")
    


def save_progress(save_data: SaveData) -> None:
    "Saved the player's current progress to be resumed later."

    # Does not save progress in demo mode
    if not debug.Cheats.demo_mode:
        with open(SAVE_DATA_PATH, "wb") as fp:
            pickle.dump(save_data, fp)



def delete_progress() -> None:
    "Deleted save data for player's progress."

    # Does not delete progress in demo mode.
    if not debug.Cheats.demo_mode:
        with open(SAVE_DATA_PATH, "wb") as _: pass



@data_cache
def load_settings(path=SETTINGS_DATA_PATH) -> dict:
    "Loads user settings as a dictionary"
    return load_json(path)


def update_settings(settings_data: dict, path=SETTINGS_DATA_PATH) -> None:
    "Updates user settings. Only settings that change need to be present in `settings_data`."
    new_settings = load_settings()
    new_settings.update(settings_data)
    save_json(new_settings, path)
    load_settings.cache_clear()





def delete_user_data() -> None:
    "Deletes all user data."

    if debug.Cheats.demo_mode:
        raise RuntimeError("Cannot delete user data in demo mode")
    
    delete_progress()
    save_highscore(0)