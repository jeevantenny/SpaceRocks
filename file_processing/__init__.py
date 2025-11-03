"Used to load all files for the game."

import sys, os
import json


def get_resource_path(path: str) -> str:
    "Gets the correct path to files when compiled to executable."
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, path)
    else:
        return path
    


def load_json(path: str, use_mei_path=True) -> dict:
    "Loads a json file as a dict (don't include .json in path)"
    path = f"{path}.json"
    if use_mei_path:
        path = get_resource_path(path)
    with open(path, 'r') as fp:
        return json.load(fp)
    


def save_json(data: dict, path: str) -> None:
    "Saves a json file from a dict (don't include .json in path)"
    with open(f"{path}.json", 'w') as fp:
        json.dump(data, fp, indent=4)