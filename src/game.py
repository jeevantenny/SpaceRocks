"Contains the game engine class."

import pygame as pg
from pygame.locals import *
from pygame._sdl2.video import Renderer, Texture

import threading
import traceback
from time import perf_counter

from config import *
import debug

from src import glb
from src.custom_types import EngineInterface
from src.input_device import stop_controller_rumble, KeyboardMouse, Controller, InputInterpreter

from src.ui import font
from src.states import StateStack, init_state
from src.file_processing import assets, data
from src.audio.soundfx import SoundFXManager
from src.misc import set_console_style, bar_of_dashes



class GameEngine(EngineInterface):
    """
    This engine uses two game loops that run on two threads. The main thread runs with the framerate of the game and
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

        self._setup = False
        self._setup_engine()



    def _setup_engine(self) -> None:
        "Called by the initializer to initialize the object."
        self._run = False

        self._window = None
        self._window_surface = None
        self.__fullscreen = False
        self.__do_fullscreen_toggle = False
        self.__prev_window_size: tuple[int, int] | None = None

        self._input_interpreter = InputInterpreter(KeyboardMouse(), None)
        self.__event_queue: list[pg.Event] = []

        self.__game_process_thread = threading.Thread(name="game_process", target=self._game_process_loop)
        self.__process_lock = threading.Lock()

        self._state_stack = StateStack()

        self.__tick_rate = TICKRATE
        self.__tick_clock = pg.Clock()
        self.__prev_tick = perf_counter()

        self.__framerate = FRAMERATE
        self.__frame_clock = pg.Clock()
        self.__prev_frame = perf_counter()

        self._setup = True
        self._error: str | None = None


    def get_fps(self) -> int:
        return self.__framerate
    
    def set_fps(self, fps=FRAMERATE) -> None:
        self.__framerate = fps

    def get_tps(self) -> int:
        return self.__tick_rate
    
    def set_tps(self, tps=TICKRATE) -> None:
        self.__tick_rate = tps

    def toggle_fullscreen(self) -> None:
        self.__do_fullscreen_toggle = True

    def get_game_canvas(self) -> pg.Surface:
        if self._window_surface.size != self.__prev_window_size:
            w_width, w_height = self.__constrained_window_size()
            ratio = w_width/w_height
            height = (CANVAS_AREA/ratio)**(0.5)
            width = height*ratio
            self.__game_canvas = pg.Surface((width, height))
            self.__prev_window_size = self._window_surface.size
        
        return self.__game_canvas



    def find_controllers(self) -> None:
        "Looks for connected controllers and selects the first one."

        if pg.joystick.get_count():
            try:
                self._input_interpreter.controller = Controller(pg.joystick.Joystick(0))
                print(f"Connected {self._input_interpreter.controller.device_name}")
            except pg.error:
                self._input_interpreter.controller = None
        else:
            self._input_interpreter.controller = None

    

    def start(self) -> None:
        "Starts the game."

        if not self._setup:
            raise RuntimeError("Cannot start game because an exception has occurred during setup.")
        
        self._run = True
        data.load_settings()
        self.__fullscreen = data.get_setting("open_fullscreen")

        # Setup Game Window
        self._window = pg.Window(WINDOW_CAPTION, WINDOW_START_SIZE, resizable=True, fullscreen_desktop=self.__fullscreen)
        self._window.minimum_size = WINDOW_MINIUM_SIZE
        self._renderer = Renderer(self._window)
        
        # Initialize window surface and surface convert format
        self._window_surface = self._window.get_surface()
        self._window.set_icon(assets.load_texture(WINDOW_ICON_PATH))

        # Initialize states
        font.init()
        self._debug_font = pg.font.SysFont("consolas", 13)
        init_state.Initializer(self._state_stack)

        # Starts game loop that processes game logic
        self.__game_process_thread.start()

        try:
            # Starts display and IO loop
            self._display_io_loop()
        except KeyboardInterrupt:
            self._error = KeyboardInterrupt.__name__
            # Closes game during keyboard interrupt

        finally:
            # Ensure that player data is saved when application is closed or crashes.
            self._quit_sequence()

    def quit(self) -> None:
        self._run = False




    def _game_process_loop(self) -> None:
        "Handles Window management, user-input and game logic."
        try:
            while self._run:
                self._get_userinput()
                
                self.__process_lock.acquire(timeout=0.2)
                self._userinput()
                self._update()
                self.__process_lock.release()

                self._next_tick()

        except Exception as e:
            self._error = type(e).__name__
            raise e
        finally:
            self.quit()
            


    def _display_io_loop(self) -> None:
        "Handles IO and rendering to screen."
        try:
            while self._run:
                self._process_events()
                glb.steamworks.run_callbacks()
                self._draw()
                self._next_frame()

        except Exception as e:
            self._error = type(e).__name__
            raise e
        finally:
            self.quit()


    def _process_events(self) -> None:
        self.__event_queue.extend(pg.event.get())

        if self.__do_fullscreen_toggle:
            self.__fullscreen = not self.__fullscreen
            if self.__fullscreen:
                self._window.set_fullscreen(True)
            else:
                self._window.set_windowed()
            self.__do_fullscreen_toggle = False


    def _get_userinput(self) -> None:
        "Record the user inputs for a game tick."

        current_events = self.__event_queue.copy()
        
        for event in current_events:
            if event.type == QUIT:
                self._run = False
                break

            elif event.type == JOYDEVICEADDED or event.type == JOYDEVICEREMOVED:
                self.find_controllers()
            
            self.__event_queue.remove(event)

        self._input_interpreter.get_userinput(current_events)


    def _userinput(self) -> None:
        "Processes user inputs recorded in a game tick."

        keyboard = self._input_interpreter.keyboard_mouse

        if keyboard.tap_keys[K_F11] and not keyboard.hold_keys[KMOD_CTRL] and not keyboard.hold_keys[KMOD_SHIFT]:
            self.toggle_fullscreen()

        if debug.DEBUG_MODE and keyboard.hold_keys[KMOD_CTRL]:
            if self._state_stack.top_state is not None and keyboard.tap_keys[K_BACKSPACE]:
                self._state_stack.pop()

            if keyboard.tap_keys[K_v]:
                print(self._state_stack)

        self._state_stack.userinput(self._input_interpreter)



    def _update(self) -> None:
        "Updates game logic."

        self._state_stack.update()
        if self._input_interpreter.controller is not None:
            self._input_interpreter.controller.update()

        SoundFXManager.play_sound_queue(self._state_stack.clear_sound_queue())



    def _draw(self) -> None:
        "Renders game onto screen."

        if self._state_stack:
            if debug.Cheats.no_lerp:
                lerp_amount = 1
            else:
                lerp_amount = min((self.__prev_frame-self.__prev_tick)*self.__tick_rate, 1)

            game_canvas = self.get_game_canvas()
            self._state_stack.draw(game_canvas, lerp_amount)
            
            if not self.__fullscreen:
                if data.get_setting("scale_blur"):
                    pg.transform.smoothscale(game_canvas, self._window_surface.size, self._window_surface)
                else:
                    pg.transform.scale(game_canvas, self._window_surface.size, self._window_surface)
            else:
                self._window_surface.fill("black")
                if data.get_setting("scale_blur"):
                    pg.transform.smoothscale(game_canvas, self._window_surface.size, self._window_surface)
                else:
                    pg.transform.scale(game_canvas, self._window_surface.size, self._window_surface)
                    
        else:
            self._window_surface.fill("black")

        if debug.DEBUG_MODE:
            self.__show_debug_text()
            self.__show_stack_view()


    def __show_debug_text(self) -> None:
        blit_text = f"FPS: {self.__frame_clock.get_fps():.0f}, TPS: {self.__tick_clock.get_fps():.0f}, state: {self._state_stack.top_state}"
        debug_message = self._state_stack.debug_info()
        if debug_message:
            blit_text += f"\n{debug_message}"

        text_surface = self._debug_font.render(blit_text, False, "white")
        self._window_surface.fill((100, 100, 100), (0, 0, *text_surface.size), BLEND_RGB_SUB)
        self._window_surface.blit(text_surface)

    
    def __show_stack_view(self) -> None:
        text = "-- StateStack --"
        current_state = self._state_stack.top_state

        while current_state is not None:
            text += f"\n{current_state.name}"
            current_state = current_state.prev_state
        
        text_surface = self._debug_font.render(text, False, "green")
        self._window_surface.fill((100, 100, 100), (0, self._window_surface.height-text_surface.height, *text_surface.size), BLEND_RGB_SUB)
        self._window_surface.blit(text_surface, (0, self._window_surface.height-text_surface.height))






    def _next_tick(self) -> None:
        self.__tick_clock.tick(self.__tick_rate*debug.Cheats.game_speed)
        current_time = perf_counter()
        self.__prev_tick = current_time



    def _next_frame(self) -> None:
        texture = Texture.from_surface(self._renderer, self._window_surface)
        self._renderer.blit(texture)
        self._renderer.present()
        self.__frame_clock.tick(self.__framerate)
        self.__prev_frame = perf_counter()



    def __constrained_window_size(self) -> tuple[int, int]:
        width, height = self._window_surface.size
        ratio = width/height
        
        if ratio < WINDOW_RATIO_RANGE[0]:
            height = int(width/WINDOW_RATIO_RANGE[0])
        elif ratio > WINDOW_RATIO_RANGE[1]:
            width = height*WINDOW_RATIO_RANGE[1]
        
        width = max(width, WINDOW_MINIUM_SIZE[0])
        height = max(height, WINDOW_MINIUM_SIZE[1])
        
        return width, height
    


    def _quit_sequence(self) -> None:
        "Saves any user data from states before closing application."

        self._run = False
        self.__game_process_thread.join()
        stop_controller_rumble()
        if self._error and debug.PAUSE_ON_CRASH:
            input("Save and Exit ->")
        try:
            glb.steamworks.unload()
            self._state_stack.quit()
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
            print(f"error: {self._error}")

            bar_of_dashes()
            set_console_style()


        finally:
            pg.quit()