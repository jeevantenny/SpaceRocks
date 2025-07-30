import pygame as p
from typing import Any, Deque, Generator, Callable
from functools import wraps

import game_errors
import config
from userinput import InputInterpreter

from file_processing import assets



__all__ = [
    "draw_wrapper",
    "State",
    "StateStack",
    "menus",
    "play"
]



def draw_wrapper(draw_func: Callable):
    """
    Added to the draw method of a state that checks if the state has been initialized before
    running the method.
    """
    @wraps(draw_func)
    def wrapper(self: type[State], surface: p.Surface, lerp_amount=0) -> str | None:
        if self._initialized:
            return draw_func(self, surface, lerp_amount)
        else:
            return None
    
    return wrapper






class State:
    "A state that a game is in. Use to separate different menus and gameplay."

    _initialized = False

    def __init__(self, state_stack: "StateStack | None" = None):
        self.state_stack: StateStack | None = None
        if state_stack is not None:
            state_stack.push(self)

        self.__pixel_art_surface = p.Surface(config.PIXEL_WINDOW_SIZE)
        self.__pixel_art_surface.set_colorkey(assets.COLORKEY)

        type(self).draw = draw_wrapper(type(self).draw)


    @property
    def prev_state(self) -> "State | None":
        if self.state_stack is not None and self in self.state_stack and len(self.state_stack) > 1:
            return self.state_stack[self.state_stack.index(self)-1]
        else:
            return None


    def userinput(self, inputs: InputInterpreter) -> None:
        "Takes the user's inputs as arguments and processes them,"
        pass


    def update(self) -> None:
        "Updates the game logic for each tick."
        pass


    def draw(self, surface: p.Surface, lerp_amount=0.0) -> None:
        "Draws the contents of the game onto the window in every frame."
        self.__pixel_art_surface.fill(assets.COLORKEY)
        output = self._draw_pixel_art(self.__pixel_art_surface, lerp_amount)
        surface.blit(p.transform.scale_by(self.__pixel_art_surface, config.PIXEL_SCALE))
        return output


    def _draw_pixel_art(self, surface: p.Surface, lerp_amount=0.0) -> None:
        "A modified draw method that reduces the window resolution when drawing. Contents drawn over main draw method."
        pass


    def quit(self) -> None:
        "Saves any data that needs to be saved."
        pass


    def __repr__(self) -> str:
        return f"<{type(self).__name__} State(state_stack={self.state_stack is not None})>"








class StateStack:
    def __init__(self, states: list[State] | None = None):
        self.__container: Deque[State]
        if states is not None:
            self.__container = Deque(states)
        else:
            self.__container = Deque()

    
    
    @property
    def top_state(self) -> State | None:
        if self:
            return self.__container[-1]
        else:
            return None
    

    def push(self, state: State) -> None:
        "Adds a new state to the top of the stack."

        if state in self:
            raise game_errors.DuplicateStateError(state)

        state.state_stack = self
        self.__container.append(state)


    def pop(self, quit_state=True) -> State:
        "Removes and returns the top state."
        state = self.__container.pop()
        if quit_state:
            state.quit()
        
        return state
    

    def index(self, item: State) -> int:
        "Returns the index of the current state."
        return self.__container.index(item)
    

    def userinput(self, inputs: InputInterpreter) -> None:
        "Processes userinput for top state."
        self.top_state.userinput(inputs)


    
    def update(self) -> None:
        "Updates the top state for every tick."
        self.top_state.update()



    def draw(self, surface: p.Surface, lerp_amount=0.0) -> str | None:
        "Draws the top state for every frame."
        return self.top_state.draw(surface, lerp_amount)
    


    def quit(self) -> None:
        "Quits all states and pops them from the stack."
        while len(self) > 0:
            self.pop()



    def __len__(self) -> int:
        return len(self.__container)
    

    def __iter__(self) -> Generator[State, Any, None]:
        for state in self.__container:
            yield state


    def __getitem__(self, index: int) -> State:
        return self.__container[index]


    def __repr__(self) -> str:
        name_list = [f"<{type(state).__name__} State>" for state in self.__container]

        return f"<{type(self).__name__}({name_list})>"