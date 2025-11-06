"Contains functions that load data required by the game."

import os
import pickle

import debug

from src.custom_types import LevelData, SaveData
from src.game_errors import SaveFileError, LevelDataError

from . import load_json, save_json, get_resource_path


HIGHSCORE_DATA_PATH = "user_data/highscore"
LEVELS_DIR = "data/levels"

SAVE_DATA_PATH = "user_data/progress.bin"


if not os.path.exists("user_data"):
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
        asteroid_data = level_data["asteroid_data"]
        spawn_weights = ([], [])

        try:
            for a_name, data in asteroid_data.items():
                data["texture_map"]
                data["hitbox_size"]
                data["health"]
                data["points"]
                data["size_value"]
                spawn_weights[0].append(a_name)
                spawn_weights[1].append(data.get("spawn_weight", 1))

        except KeyError as e:
            raise KeyError(f"asteroid_data.{a_name}.{e.args[0]}")

        level_data_obj = LevelData(
            name,
            level_data.get("base_color", "#000000"),
            level_data.get("parl_a", "backgrounds/space_background"),
            level_data.get("parl_b", "backgrounds/space_background_big"),
            level_data["background_palette"],
            level_data.get("asteroid_palette", None),
            level_data.get("background_tint", "#335588"),

            tuple(level_data["asteroid_density"]),
            tuple(level_data["asteroid_speed"]),
            level_data.get("asteroid_frequency", 0.2),
            spawn_weights,

            asteroid_data,

            tuple(level_data["score_range"]),
            level_data["next_level"]
        )
    except KeyError as e:
        raise LevelDataError(name, e.args[0])

    return level_data_obj











def load_highscore(path=HIGHSCORE_DATA_PATH) -> int:
    "Loads the last saved highscore achieved by the player"
    
    try:
        return load_json(path, False)["highscore"]
    except FileNotFoundError:
        return 0


def save_highscore(value: int, path=HIGHSCORE_DATA_PATH) -> None:
    "Saved an integer value as the highscore."

    try:
        data = load_json(path, False)
    except FileNotFoundError:
        data = {}
    
    data["highscore"] = int(value)
    save_json(data, path)



def load_progress() -> SaveData | None:
    "Loads the player's from save data as a SaveData object. Returns None if there us no progress saved."

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

    with open(SAVE_DATA_PATH, "wb") as fp:
        pickle.dump(save_data, fp)



def delete_progress() -> None:
    "Deleted save data for player's progress."
    with open(SAVE_DATA_PATH, "wb") as _: pass