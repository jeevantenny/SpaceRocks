"Contains functions that load data required by the game."

import os
import pickle
from functools import lru_cache
from json import JSONDecodeError

import debug

from src.custom_types import UserSettings, LevelData, SaveData
from src.game_errors import SaveFileError, LevelDataError

from . import load_json, save_json


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

        asteroids: dict = level_data.get("spawn_asteroids", {})
        asteroid_weights = (list(asteroids.keys()), list(asteroids.values()))

        enemies: dict = level_data.get("spawn_enemies", {})
        enemy_weights = (list(enemies.keys()), list(enemies.values()))

        powerups: dict = level_data.get("spawn_powerups", {})
        powerup_weights = (list(powerups.keys()), list(powerups.values()))

        level_data_obj = LevelData(
            level_name=             name,
            base_color=             level_data.get("base_color", "#000000"),
            parl_a=                 level_data.get("parl_a"),
            parl_b=                 level_data.get("parl_b"),
            background_palette=     level_data.get("background_palette"),
            background_tint=        level_data.get("background_tint", "#4E6382"),

            asteroid_density=       tuple(level_data["asteroid_density"]),
            asteroid_speed=         tuple(level_data["asteroid_speed"]),
            asteroid_frequency=     level_data.get("asteroid_frequency", 0.0),
            asteroid_spawn_weights= asteroid_weights,

            enemy_frequency=        level_data.get("enemy_frequency", 0.0),
            enemy_count=            level_data.get("enemy_count", 0),
            enemy_spawn_weights=    enemy_weights,

            powerup_frequency=      level_data.get("powerup_frequency", 0.0),
            powerup_spawn_weights=  powerup_weights,

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
        return load_json(path)["highscore"]
    except (FileNotFoundError, JSONDecodeError):
        return 0


def save_highscore(value: int, path=HIGHSCORE_DATA_PATH) -> None:
    "Saved an integer value as the highscore."

    # Highscore is saved temporarily in variable
    if debug.Cheats.demo_mode:
        global __demo_highscore
        __demo_highscore = value
        return
    
    save_json({"highscore": int(value)}, path)



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



@lru_cache(1)
def load_settings() -> UserSettings:
    "Loads user settings as a dictionary"
    try:
        settings = load_json(SETTINGS_DATA_PATH)
    except (FileNotFoundError, JSONDecodeError):
        settings = {}
    else:
        settings = {
            name: value
            for name, value in settings.items()
            if name in UserSettings._fields
        }

    return UserSettings(**settings)


def update_settings(**settings_data) -> None:
    "Updates user settings. Only settings that change need to be present in `settings_data`."
    full_settings = load_settings()._asdict()
    for setting in settings_data.keys():
        if setting not in full_settings:
            raise ValueError(f"Invalid setting name '{setting}'")
    
    full_settings.update(settings_data)
    save_json(full_settings, SETTINGS_DATA_PATH)
    load_settings.cache_clear()



def reset_settings() -> None:
    "Resets all settings to default values."
    save_json({}, SETTINGS_DATA_PATH)
    load_settings.cache_clear()





def delete_user_data() -> None:
    "Deletes all user data."

    if debug.Cheats.demo_mode:
        raise RuntimeError("Cannot delete user data in demo mode")
    
    delete_progress()
    save_highscore(0)
    reset_settings()