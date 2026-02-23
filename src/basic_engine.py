import pygame as pg
from pygame.locals import *

import config
from src.input_device import InputInterpreter, KeyboardMouse

from src.file_processing import assets
from src.audio import soundfx
from src.ui import font
from src.states import StateStack, init_state



class BasicEngine:
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
        self.clock = pg.Clock()
        self.state_stack = StateStack()

        self.input_interpreter = InputInterpreter(KeyboardMouse(), None)

        self.run = True
        self.error = None


    def start(self) -> None:
        self.screen = pg.display.set_mode(config.WINDOW_START_SIZE)
        pg.display.set_caption(config.WINDOW_CAPTION)
        pg.display.set_icon(assets.load_texture(config.WINDOW_ICON_PATH))
        self.game_canvas = pg.Surface(config.DEFAULT_CANVAS_SIZE)

        font.init()
        init_state.Initializer(self.state_stack)

        try:
            while self.run:
                self.get_userinput()

                self.state_stack.userinput(self.input_interpreter)
                self.state_stack.update()
                soundfx.play_sound_queue(self.state_stack.clear_sound_queue())

                self.state_stack.draw(self.game_canvas)
                pg.transform.scale(self.game_canvas, self.screen.size, self.screen)
                pg.display.flip()
                self.clock.tick(config.TICKRATE)
        except KeyboardInterrupt:
            self.error = KeyboardInterrupt.__name__
        
        except Exception as e:
            self.error = type(e).__name__
        
        finally:
            self.state_stack.quit()
            print(f"error: {self.error}")


    def get_userinput(self) -> None:
        events = pg.event.get()
        
        for event in events:
            if event.type == QUIT:
                self.run = False
                return
        
        self.input_interpreter.keyboard_mouse.get_userinput(events)

