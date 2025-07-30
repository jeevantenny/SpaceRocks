import os

from . import load_json, save_json, get_resource_path


HIGHSCORE_DATA_PATH = "user_data/user_data"


def load_highscore(path=HIGHSCORE_DATA_PATH) -> int:
    # return 0
    try:
        return load_json(path, False)["highscore"]
    except FileNotFoundError:
        return load_json(path)["highscore"]


def save_highscore(value: int, path=HIGHSCORE_DATA_PATH) -> None:
    # return # TODO Re-enable this
    if not os.path.exists("user_data"):
        os.makedirs("user_data")
        data = {}
    else:
        data = load_json(path, False)

    data["highscore"] = int(value)
    save_json(data, path)