import pygame as pg
from pygame.locals import *

from config import *
import debug

from src.custom_types import EngineInterface
from src.input_device import InputInterpreter, KeyboardMouse

from src.file_processing import assets
from src.audio.soundfx import SoundFXManager
from src.ui import font
from src.states import StateStack, init_state



class BasicEngine(EngineInterface):
    """
    A stripped down version of the game engine that does not use threading. Framerate will be
    the same as the tickrate. Can be used to test other parts of the game if the main engine
    does not work.
    """
    def __init__(self):
        try:
            pg.mixer.pre_init(channels=128, buffer=1024)
            pg.mixer.init()
        except pg.error as e:
            print(f"Warning:", *e.args)

        pg.init()
        pg.joystick.init()
        self.__tickrate = TICKRATE
        self.__clock = pg.Clock()
        self.__state_stack = StateStack()

        self._input_interpreter = InputInterpreter(KeyboardMouse(), None)

        self._run = True
        self._error = None
    
    def get_fps(self):
        return self.__tickrate
    
    def set_fps(self, fps=0):
        raise NotImplementedError("Cannot change FPS")
    
    def get_tps(self):
        return self.__tickrate
    
    def set_tps(self, tps=TICKRATE):
        self.__tickrate = tps
    
    def toggle_fullscreen(self):
        raise NotImplementedError("Cannot toggle fullscreen")


    def start(self) -> None:
        self._window = pg.Window(WINDOW_CAPTION, WINDOW_START_SIZE)
        self._window_surface = self._window.get_surface()
        self._window.set_icon(assets.load_texture(WINDOW_ICON_PATH))
        self._window.minimum_size = WINDOW_MINIUM_SIZE
        self._game_canvas = pg.Surface(DEFAULT_CANVAS_SIZE)

        font.init()
        init_state.Initializer(self.__state_stack)

        try:
            while self._run:
                self._get_userinput()

                self.__state_stack.userinput(self._input_interpreter)
                self.__state_stack.update()
                SoundFXManager.play_sound_queue(self.__state_stack.clear_sound_queue())

                self.__state_stack.draw(self._game_canvas)
                pg.transform.scale(self._game_canvas, self._window_surface.size, self._window_surface)
                self._window.flip()
                self.__clock.tick(self.__tickrate*debug.Cheats.game_speed)
        except KeyboardInterrupt:
            self._error = KeyboardInterrupt.__name__
        
        except Exception as e:
            self._error = type(e).__name__
        
        finally:
            self.__state_stack.quit()
            print(f"error: {self._error}")


    def _get_userinput(self) -> None:
        events = pg.event.get()
        
        for event in events:
            if event.type == QUIT:
                self._run = False
                return
        
        self._input_interpreter.keyboard_mouse.get_userinput(events)
