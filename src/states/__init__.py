"""
States define what should be run on each input, process, draw cycle. They are
different sections in the game that determine what screen or menu the game
should currently show.
"""

import pygame as pg
from typing import Self, Any, Deque, Generator

from src import game_errors
from src.input_device import InputInterpreter
from src.audio.soundfx import HasSoundQueue
from src.misc import find_subclass_by_name



__all__ = [
    "State",
    "StateStack",
    "menus",
    "play"
]









class State(HasSoundQueue):
    """
    A state that a game is in. Use to separate different menus and gameplay.
    """

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


    def draw(self, surface: pg.Surface, lerp_amount=0.0) -> None:
        "Draws the contents of the game onto the window in every frame."
        pass

    
    def debug_info(self) -> str | None:
        "Returns information to be displayed at the top of the window."
        pass


    def is_top_state(self) -> bool:
        "Returns weather the current state is at the top of it's stack."
        return self.state_stack.top() is self


    def quit(self) -> None:
        "Saves any data that needs to be saved."
        return None


    def __repr__(self) -> str:
        return f"<{self.name} State>"
    






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








class StateStack(HasSoundQueue):
    """
    Holds all the states that are currently loaded in. States can be layered on top of
    one another to show different overlapping menus.
    """
    
    def __init__(self, states: list[State] | None = None):
        super().__init__()
        self.__container: Deque[State] = Deque()
        
        if states is not None:
            for state in states:
                self.push(state)


    def top(self) -> State | None:
        if self:
            return self.__container[-1]
        else:
            return None
    

    def push(self, state: State) -> None:
        "Add a new state to the top of the stack."
        if not isinstance(state, State):
            raise TypeError("State must be of type 'State'")
        elif state in self:
            raise game_errors.DuplicateStateError(self)
        state.state_stack = self
        self.__container.append(state)


    def pop(self, quit_state=True) -> State:
        "Remove and return the top state."
        
        state = self.top()
        if state is None:
            raise IndexError("Pop from empty stack")
        
        if quit_state:
            state.quit()
        self.__container.pop()
        
        return state
        

    def index(self, item: State) -> int:
        "Return the index of the current state."
        return self.__container.index(item)
    


    def find_by_type[T](self, state_type: type[T]) -> T | None:
        """Find the first state in the stack that is of the specified type"""
        for state in self:
            if isinstance(state, state_type):
                return state
        else:
            return None
    

    def find_by_name(self, name: str) -> State | None:
        """Find the first state in the stack with the specified name (name of State type)"""
        state_type = find_subclass_by_name(State, name)
        return state_type and self.find_by_type(state_type)

    


    def userinput(self, inputs: InputInterpreter) -> None:
        "Processes userinput for top state."
        if self.top() is not None:
            self.top().userinput(inputs)



    def update(self) -> None:
        "Updates the top state for every tick."
        if self.top() is not None:
            self.top().update()
            self._join_sound_queue(self.top().clear_sound_queue())


    def draw(self, surface: pg.Surface, lerp_amount=0.0) -> None:
        "Draws the top state for every frame."
        if self.top() is not None:
            self.top().draw(surface, lerp_amount)


    def debug_info(self) -> str | None:
        if self.top() is not None:
            return self.top().debug_info()
    

    def quit(self) -> None:
        "Quits all states and pops them from the stack."
        while len(self) > 0:
            self.pop()
    
    def force_quit(self) -> None:
        "Removes all states without saving any data in them."
        self.__container.clear()



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