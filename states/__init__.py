import pygame as p
from typing import Deque

from custom_types import ActionKeys, HoldKeys






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


    def userinput(self, action_keys: ActionKeys, hold_keys: HoldKeys, mouse_pos: p.Vector2) -> None:
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
    

    def userinput(self, action_keys: ActionKeys, hold_keys: HoldKeys, mouse_pos: p.Vector2) -> None:
        self.top_state.userinput(action_keys, hold_keys, mouse_pos)


    
    def update(self) -> None:
        self.top_state.update()



    def draw(self, surface: p.Surface, lerp_amount=0.0) -> None:
        self.top_state.draw(surface, lerp_amount)