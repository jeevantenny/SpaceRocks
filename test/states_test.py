import pygame as pg
import unittest

from src.states import State, StateStack
from src.game_errors import DuplicateStateError



class StateTest(unittest.TestCase):
    state: State

    def setUp(self):
        self.state = State()
    
    def test_init(self):
        self.assertIsNone(self.state.state_stack)
        self.assertIsNone(self.state.prev_state)
        self.assertEqual(self.state.name, type(self.state).__name__)
        self.assertEqual(str(self.state), f"<{self.state.name} State(in_state_stack=False)>")

    def test_add_to_stack(self):
        state_stack = StateStack()
        self.state.add_to_stack(state_stack)
        self.assertIs(self.state.state_stack, state_stack)
        self.assertIsNone(self.state.prev_state)
        self.assertEqual(str(self.state), f"<{self.state.name} State(in_state_stack=True)>")
    
    def test_prev_state(self):
        other_state = State()
        state_stack = StateStack([other_state, self.state])
        self.assertIs(self.state.state_stack, state_stack)
        self.assertIs(self.state.prev_state, other_state)



class StateStackTest(unittest.TestCase):
    state_stack: StateStack

    def setUp(self):
        self.state_stack = StateStack()

    def test_init(self):
        self.assertEqual(len(self.state_stack), 0)
        self.assertIsNone(self.state_stack.top_state)
        self.assertEqual(str(self.state_stack), f"<StateStack([])>")
    
    def test_init_with_states(self):
        state1 = State()
        state2 = State()
        state3 = State()
        self.state_stack = StateStack([state1, state2, state3])
        self.assertEqual(len(self.state_stack), 3)
        self.assertIs(self.state_stack.top_state, state3)

        for state in self.state_stack:
            self.assertIs(state.state_stack, self.state_stack)

    
    def test_push(self):
        state = State()
        self.state_stack.push(state)
        self.assertIs(self.state_stack.top_state, state)
        self.assertEqual(len(self.state_stack), 1)
        self.assertEqual(str(self.state_stack), f"<StateStack(['<State State>'])>")

    def test_push_duplicate_state(self):
        state = State()
        self.state_stack.push(state)
        # add the same state again
        with self.assertRaises(DuplicateStateError, msg="Did no raise DuplicateStateError when adding duplicate states to stack"):
            self.state_stack.push(state)

    def test_pop(self):
        state = State()
        self.state_stack.push(state)
        output_state = self.state_stack.pop()
        self.assertIs(output_state, state)
        self.test_init()

    def test_pop_when_empty(self):
        with self.assertRaises(IndexError, msg="Did not raise IndexError when attempting to pop from empty stack"):
            self.state_stack.pop()