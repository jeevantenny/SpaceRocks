


class MissingComponentError(Exception):
    def __init__(self, missing_component, dependant):
        super().__init__(f"Game object is missing components {[x.__name__ for x in missing_component]}, required by {dependant.__name__}")