import pygame as pg
from pygame.locals import *

from typing import Any, Literal
from collections import defaultdict

from src.custom_types import TapKeys, HoldKeys, InputType, BindData, KeybindsType
from src.math_functions import sign

from src.file_processing import load_json, data



INPUT_FORMAT_DIR = "data/input_devices"



def controller_rumble(pattern_name: str, intensity=0.5, wait_until_clear=False) -> None:
    """
    Makes the controller vibrate in a certain pattern defined in `rumble_patterns.json` with a specific intensity.
    The `wait_until_clear` parameter means thr rumble pattern will not be played if a pattern is already playing.
    """
    if Controller.current_instance is not None and  InputInterpreter.current_input_type() == "controller":
        Controller.current_instance.rumble(pattern_name, intensity, wait_until_clear)



def get_control_icon_name(action_name: str) -> str | None:
    return InputInterpreter.get_control_icon_name(action_name)



class KeyboardMouse:
    def __init__(self) -> None:
        self.__tap_keys: TapKeys = defaultdict(bool)
        self.__hold_keys: HoldKeys = defaultdict(float)

    
    @property
    def tap_keys(self) -> TapKeys:
        return self.__tap_keys.copy()
    
    @property
    def hold_keys(self) -> HoldKeys:
        return self.__hold_keys.copy()
    


    def get_userinput(self, events: list[pg.Event]) -> None:
        self.__tap_keys.clear()
        for key, amount in self.__hold_keys.items():
            if amount:
                self.__hold_keys[key] += 1
        
        for event in events:
            if event.type == KEYDOWN:
                key = self.__get_key(event.key)
                self.__tap_keys[key] = True
                self.__tap_keys["any"] = True
                self.__hold_keys[key] = 1


            elif event.type == KEYUP:
                key = self.__get_key(event.key)
                self.__hold_keys[key] = 0


    def __get_key(self, event_key: int) -> int:
        "Detects modifier keys and converts the to pygame key mod values."
        if event_key in (K_LCTRL, K_RCTRL):
            return KMOD_CTRL
        elif event_key in (K_LSHIFT, K_RSHIFT):
            return KMOD_SHIFT
        elif event_key in (K_LALT, K_RALT):
            return KMOD_ALT
        else:
            return event_key






class Controller:
    __controller_mappings = load_json(f"{INPUT_FORMAT_DIR}/controller_mappings")
    __rumble_patterns = load_json(f"{INPUT_FORMAT_DIR}/rumble_patterns")
    __stick_dead_zone = 0.3

    current_instance: "Controller | None" = None

    def __init__(self, joystick: pg.joystick.JoystickType | None = None):
        self.__joystick = joystick
        if self.__joystick is not None:
            working_name = self.device_name
            if working_name not in self.__controller_mappings:
                working_name = self.__controller_mappings["default"]

            working_name = self.__controller_mappings[working_name].get("same_as", working_name)
            self.__mappings: dict[str, dict[str, Any]] = self.__controller_mappings[working_name]


        self.__tap_buttons: TapKeys = defaultdict(bool)
        self.__hold_buttons: HoldKeys = defaultdict(int)

        self.__left_stick = pg.Vector2()
        self.__right_stick = pg.Vector2()

        self.__left_trigger = 0.0
        self.__right_trigger = 0.0

        self.__rumble_queue = []
        
        type(self).current_instance = self


    @property
    def device_name(self) -> str | None:
        if self.__joystick is not None:
            return self.__joystick.get_name()
        else:
            return None


    @property
    def tap_buttons(self) -> TapKeys:
        return self.__tap_buttons.copy()
    @property
    def hold_keys(self) -> HoldKeys:
        return self.__hold_buttons.copy()
    
    @property
    def left_stick(self) -> pg.Vector2:
        return self.__left_stick.copy()
    @property
    def right_stick(self) -> pg.Vector2:
        return self.__right_stick.copy()
    
    @property
    def left_trigger(self) -> float:
        return self.__left_trigger
    @property
    def right_trigger(self) -> float:
        return self.__right_trigger


    
    def get_userinput(self, events: list[pg.Event]) -> None:
        self.__tap_buttons.clear()

        if self.__joystick is None:
            return

        for button, value in self.__hold_buttons.items():
            if value:
                self.__hold_buttons[button] += 1

        for event in events:
            if event.type == JOYBUTTONDOWN:
                button_name = self.__mappings["buttons"].get(str(event.button))

                if button_name is not None:
                    self.__tap_buttons[button_name] = True
                    self.__tap_buttons["any"] = True
                    self.__hold_buttons[button_name] = 1

                #     print(event.button, button_name)
                # else:
                #     print(event.button)
                
            if event.type == JOYBUTTONUP:
                button_name = self.__mappings["buttons"].get(str(event.button))

                if button_name is not None:
                    self.__hold_buttons[button_name] = 0
            
            if event.type == JOYAXISMOTION:
                axis_data = self.__mappings["axis"].get(str(event.axis))


                if axis_data is not None:
                    match axis_data["stick"]:
                        case "left_stick":
                            self.__set_stick_value(self.__left_stick, axis_data["axis"], event.value)
  
                        case "right_stick":
                            self.__set_stick_value(self.__right_stick, axis_data["axis"], event.value)
                        
                        case "l_trigger":
                            if abs(event.value) > self.__stick_dead_zone:
                                self.__left_trigger = event.value
                            else:
                                self.__left_trigger = 0.0
                        
                        case "r_trigger":
                            if abs(event.value) > self.__stick_dead_zone:
                                self.__right_trigger = event.value
                            else:
                                self.__right_trigger = 0.0
    




    def update(self) -> None:
        if self.__rumble_queue:
            if data.load_settings().controller_rumble:
                self.__joystick.rumble(*self.__rumble_queue.pop(0))
            else:
                self.__rumble_queue.clear()







    def __set_stick_value(self, stick: pg.Vector2, axis: str, value: float):
        if abs(value) > self.__stick_dead_zone:
            setattr(stick, axis, value)
        else:
            setattr(stick, axis, 0.0)






    def get_stick_value(self, side: Literal["left", "right"], axis: Literal["x", "y"]) -> float:
        if side == "left":
            return getattr(self.left_stick, axis)
        
        if side == "right":
            return getattr(self.right_stick, axis)
        


    def rumble(self, pattern_name: str, intensity: float, wait_until_clear: bool) -> None:
        if pattern_name not in self.__rumble_patterns:
            raise ValueError(f"Invalid rumble pattern {pattern_name}")

        if self.__joystick is None or not data.load_settings().controller_rumble or (wait_until_clear and self.__rumble_queue):
            return
        
        self.__rumble_queue.clear()

        prev_time = -1
        for time, values in self.__rumble_patterns[pattern_name].items():
            time = int(time)
            working_values = values.copy()
            working_values[0] *= intensity
            working_values[1] *= intensity
            for _ in range(time-prev_time):
                self.__rumble_queue.append(working_values)
            
            prev_time = time




    
    def stop_rumble(self) -> None:
        if self.__joystick is not None:
            self.__rumble_queue.clear()
            self.__joystick.stop_rumble()


















