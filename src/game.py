"Contains the game engine class."

import pygame as pg
from pygame.locals import *
import threading
from functools import lru_cache

import traceback
from time import perf_counter

import config
import debug

from src.input_device import stop_controller_rumble, KeyboardMouse, Controller, InputInterpreter

from src.ui import blit_to_center, font
from src.states import StateStack, init_state
from src.file_processing import assets, data
from src.audio import soundfx
from src.misc import set_console_style, bar_of_dashes



class GameEngine:
    """
    The engine uses two game loop that run on two threads. The main thread runs with the framerate of the game and
    handles window management, rendering and event handling. The second thread runs with the game's tickrate of 20
    TPS and handles user-input processing and game logic. 
    """

    def __init__(self) -> None:
        try:
            pg.mixer.pre_init(channels=128, buffer=1024)
            pg.mixer.init()
        except pg.error as e:
            print(f"Warning:", *e.args)

        pg.init()
        pg.joystick.init()

        self.__setup = False
        self.__setup_engine()


    
    @property
    def __desktop_size(self) -> None:
        return pg.display.get_desktop_sizes()[0]



    def __setup_engine(self) -> None:
        "Called by the initializer to initialize the object."
        self.run = True

        self.screen = None
        self.game_canvas = None
        self.__fullscreen = False
        self.__update_screen_mode = False

        self.input_interpreter = InputInterpreter(KeyboardMouse(), None)
        self.__event_queue: list[pg.Event] = []

        self.state_stack = StateStack()

        game_speed = 1
        self.tick_rate = config.TICKRATE*game_speed

        self.tick_clock = pg.Clock()
        self.prev_tick = perf_counter()
        self.delta_time = 1/self.tick_rate

        self.frame_clock = pg.Clock()
        self.prev_frame = perf_counter()

        self.__setup = True
        self.error: str | None = None



    def __set_screen_mode(self, fullscreen: bool) -> None:
        "Used to switch between windowed and fullscreen mode."

        if fullscreen:
            self.screen = pg.display.set_mode(self.__desktop_size, FULLSCREEN)
        else:
            self.screen = pg.display.set_mode(config.WINDOW_SIZE)
        
        self.__fullscreen = fullscreen




    def set_controllers(self) -> None:
        "Looks for connected controllers and selects the first one."

        if pg.joystick.get_count():
            try:
                self.input_interpreter.controller = Controller(pg.joystick.Joystick(0))
                print(f"Connected {self.input_interpreter.controller.device_name}")
            except pg.error:
                self.input_interpreter.controller = None
        else:
            self.input_interpreter.controller = None

    

    def start(self) -> None:
        "Starts the game."

        if not self.__setup:
            raise RuntimeWarning("Cannot start game because an exception has occurred during setup.")
        
        self.__set_screen_mode(False)
        pg.display.set_caption(config.WINDOW_CAPTION)
        pg.display.set_icon(assets.load_texture(config.WINDOW_ICON_PATH))
        self.game_canvas = pg.Surface(config.PIXEL_WINDOW_SIZE)

        font.init()
        self.debug_font = pg.font.SysFont("consolas", 13)

        init_state.Initializer(self.state_stack)

        self.game_process_thread = threading.Thread(name="game_process", target=self.game_process_loop)
        # Starts game loop that processes game logic
        self.game_process_thread.start()

        try:
            # Starts display and IO loop
            self.display_io_loop()
        except KeyboardInterrupt:
            self.error = KeyboardInterrupt.__name__
            # Closes game during keyboard interrupt

        finally:
            # Ensure that player data is saved when application is closed or crashes.
            self.quit()




    def game_process_loop(self) -> None:
        "Handles Window management, user-input and game logic."
        try:
            while self.run:
                self.get_userinput()
                self.userinput()
                self.update()
                self.next_tick()

        except Exception as e:
            self.error = type(e).__name__
            self.run = False
            raise e
            


    def display_io_loop(self) -> None:
        "Handles IO and rendering to screen."
        try:
            while self.run:
                self.__event_queue.extend(pg.event.get())
                if self.__update_screen_mode:
                    self.__set_screen_mode(self.__fullscreen)
                    self.__update_screen_mode = False

                self.draw()
                self.next_frame()

        except Exception as e:
            self.error = type(e).__name__
            self.run = False
            raise e




    def get_userinput(self) -> None:
        "Record the user inputs for a game tick."

        current_events = self.__event_queue.copy()
        
        for event in current_events:
            if event.type == QUIT:
                self.run = False
                break

            elif event.type == JOYDEVICEADDED or event.type == JOYDEVICEREMOVED:
                self.set_controllers()
            
            self.__event_queue.remove(event)

        self.input_interpreter.get_userinput(current_events)


    def userinput(self) -> None:
        "Processes user inputs recorded in a game tick."

        keyboard = self.input_interpreter.keyboard_mouse

        if keyboard.tap_keys[K_F11]:
            self.__fullscreen = not self.__fullscreen
            self.__update_screen_mode = True


        if debug.DEBUG_MODE and keyboard.hold_keys[KMOD_CTRL]:
            if self.state_stack.top_state is not None and keyboard.tap_keys[K_BACKSPACE]:
                self.state_stack.pop()

            if keyboard.tap_keys[K_v]:
                print(self.state_stack)

        self.state_stack.userinput(self.input_interpreter)



    def update(self) -> None:
        "Updates game logic."

        self.state_stack.update()
        if self.input_interpreter.controller is not None:
            self.input_interpreter.controller.update()

        soundfx.play_sound_queue(self.state_stack.clear_sound_queue())



    def draw(self) -> None:
        "Renders game onto screen."

        if self.state_stack:
            if debug.Cheats.no_lerp:
                lerp_amount = 1
            else:
                lerp_amount = min((self.prev_frame-self.prev_tick)*self.tick_rate, 1)

            self.state_stack.draw(self.game_canvas, lerp_amount)
            
            if not self.__fullscreen:
                if data.get_setting("scale_blur"):
                    pg.transform.smoothscale(self.game_canvas, self.screen.size, self.screen)
                else:
                    pg.transform.scale(self.game_canvas, self.screen.size, self.screen)
            else:
                self.screen.fill("black")
                if data.get_setting("scale_blur"):
                    blit_to_center(pg.transform.smoothscale_by(self.game_canvas, self.__fullscreen_scale(self.__desktop_size)), self.screen)
                else:
                    blit_to_center(pg.transform.scale_by(self.game_canvas, self.__fullscreen_scale(self.__desktop_size)), self.screen)
                    
        else:
            self.screen.fill("black")

        if debug.DEBUG_MODE:
            blit_text = f"FPS: {self.frame_clock.get_fps():.0f}, TPS: {self.tick_clock.get_fps():.0f}, state: {self.state_stack.top_state}"
            debug_message = self.state_stack.debug_info()
            if debug_message:
                blit_text = f"{blit_text}\n{debug_message}"
            self.screen.blit(self.debug_font.render(blit_text, False, "white", "black"))

            self.__show_stack_view()



    @lru_cache(1)
    def __fullscreen_scale(self, monitor_size: pg.typing.Point) -> float:
        return min(monitor_size[0]/config.PIXEL_WINDOW_WIDTH, monitor_size[1]/config.PIXEL_WINDOW_HEIGHT)


    
    def __show_stack_view(self) -> None:
        text = "-- StateStack --"
        current_state = self.state_stack.top_state

        while current_state is not None:
            text += f"\n{current_state.name}"
            current_state = current_state.prev_state
        
        text_surface = self.debug_font.render(text, False, "green", "black")
        self.screen.blit(text_surface, (0, self.screen.height-text_surface.height))








    def next_tick(self) -> None:
        self.tick_clock.tick(self.tick_rate)
        current_time = perf_counter()
        self.delta_time = current_time - self.prev_tick
        self.prev_tick = current_time



    def next_frame(self) -> None:
        pg.display.flip()
        self.frame_clock.tick(config.FRAMERATE)
        self.prev_frame = perf_counter()



    def quit(self) -> None:
        "Saves any user data from states before closing application."

        self.run = False
        self.game_process_thread.join()
        stop_controller_rumble()
        if self.error and debug.PAUSE_ON_CRASH:
            input("Save and Exit ->")
        try:
            self.state_stack.quit()
            data.save_settings()
        
        except:
            traceback.print_exc()

            set_console_style(91, 1)
            bar_of_dashes()

            print("\x1BAn error occurred during saving. Data may not have been saved properly.")

            bar_of_dashes()
            set_console_style()

        else:
            set_console_style(32, 1)
            bar_of_dashes()

            print("Game Data Saved")
            print(f"error: {self.error}")

            bar_of_dashes()
            set_console_style()


        finally:
            pg.quit()