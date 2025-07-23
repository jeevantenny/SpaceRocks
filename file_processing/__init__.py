import sys, os
import json


def get_resource_path(path: str) -> str:
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, path)
    else:
        return path
    


def load_json(path: str, use_mei_path=True) -> dict:
    if use_mei_path:
        path = get_resource_path(path)
    with open(path, 'r') as fp:
        return json.load(fp)
    


def save_json(data: dict, path: str) -> None:
    with open(path, 'w') as fp:
        json.dump(data, fp, indent=4)