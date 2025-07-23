from . import load_json, save_json


HIGHSCORE_DATA_PATH = "user_data/user_data.json"


def load_highscore(path=HIGHSCORE_DATA_PATH) -> int:
    return load_json(path, False)["highscore"]


def save_highscore(value: int, path=HIGHSCORE_DATA_PATH) -> None:
    data = load_json(path, False)
    data["highscore"] = int(value)
    save_json(data, path)