"Contains the main Game class."

import pygame as p
from pygame.locals import *
import threading

import traceback
from time import perf_counter
from collections import defaultdict

import config
import debug

from userinput import KeyboardMouse, Controller, InputInterpreter

import states
from file_processing import assets
import states.play



class Game:
    "The Core part of the Game Engine."

    def __init__(self) -> None:
        p.init()
        p.joystick.init()

        self.run = True

        self.window = p.display.set_mode(config.WINDOW_SIZE, DOUBLEBUF)
        p.display.set_caption(config.WINDOW_CAPTION)
        p.display.set_icon(assets.load_texture(config.WINDOW_ICON_PATH))

        self.game_surface = p.Surface((p.Vector2(config.WINDOW_SIZE)/config.PIXEL_SCALE))

        self.input_interpreter = InputInterpreter(KeyboardMouse(), None)
        self.set_controllers()


        self.state_stack = states.StateStack()
        # self.state_stack.push(states.State())
        self.state_stack.push(states.play.Play())

        game_speed = 1
        self.tick_rate = config.TICKRATE*game_speed

        self.debug_font = p.font.SysFont("arial", 20)




    def set_controllers(self) -> None:
        if p.joystick.get_count():
            self.input_interpreter.controller = Controller(p.joystick.Joystick(0))
            print(f"Connected {self.input_interpreter.controller}")
        else:
            self.input_interpreter.controller = Controller()

    

    def start(self) -> None:
        "Starts the game."

        self.tick_clock = p.Clock()
        self.prev_tick = perf_counter()
        self.delta_time = 1/self.tick_rate

        self.frame_clock = p.Clock()
        self.prev_frame = perf_counter()

        self.error = False
        

        self.thread = threading.Thread(target=self.display_loop)
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

        events = p.event.get()
        
        for event in events:
            if event.type == QUIT:
                self.run = False
                break

            elif event.type == JOYDEVICEADDED or event.type == JOYDEVICEREMOVED:
                self.set_controllers()
        
        self.input_interpreter.get_userinput(events)


        if self.input_interpreter.keyboard_mouse.hold_keys[p.K_LCTRL] and self.input_interpreter.keyboard_mouse.action_keys[p.K_d]:
            debug.debug_mode = not debug.debug_mode

        self.state_stack.userinput(self.input_interpreter)



    def update(self) -> None:
        self.state_stack.update()



    def draw(self) -> None:
        if self.state_stack:
            lerp_amount = min((self.prev_frame-self.prev_tick)*self.tick_rate, 1)
            debug_message = self.state_stack.draw(self.game_surface, lerp_amount)
            
            self.window.blit(p.transform.scale(self.game_surface, config.WINDOW_SIZE))


            if debug.debug_mode:
                blit_text = f"FPS: {self.frame_clock.get_fps():.0f}, Tickrate: {self.tick_clock.get_fps():.0f}"
                if debug_message is not None:
                    blit_text = f"{blit_text}, {debug_message}"

                self.window.blit(self.debug_font.render(blit_text, False, "white", "black"))








    def next_tick(self) -> None:
        self.tick_clock.tick(self.tick_rate)
        current_time = perf_counter()
        self.delta_time = current_time - self.prev_tick
        self.prev_tick = current_time



    def next_frame(self) -> None:
        p.display.flip()

        self.frame_clock.tick(config.MAX_FPS)
        self.prev_frame = perf_counter()



    def quit(self) -> None:
        self.thread.join()
        if self.error:
            input("Continue ->")
        self.state_stack.quit()
        print("Program closed successfully")
        print(f"error: {self.error}")