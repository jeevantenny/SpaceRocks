import pygame as p
from pygame.locals import *

from typing import Callable, Any, Literal
from collections import defaultdict

from custom_types import ActionKeys, HoldKeys
from math_functions import sign

from file_processing import load_json





class KeyboardMouse:
    def __init__(self) -> None:
        self.__action_keys: ActionKeys = defaultdict(bool)
        self.__hold_keys: HoldKeys = defaultdict(float)

    
    @property
    def action_keys(self) -> ActionKeys:
        return self.__action_keys.copy()
    
    @property
    def hold_keys(self) -> HoldKeys:
        return self.__hold_keys.copy()
    


    def get_userinput(self, events: list[p.Event]) -> None:
        self.__action_keys.clear()
        for key, amount in self.__hold_keys.items():
            if amount:
                self.__hold_keys[key] += 1
        
        for event in events:
            if event.type == KEYDOWN:
                self.__action_keys[event.key] = True
                self.__hold_keys[event.key] = 1


            elif event.type == KEYUP:
                self.__hold_keys[event.key] = 0




class Controller:
    controller_mappings = load_json("data/controller_mappings.json")
    stick_dead_zone = 0.3

    def __init__(self, joystick: p.joystick.JoystickType | None = None):
        self.__joystick = joystick
        if self.__joystick is not None:
            if (joy_name:=joystick.get_name()) in self.controller_mappings:
                self.__mappings: dict[str, dict[str, Any]] = self.controller_mappings[joy_name]
            else:
                self.__joystick = None

        self.__action_buttons: ActionKeys = defaultdict(bool)
        self.__hold_buttons: HoldKeys = defaultdict(int)

        self.__left_stick = p.Vector2()
        self.__right_stick = p.Vector2()


    @property
    def action_buttons(self) -> ActionKeys:
        return self.__action_buttons.copy()
    
    @property
    def hold_keys(self) -> HoldKeys:
        return self.__hold_buttons.copy()
    
    @property
    def left_stick(self) -> p.Vector2:
        return self.__left_stick.copy()
    
    @property
    def right_stick(self) -> p.Vector2:
        return self.__right_stick.copy()


    
    def get_userinput(self, events: list[p.Event]) -> None:
        self.__action_buttons.clear()

        if self.__joystick is None:
            return

        for button, value in self.__hold_buttons.items():
            if value:
                self.__hold_buttons[button] += 1

        for event in events:
            if event.type == JOYBUTTONDOWN:
                button_name = self.__mappings["buttons"].get(str(event.button))

                if button_name is not None:
                    self.__action_buttons[button_name] = True
                    self.__hold_buttons[button_name] = 1
                
            if event.type == JOYBUTTONUP:
                button_name = self.__mappings["buttons"].get(str(event.button))

                if button_name is not None:
                    self.__hold_buttons[button_name] = 0
            
            if event.type == JOYAXISMOTION:
                axis_data = self.__mappings["axis"].get(str(event.axis))

                if axis_data is not None and axis_data["stick"] == "left_stick":
                    self.__set_stick_value(self.__left_stick, axis_data["axis"], event.value)

                        
                if axis_data is not None and axis_data["stick"] == "right_stick":
                    self.__set_stick_value(self.__right_stick, axis_data["axis"], event.value)



    def __set_stick_value(self, stick: p.Vector2, axis: str, value: float):
        if abs(value) > self.stick_dead_zone:
            setattr(stick, axis, value)
        else:
            setattr(stick, axis, 0.0)



    def get_stick_value(self, side: Literal["left", "right"], axis: Literal["x", "y"]) -> float:
        if side == "left":
            return getattr(self.left_stick, axis)
        
        if side == "right":
            return getattr(self.right_stick, axis)















class InputInterpreter:
    __keybinds = load_json("data/keybinds.json")

    def __init__(self, keyboard_mouse: KeyboardMouse, controller: Controller):
        self.keyboard_mouse = keyboard_mouse
        self.controller = controller


    
    def get_keybind_names(self) -> list[str]:
        return list(self.__keybinds.keys())
    


    def get_userinput(self, events: list[p.Event]) -> None:
        self.keyboard_mouse.get_userinput(events)
        self.controller.get_userinput(events)


    def check_input(self, name: str) -> bool:
        if name not in self.__keybinds:
            raise ValueError(f"Invalid input name '{name}'")
        
        input_parameters = self.__keybinds[name]

        results: list[bool] = []

        if "keyboard" in input_parameters:
            keyboard_parameters = input_parameters["keyboard"]
            key_code = p.key.key_code(keyboard_parameters["key"])
            if keyboard_parameters["type"] == "hold":
                results.append(bool(self.keyboard_mouse.hold_keys[key_code]))
            else:
                results.append(self.keyboard_mouse.action_keys[key_code])
        

        if "controller" in input_parameters:
            controller_parameters = input_parameters["controller"]

            # print(controller_parameters["type"])
            match controller_parameters["type"]:
                case "action_button":
                    results.append(self.controller.action_buttons[controller_parameters["value"]])
                
                case "hold_button":
                    # print(self.controller.hold_keys)
                    results.append(bool(self.controller.hold_keys[controller_parameters["value"]]))

                case "stick":
                    side = controller_parameters["side"]
                    axis = controller_parameters["axis"]
                    target_value = controller_parameters["value"]

                    value = self.controller.get_stick_value(side, axis)

                    results.append(abs(value) > abs(target_value) and sign(value) == sign(target_value))
        

        return any(results)