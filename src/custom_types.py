"""
Contains various types that will be used throughout the game.
"""

import pygame as pg
from typing import Self, Any, Literal, Callable, Generator, NamedTuple
import random
from collections import defaultdict





type TapKeys = defaultdict[int | str, bool]
type HoldKeys = defaultdict[int, int]

type InputType = Literal["controller", "keyboard_mouse"]
type BindData = dict[Literal["input_device", "key", "type", "value", "icon"] | str, InputType | str]
type KeybindsType = dict[str, list[BindData]]

type Coordinate = tuple[float, float] | pg.Vector2

type TextureMap = dict[str, pg.Surface]
type AnimData = dict[str, dict[Literal["duration", "loop", "timeline"], float | bool | dict[str, str]]]
type ControllerData = dict[Literal["name", "starting_state", "states"], str | dict[str, dict[Literal["animations", "transitions"], list[str] | dict[str, str]]]]







class GameSound:
    def __init__(self, name: str, sounds: list[pg.Sound]):
        self.name = name
        self.__sounds = sounds
    
    
    def play(self, volume=1.0, loops=0) -> pg.Channel | None:
        if self.__sounds:
            sound = random.choice(self.__sounds)
            sound.set_volume(volume)
            return sound.play(loops)
        else:
            return ValueError(f"No sounds available to play for '{self.name}'")






class Timer:
    def __init__(self, duration_ticks: int, loop=False, exec_after: Callable[[], None] | None = None):
        self.__duration = duration_ticks
        self.loop = loop
        self.__exec_after = exec_after
        self.__time_left = 0.0

    @property
    def duration(self) -> float:
        return self.__duration

    @property
    def countdown(self) -> float:
        return self.__time_left
    
    @property
    def time_elapsed(self) -> float:
        return self.__duration - self.__time_left
    
    @property
    def complete(self) -> bool:
        return self.__time_left == 0.0
    
    @property
    def completion_amount(self) -> float:
        return self.time_elapsed/self.__duration
    


    def start(self) -> Self:
        self.__time_left = self.__duration
        return self
    

    def restart(self) -> None:
        self.start()


    def end(self) -> None:
        self.__time_left == 0.0
        if self.__exec_after is not None:
            self.__exec_after()

    def update(self, speed_multiplier=1.0) -> None:
        if self.loop or not self.complete:
            self.__time_left -= speed_multiplier
            
            if self.__time_left <= 0.0:
                if self.loop:
                    self.__time_left += self.__duration
                else:
                    self.__time_left = 0.0
                if self.__exec_after is not None:
                    self.__exec_after()
    

    
    def __repr__(self) -> str:
        return f"<{type(self).__name__}: {self.countdown}>"
    



class Stopwatch:
    def __init__(self):
        self.__time = 0.0
        self.__running = False


    @property
    def time_elapsed(self) -> float:
        return self.__time
    

    def start(self) -> Self:
        self.__running = True
        return self
    
    def restart(self) -> None:
        self.reset()
        self.start()
    

    def reset(self) -> None:
        self.__time = 0.0


    def pause(self):
        self.__running = False
    

    def update(self, speed_multiplier=1.0) -> None:
        if self.__running:
            self.__time += speed_multiplier
    








