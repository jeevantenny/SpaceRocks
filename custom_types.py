import pygame as p
from typing import Literal, Generator, Any
from collections import defaultdict

from file_processing import assets




type ActionKeys = defaultdict[int | str, bool]
type HoldKeys = defaultdict[int, int]

type Coordinate = tuple[float, float] | p.Vector2

type TextureMap = dict[str, p.Surface]
type AnimData = dict[str, dict[Literal["duration", "loop", "timeline"], float | bool | dict[str, str]]]
type ControllerData = dict[Literal["name", "starting_state", "states"], str | dict[str, dict[Literal["animations", "transitions"], list[str] | dict[str, str]]]]

# test: AnimData = {}

# a = test["nin"]["duration"]



class Animation:
    def __init__(self, name: str, anim_data: AnimData):
        self.name = name
        self.__anim_data = anim_data

        self.__anim_time = 0.0
        self.__default_frame = self.__timeline["0.0"]



    @property
    def duration(self) -> float:
        return self.__anim_data["duration"]
    
    @property
    def loop(self) -> bool:
        return self.__anim_data.get("loop", False)
    
    @property
    def anim_speed_multiplier(self) -> float:
        return self.__anim_data.get("anim_speed_multiplier", 1.0)
    
    @property
    def complete(self) -> bool:
        return self.__anim_time == self.duration
    
    @property
    def __timeline(self) -> dict[str, str]:
        return self.__anim_data["timeline"]
    


    def update(self):
        if self.__anim_time < self.duration:
            self.__anim_time += self.anim_speed_multiplier
            
            if self.__anim_time >= self.duration:
                if self.loop:
                    self.__anim_time -= self.duration
                else:
                    self.__anim_time = self.duration






    def restart(self) -> None:
        self.__anim_time = 0.0



    def get_frame(self, texture_map: TextureMap, lerp_amount=0.0) -> p.Surface:
        current_time = self.__anim_time + self.anim_speed_multiplier*lerp_amount*(not self.complete)
        prev_time = "0.0"

        for time in self.__timeline.keys():
            if float(time) > current_time:
                break
            else:
                prev_time = time

        try:
            return texture_map[self.__timeline[prev_time]]
        except KeyError:
            return p.Surface((0, 0))
    







class AnimController:
    def __init__(self, controller_data: ControllerData, animations: dict[str, Animation]):
        self.__controller_data = controller_data
        self.__animations = animations
        self.__current_state_name = self.__controller_data["starting_state"]


    @property
    def states(self) -> dict[str, dict]:
        return self.__controller_data["states"]

    @property
    def current_state(self) ->  dict[str, Any]:
        return self.states[self.__current_state_name]   

    @property
    def __current_animation_names(self) -> list[str]:
        return self.current_state["animations"]

    @property
    def __current_transitions(self) -> dict[str, str]:
        return self.current_state.get("transitions", {})

    @property
    def animations_complete(self) -> bool:
        return all([anim.complete for anim in self.current_animations()])
    


    def current_animations(self) -> Generator[Animation, Any, None]:
        for anim_name in self.__current_animation_names:
            yield self.__animations[anim_name]




    def update(self, animated_obj) -> None:
        self.__test_for_transition(animated_obj)

        for anim in self.current_animations():
            anim.update()

        


    def __test_for_transition(self, obj):
        for state_name, condition in self.__current_transitions.items():
            if self.__test_condition(obj, condition):
                self.__current_state_name = state_name
                self.__test_for_transition(obj)
                break


    
    def __test_condition(self, obj, condition: str) -> bool:
        return eval(condition, None, locals())



    def restart_animations(self) -> None:
        for anim in self.current_animations():
            anim.restart()


    
    def get_frame(self, texture_map: TextureMap, lerp_amount=0.0) -> p.Surface:
        frames = [anim.get_frame(texture_map, lerp_amount) for anim in self.current_animations()]
        base_surface = p.Surface((max(frames, key=lambda x: x.width).width, max(frames, key=lambda x: x.height).height))
        base_surface.fill(assets.COLORKEY)

        for frame in frames:
            base_surface.blit(frame, (base_surface.size-p.Vector2(frame.size))*0.5)
        base_surface.set_colorkey(assets.COLORKEY)
        return base_surface