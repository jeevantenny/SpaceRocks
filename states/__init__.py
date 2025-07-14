import pygame as p
from typing import Deque

from userinput import InputInterpreter






class State:
    "A state that a game is in. Use to separate different menus and gameplay."
    def __init__(self, state_stack: "StateStack | None" = None):
        self.state_stack = state_stack


    @property
    def prev_state(self) -> "State | None":
        if self.state_stack is not None and self in self.state_stack and len(self.state_stack) > 1:
            return self.state_stack[self.state_stack.index(self)-1]
        else:
            return None


    def userinput(self, inputs: InputInterpreter) -> None:
        pass


    def update(self) -> None:
        pass


    def draw(self, surface: p.Surface, lerp_amount=0.0) -> None:
        pass


    def quit(self) -> None:
        pass








class StateStack(Deque[State]):
    def __init_subclass__(cls):
        return super().__init_subclass__()
    
    
    @property
    def top_state(self) -> State:
        return self[-1]
    

    def push(self, state: State) -> None:
        # Initializing code goes here

        state.state_stack = self
        super().append(state)


    def pop(self, quit_state=True) -> State:
        state = super().pop()
        if quit_state:
            state.quit()
        
        return state
    

    def userinput(self, inputs: InputInterpreter) -> None:
        self.top_state.userinput(inputs)


    
    def update(self) -> None:
        self.top_state.update()



    def draw(self, surface: p.Surface, lerp_amount=0.0) -> str | None:
        return self.top_state.draw(surface, lerp_amount)
    


    def quit(self) -> None:
        while len(self) > 0:
            self.pop()