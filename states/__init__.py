"""
States define what should be run on each input, process, draw cycle. They are
different sections in the game that determine what screen or menu the game
should currently show.
"""

import pygame as pg
from typing import Self, Literal, Any, Deque, Generator, Callable
from functools import wraps

import game_errors
from input_device import InputInterpreter
from custom_types import Timer

from audio import soundfx



__all__ = [
    "State",
    "StateStack",
    "menus",
    "play"
]









class State(soundfx.HasSoundQueue):
    "A state that a game is in. Use to separate different menus and gameplay."

    enter_duration = 0
    exit_duration = 0
    take_input_on_transition = True


    def __init__(self):
        super().__init__()
        self.state_stack: StateStack | None = None

    @property
    def prev_state(self) -> "State | None":
        if self.state_stack and self in self.state_stack:
            index = self.state_stack.index(self)
            if index > 0:
                return self.state_stack[index-1]
        
        return None
        

    @property
    def name(self) -> str:
        return type(self).__name__
    

    def add_to_stack(self, state_stack: "StateStack") -> None:
        if not isinstance(state_stack, StateStack):
            raise TypeError(f"state_stack must be of type '{StateStack.__name__}")
        
        state_stack.push(self)


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


    def draw(self, surface: pg.Surface, lerp_amount=0.0) -> None:
        "Draws the contents of the game onto the window in every frame."
        pass


    def draw_on_enter(self, enter_amount: float, surface: pg.Surface, lerp_amount=0.0) -> None:
        "Called to draw values while entering state."
        pass


    def draw_on_exit(self, exit_amount: float, surface: pg.Surface, lerp_amount=0.0) -> None:
        "Called to draw while exiting state."
        self.draw_on_enter(1-exit_amount)

    
    def debug_info(self) -> str | None:
        "Returns information to be displayed at the top of the window."
        pass


    def is_top_state(self) -> bool:
        "Returns weather the current state is at the top of it's stack."
        return self.state_stack.top_state is self


    def quit(self) -> None:
        "Saves any data that needs to be saved."
        return None


    def __repr__(self) -> str:
        return f"<{type(self).__name__} State(in_state_stack={self.state_stack is not None})>"
    






class PassThroughState(State):
    
    def userinput(self, inputs):
        self.prev_state.userinput(inputs)
    
    def update(self):
        self.prev_state.update()
        self._join_sound_queue(self.prev_state.clear_sound_queue())
    
    def draw(self, surface, lerp_amount=0):
        self.prev_state.draw(surface, lerp_amount)
    
    def debug_info(self):
        return self.prev_state.debug_info()








class StateStack(soundfx.HasSoundQueue):
    """
    Holds all the states that are currently loaded in. States can be layered on top of
    one another to show different overlapping menus.
    """
    
    def __init__(self, states: list[State] | None = None):
        super().__init__()
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
    


    def userinput(self, inputs: InputInterpreter) -> None:
        "Processes userinput for top state."
        if self.top_state is not None and (self.__current_mode == "show_state" or self.top_state.take_input_on_transition):
            self.top_state.userinput(inputs) # type: ignore



    def update(self) -> None:
        "Updates the top state for every tick."

        if self.top_state is None:
            return
        
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
        
        self._join_sound_queue(self.top_state.clear_sound_queue())


    def draw(self, surface: pg.Surface, lerp_amount=0.0) -> None:
        "Draws the top state for every frame."
        if self.top_state is not None:
            self.top_state.draw(surface, lerp_amount)


    def debug_info(self) -> str | None:
        if self.top_state is not None:
            return self.top_state.debug_info()
    

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