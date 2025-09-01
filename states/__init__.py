import pygame as pg
from typing import Self, Literal, Any, Deque, Generator, Callable
from functools import wraps

import game_errors
import config
from input_device import InputInterpreter
from custom_types import Timer

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
    def wrapper(self: type[State], surface: pg.Surface, lerp_amount=0) -> str | None:
        if self._initialized:
            return draw_func(self, surface, lerp_amount)
        else:
            return None
    
    return wrapper



def stack_method(func: Callable):
    @wraps(func)
    def wrapper(self: type["StateStack"], *args, **kwargs):
        if self.top_state is not None:
            return func(self, *args, **kwargs)
        else:
            return None
        
    return wrapper





class State:
    "A state that a game is in. Use to separate different menus and gameplay."

    enter_duration = 0
    exit_duration = 0
    take_input_on_transition = True
    _initialized = False

    def __init__(self, state_stack: "StateStack | None" = None):
        self.state_stack: StateStack | None = None
        if state_stack is not None:
            state_stack.push(self)

        type(self).draw = draw_wrapper(type(self).draw) # type: ignore


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


    def update_on_enter(self, enter_amount: float) -> None:
        "Called to update while entering state."
        pass


    def update_on_exit(self, exit_amount: float) -> None:
        "Called to update while exiting state."
        self.update_on_enter(1-exit_amount)


    def draw(self, surface: pg.Surface, lerp_amount=0.0) -> str | None:
        "Draws the contents of the game onto the window in every frame."
        pass


    def draw_on_enter(self, enter_amount: float, surface: pg.Surface, lerp_amount=0.0) -> None:
        "Called to draw values while entering state."
        pass


    def draw_on_exit(self, exit_amount: float, surface: pg.Surface, lerp_amount=0.0) -> None:
        "Called to draw while exiting state."
        self.draw_on_enter(1-exit_amount)


    def is_top_state(self) -> bool:
        "Returns weather the current state is at the top of it's stack."
        return self.state_stack.top_state is self


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

        
        self.__current_mode: Literal["show_state", "enter_transition", "exit_transition"] = "show_state"
        self.__transition_timer = Timer(0.0)

    
    
    @property
    def top_state(self) -> State | None:
        if self:
            return self.__container[-1]
        else:
            return None
    

    def push(self, state: State, transition=True) -> None:
        "Adds a new state to the top of the stack."

        self.__transition_timer.end()

        if state in self:
            raise game_errors.DuplicateStateError(state)

        state.state_stack = self
        self.__container.append(state)

        if transition and state.enter_duration > 0.0:
            self.__current_mode = "enter_transition"
            self.__transition_timer = Timer(state.enter_duration).start()


    def pop(self, transition=True, quit_state=True) -> State:
        "Removes and returns the top state."

        self.__transition_timer.end()
        
        state = self.top_state
        if transition and state.exit_duration > 0.0:
            self.__transition_timer = Timer(state.exit_duration, exec_after=lambda: self.pop(False, quit_state)).start()
        
        else:
            if quit_state:
                state.quit()
            self.__container.pop()
        
        return state
        

    def index(self, item: State) -> int:
        "Returns the index of the current state."
        return self.__container.index(item)
    

    @stack_method
    def userinput(self, inputs: InputInterpreter) -> None:
        "Processes userinput for top state."
        if self.__current_mode == "show_state" or self.top_state.take_input_on_transition:
            self.top_state.userinput(inputs) # type: ignore


    @stack_method
    def update(self) -> None:
        "Updates the top state for every tick."
        if not self.__transition_timer.complete:
            self.__transition_timer.update()
            if self.__current_mode == "enter_transition":
                self.top_state.update_on_enter(self.__transition_timer.completion_amount)

            elif self.__current_mode == "exit_transition":
                self.top_state.update_on_exit(self.__transition_timer.completion_amount)
            
            if self.__transition_timer.complete:
                self.__current_mode == "show_state"
            
        else:
            self.top_state.update() # type: ignore


    @stack_method
    def draw(self, surface: pg.Surface, lerp_amount=0.0) -> str | None:
        "Draws the top state for every frame."
        return self.top_state.draw(surface, lerp_amount) # type: ignore
    

    @stack_method
    def quit(self) -> None:
        "Quits all states and pops them from the stack."
        while len(self) > 0:
            self.pop()



    def __eq__(self, value: Self):
        return self.__container == value.__container


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