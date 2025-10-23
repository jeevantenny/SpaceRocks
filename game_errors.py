

class InitializationError(Exception):
    def __init__(self, _class: type[object]):
        super().__init__(f"Class '{_class.__name__}' has not been initialized.")


class DuplicateStateError(Exception):
    def __init__(self, state):
        super().__init__(f"The current instance of the '{type(state).__name__}' state is already in state stack.")


class SaveFileError(Exception):
    def __init__(self, *args):
        super().__init__(*args)