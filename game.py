"Contains the main Game class."

import pygame as pg
from pygame.locals import *
import threading

import traceback
from time import perf_counter

import config
import debug

from input_device import KeyboardMouse, Controller, InputInterpreter

from ui import font
from states import StateStack, init_state
from file_processing import assets
from audio import soundfx



class Game:
    "The Core part of the Game Engine."

    def __init__(self) -> None:
        pg.mixer.pre_init(channels=128, buffer=1024)
        pg.init()
        pg.joystick.init()


        self.__setup = False
        try:
            self.__setup_engine()
        except Exception:
            traceback.print_exc()
            input("Error occurred during setup\nExit ->")




    def __setup_engine(self) -> None:
        self.run = True

        self.__set_screen_mode(False)
        self.pixel_scaled_window = pg.Surface(pg.Vector2(self.screen.size)/config.PIXEL_SCALE)
        pg.display.set_caption(config.WINDOW_CAPTION)
        pg.display.set_icon(assets.load_texture(config.WINDOW_ICON_PATH))
        self.__fullscreen = False

        self.input_interpreter = InputInterpreter(KeyboardMouse(), None)
        font.init()


        self.state_stack = StateStack()
        init_state.Initializer(self.state_stack)
        # test.TestState(self.state_stack)

        game_speed = 1
        self.tick_rate = config.TICKRATE*game_speed

        self.debug_font = pg.font.SysFont("arial", 15)
    
        self.__setup = True



    def __set_screen_mode(self, fullscreen: bool) -> None:
        if fullscreen:
            self.screen = pg.display.set_mode(config.WINDOW_SIZE, DOUBLEBUF|FULLSCREEN)
        else:
            self.screen = pg.display.set_mode(config.WINDOW_SIZE, DOUBLEBUF)
        
        self.__fullscreen = fullscreen




    def set_controllers(self) -> None:
        if pg.joystick.get_count():
            try:
                self.input_interpreter.controller = Controller(pg.joystick.Joystick(0))
                print(f"Connected {self.input_interpreter.controller.device_name}")
            except pg.error:
                self.input_interpreter.controller = Controller()
        else:
            self.input_interpreter.controller = Controller()

    

    def start(self) -> None:
        "Starts the game."

        if not self.__setup:
            raise RuntimeWarning("Cannot start game because an exception has occurred during setup.")

        self.tick_clock = pg.Clock()
        self.prev_tick = perf_counter()
        self.delta_time = 1/self.tick_rate

        self.frame_clock = pg.Clock()
        self.prev_frame = perf_counter()

        self.error = False
        

        self.thread = threading.Thread(name="display_loop", target=self.display_loop)
        try:
            self.thread.start()
            self.game_process_loop()
        finally:
            self.quit()



    def game_process_loop(self) -> None:
        try:
            while self.run:
                self.userinput()
                self.update()
                self.next_tick()
        
        except Exception:
            traceback.print_exc()
            self.run = False
            self.error = True
            


    def display_loop(self) -> None:
        try:
            while self.run:
                self.draw()
                self.next_frame()
        
        except Exception:
            traceback.print_exc()
            self.run = False
            self.error = True




    def userinput(self) -> None:
        "Record the user inputs for a given frame and process them."

        events = pg.event.get()
        
        for event in events:
            if event.type == QUIT:
                self.run = False
                break

            elif event.type == JOYDEVICEADDED or event.type == JOYDEVICEREMOVED:
                self.set_controllers()
        
        self.input_interpreter.get_userinput(events)

        keyboard = self.input_interpreter.keyboard_mouse


        
        if keyboard.hold_keys[K_LALT] and keyboard.action_keys[K_F11]:
            self.__set_screen_mode(not self.__fullscreen)


        if keyboard.hold_keys[pg.K_LCTRL] and keyboard.action_keys[pg.K_d]:
            debug.debug_mode = not debug.debug_mode


        if debug.debug_mode and keyboard.hold_keys[K_LCTRL]:
            if self.state_stack.top_state is not None and keyboard.action_keys[K_BACKSPACE]:
                self.state_stack.pop()

            if keyboard.action_keys[K_v]:
                print(self.state_stack)

        self.state_stack.userinput(self.input_interpreter)



    def update(self) -> None:
        self.state_stack.update()
        self.input_interpreter.controller.update()

        soundfx.play_sound_queue(self.state_stack.clear_sound_queue())



    def draw(self) -> None:
        if self.state_stack:
            lerp_amount = min((self.prev_frame-self.prev_tick)*self.tick_rate, 1)
            self.state_stack.draw(self.pixel_scaled_window, lerp_amount)
            pg.transform.scale_by(self.pixel_scaled_window, config.PIXEL_SCALE, self.screen)

            if debug.debug_mode:
                blit_text = f"FPS: {self.frame_clock.get_fps():.0f}, TPS: {self.tick_clock.get_fps():.0f}, state: {type(self.state_stack.top_state).__name__}"
                debug_message = self.state_stack.debug_info()
                if debug_message:
                    blit_text = f"{blit_text}\n{debug_message}"

                self.screen.blit(self.debug_font.render(blit_text, False, "white", "black"))








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
        self.thread.join()
        self.input_interpreter.controller.stop_rumble()
        if self.error:
            input("Save and Exit ->")
        try:
            self.state_stack.quit()
            print("Program closed successfully")
            print(f"error: {self.error}")
        
        except:
            traceback.print_exc()
            input("\033[91m\033[1mAn error occurred during saving. Data may not have been saved properly\033[0m\nExit ->")
        finally:
            pg.quit()