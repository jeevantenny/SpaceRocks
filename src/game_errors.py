

class InitializationError(Exception):
    def __init__(self, *args):
        super().__init__(*args)


class DuplicateStateError(Exception):
    def __init__(self, state):
        super().__init__(f"The current instance of the '{type(state).__name__}' state is already in state stack")


class SaveFileError(Exception):
    "Save file got corrupted."
    def __init__(self, *args):
        super().__init__(*args)


class LevelDataError(Exception):
    "Level data json file is missing required property."
    def __init__(self, level_name: str, property_name: str):
        super().__init__(f"'{level_name}' is missing required property '{property_name}'.")