class Animation:
    def __init__(self, name: str, anim_data: AnimData):
        self.name = name
        self.__anim_data = anim_data

        self.__anim_time: Timer | Stopwatch
        if "frame_duration" in self.__anim_data:
            self.prev_frame = None
            self.__flipbook = True
            self.__anim_time = Stopwatch().start()
        else:
            self.__flipbook = False
            self.__anim_time = Timer(self.duration, self.loop)
            self.__timeline = self.__convert_timeline(self.__anim_data["timeline"])
            


    @property
    def duration(self) -> float:
        if self.__flipbook:
            raise AttributeError("Can't determine duration for flipbook animation.")
        return self.__anim_data["duration"]
    
    @property
    def loop(self) -> bool:
        return self.__anim_data.get("loop", False)
    
    @property
    def anim_speed_multiplier(self) -> float:
        return self.__anim_data.get("anim_speed_multiplier", 1.0)
    
    @property
    def complete(self) -> bool:
        if self.__flipbook:
            return False
        else:
            return self.__anim_time.complete
    

    @property
    def __frame_duration(self) -> float:
        if not self.__flipbook:
            raise AttributeError("Can't determine frame duration for animation.")
        
        return self.__anim_data["frame_duration"]
    


    def update(self):
        self.__anim_time.update(self.anim_speed_multiplier)




    def restart(self) -> None:
        self.__anim_time.restart()



    def get_frame(self, texture_map: TextureMap, lerp_amount=0.0) -> pg.Surface:
        if self.__flipbook:
            return self.__get_frame_flipbook(texture_map, lerp_amount)
        current_time = self.__anim_time.time_elapsed + self.anim_speed_multiplier*lerp_amount*(not self.complete)
        prev_time = 0.0

        for time in self.__timeline.keys():
            if time > current_time:
                break
            else:
                prev_time = time

        try:
            return texture_map[self.__timeline[prev_time]]
        except KeyError:
            return pg.Surface((0, 0))
        
    

    def __get_frame_flipbook(self, texture_map: TextureMap, lerp_amount=0.0) -> pg.Surface:
        frame_time = (self.__anim_time.time_elapsed + self.anim_speed_multiplier*lerp_amount*(not self.complete))/self.__frame_duration

        frames = list(texture_map.values())

        if self.loop:
            index = int(frame_time)%len(frames)
        else:
            index = min(int(frame_time), len(frames)-1)

        return frames[index]
    

    
    @staticmethod
    def __convert_timeline(timeline: dict[str, str]) -> dict[float, str]:
        return {float(key): value for key, value in timeline.items()}
    


    def __repr__(self):
        return f"{type(self).__name__}('{self.name}')"

    







class AnimController:
    def __init__(self, controller_data: ControllerData, animations: dict[str, Animation]):
        self.__controller_data = controller_data
        self.__animations = animations
        self.set_state(self.__controller_data["starting_state"])


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




    def update(self, animated_obj) -> None:
        self.do_transitions(animated_obj)

        for anim in self.current_animations():
            anim.update()


    
    def get_frame(self, texture_map: TextureMap, lerp_amount=0.0) -> pg.Surface:
        frames = [anim.get_frame(texture_map, lerp_amount) for anim in self.current_animations()]
        if len(frames) == 1:
            return frames[0]
        
        from file_processing import assets
        base_surface = assets.colorkey_surface((max(frames, key=lambda x: x.width).width, max(frames, key=lambda x: x.height).height))

        for frame in frames:
            base_surface.blit(frame, (base_surface.size-pg.Vector2(frame.size))*0.5)
        
        return base_surface



    def restart_animations(self) -> None:
        for anim in self.current_animations():
            anim.restart()
    


    def current_animations(self) -> Generator[Animation, Any, None]:
        for anim_name in self.__current_animation_names:
            yield self.__animations[anim_name]


    def set_state(self, name: str) -> None:
        if name not in self.states:
            raise ValueError(f"Invalid state name '{name}'")
        
        self.__current_state_name = name
        self.restart_animations()

        


    def do_transitions(self, obj) -> None:
        """
        Performs any state transitions recursively until it reaches a state that no longer
        has any valid transitions.
        """

        for state_name, condition in self.__current_transitions.items():
            if self.__test_condition(obj, condition):
                self.set_state(state_name)
                self.do_transitions(obj)
                break


    
    def __test_condition(self, obj, condition: str) -> bool:
        return bool(eval(condition, None, locals()))
    



class LevelData(NamedTuple):
    level_name: str
    base_color: str
    parl_a: str
    parl_b: str
    background_palette: str
    background_tint: str

    asteroid_density: int
    asteroid_speed: tuple[float, float]
    asteroid_frequency: float
    asteroid_spawn_weights: tuple[list[str], list[int]]

    score_range: tuple[int, int]
    next_level: str




class SaveData(NamedTuple):
    level_name: str
    score: int
    entity_data: list[dict]