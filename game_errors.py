


class MissingComponentError(Exception):
    def __init__(self, missing_component, dependant):
        super().__init__(f"Game object is missing components {[x.__name__ for x in missing_component]}, required by {dependant.__name__}")


class InitializationError(Exception):
    def __init__(self, _class: type[object]):
        super().__init__(f"Class '{_class.__name__}' has not been initialized.")


class DuplicateStateError(Exception):
    def __init__(self, state):
        super().__init__(f"The current instance of the '{type(state).__name__}' state is already in state stack.")