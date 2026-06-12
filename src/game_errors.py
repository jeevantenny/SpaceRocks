

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
    level_name: str
    missing_property: str
    def __init__(self, level_name: str, missing_property: str):
        self.level_name = level_name
        self.missing_property = missing_property
        super().__init__(f"'{level_name}' is missing required property '{missing_property}'.")