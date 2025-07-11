import json



def load_json(path: str) -> dict:
    with open(path, 'r') as fp:
        return json.load(fp)
    


def save_json(data: dict, path: str) -> None:
    with open(path, 'w') as fp:
        json.dump(data, fp, indent=4)