class InputInterpreter:
    __keybinds: KeybindsType = load_json(f"{INPUT_FORMAT_DIR}/action_mappings")
    __action_icons = load_json(f"{INPUT_FORMAT_DIR}/action_icons")
    __current_instance: "InputInterpreter | None" = None

    def __init__(self, keyboard_mouse: KeyboardMouse, controller: Controller| None):
        self.__current_input_type: InputType

        self.__keyboard_mouse = keyboard_mouse
        if controller is None:
            self.controller = Controller(None)
        else:
            self.controller = controller
        
        type(self).__current_instance = self


    @property
    def keyboard_mouse(self) -> KeyboardMouse:
        return self.__keyboard_mouse
    
    @property
    def controller(self) -> Controller | None:
        return self.__controller
    @controller.setter
    def controller(self, value: Controller | None) -> None:
        self.__controller = value
        if self.controller.device_name is not None:
            self.__current_input_type = "controller"
        else:
            self.__current_input_type = "keyboard_mouse"


    @classmethod
    def current_input_type(cls) -> InputType:
        return cls.__current_instance.__current_input_type


    
    def get_keybind_names(self) -> list[str]:
        return list(self.__keybinds.keys())
    


    def __get_bind_options(self, action_name: str) -> list[BindData]:
        if action_name not in self.__keybinds:
            raise ValueError(f"Invalid action_name '{action_name}'")
        else:
            return self.__keybinds[action_name]

    


    def get_userinput(self, events: list[pg.Event]) -> None:
        self.__keyboard_mouse.get_userinput(events)
        if self.__controller.tap_buttons["any"]:
            self.__current_input_type = "controller"

        self.__controller.get_userinput(events)
        if self.__keyboard_mouse.tap_keys["any"]:
            self.__current_input_type = "keyboard_mouse"


    def check_input(self, action_name: str) -> bool:
        results: list[bool] = []

        for bind_data in self.__get_bind_options(action_name):
            if bind_data["input_device"] == "keyboard_mouse":
                key_code = pg.key.key_code(bind_data["key"])
                if bind_data["type"] == "hold":
                    results.append(self.__keyboard_mouse.hold_keys[key_code] > bind_data.get("threshold", 0))
                else:
                    results.append(self.__keyboard_mouse.tap_keys[key_code])
        

            elif bind_data["input_device"] == "controller":
                match bind_data["type"]:
                    case "tap_button":
                        results.append(self.__controller.tap_buttons[bind_data["value"]])
                    
                    case "hold_button":
                        # print(self.__controller.hold_keys)
                        results.append(self.__controller.hold_keys[bind_data["value"]] > bind_data.get("threshold", 0))

                    case "stick" | "trigger":
                        side = bind_data["side"]
                        target_value = bind_data["value"]

                        if bind_data["type"] == "stick":
                            axis = bind_data["axis"]
                            value = self.__controller.get_stick_value(side, axis)
                        elif side == "right":
                            value = self.__controller.right_trigger
                        else:
                            value = self.__controller.left_trigger

                        results.append(abs(value) > abs(target_value) and sign(value) == sign(target_value))
        

        return any(results)
    


    def __get_all_control_icons(self) -> dict[str, str]:
        if self.__current_input_type == "keyboard_mouse":
            return self.__action_icons[self.__current_input_type]
        else:
            return self.__get_controller_icon_names(self.controller.device_name)
    

    def __get_controller_icon_names(self, controller_name: str) -> dict[str, str]:
        icons = self.__action_icons["controllers"][controller_name]
        if "same_as" in icons:
            icons = self.__get_controller_icon_names(icons["same_as"]) | icons
        
        return icons




    @classmethod
    def get_control_icon_name(cls, action_name: str) -> str | None:
        self = cls.__current_instance

        try:
            return self.__get_all_control_icons()[action_name]
        except KeyError:
            return None