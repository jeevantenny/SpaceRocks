import os
import pickle

from custom_types import LevelData, SaveData

from . import load_json, save_json, get_resource_path


HIGHSCORE_DATA_PATH = "user_data/highscore"
LEVELS_DIR = "data/levels"

SAVE_DATA_PATH = "user_data/progress.bin"


if not os.path.exists("user_data"):
    os.makedirs("user_data")




def load_level(name: str) -> LevelData:
    level_data = load_json(f"{LEVELS_DIR}/{name}")


    return level_data


def load_highscore(path=HIGHSCORE_DATA_PATH) -> int:
    try:
        return load_json(path, False)["highscore"]
    except FileNotFoundError:
        return 0


def save_highscore(value: int, path=HIGHSCORE_DATA_PATH) -> None:
    try:
        data = load_json(path, False)
    except FileNotFoundError:
        data = {}
    
    data["highscore"] = int(value)
    save_json(data, path)



def load_progress() -> SaveData | None:
    try:
        with open(SAVE_DATA_PATH, "rb") as fp:
            save_data = pickle.load(fp)
            return save_data
    
    except (FileNotFoundError, EOFError):
        return None
    
    except pickle.UnpicklingError:
        raise ValueError("Progress got corrupted")
    


def save_progress(save_data: SaveData) -> None:
    with open(SAVE_DATA_PATH, "wb") as fp:
        pickle.dump(save_data, fp)



def delete_progress() -> None:
    with open(SAVE_DATA_PATH, "wb") as fp: pass