"Contains the main Game class."

import pygame as p
from pygame.locals import *
import threading

import traceback
from time import perf_counter
from collections import defaultdict

import config

import states
import game_objects
from file_processing import assets
import states.play



class Game:
    "The Core part of the Game Engine."

    def __init__(self) -> None:
        p.init()
        self.run = True

        self.window = p.display.set_mode(config.WINDOW_SIZE, DOUBLEBUF)
        p.display.set_caption(config.WINDOW_CAPTION)
        p.display.set_icon(assets.load_texture(config.WINDOW_ICON_PATH))

        self.game_surface = p.Surface((p.Vector2(config.WINDOW_SIZE)/config.PIXEL_SCALE))

        self.action_keys = defaultdict(bool)
        self.hold_keys = defaultdict(float)

        self.state_stack = states.StateStack()
        self.state_stack.push(states.play.Play())

        game_speed = 1
        self.tick_rate = config.TICKRATE*game_speed

    

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
        "Record the userinputs for a given frame and process them."

        self.action_keys.clear()
        for key, amount in self.hold_keys.items():
            if amount:
                self.hold_keys[key] += self.delta_time
        
        for event in p.event.get():
            if event.type == QUIT:
                self.run = False
                break

            elif event.type == KEYDOWN:
                self.action_keys[event.key] = True
                self.hold_keys[event.key] = self.delta_time


            elif event.type == KEYUP:
                self.hold_keys[event.key] = 0.0


        self.state_stack.userinput(self.action_keys, self.hold_keys, p.mouse.get_pos())



    def update(self) -> None:
        self.state_stack.update()



    def draw(self) -> None:
        lerp_amount = min((self.prev_frame-self.prev_tick)*self.tick_rate, 1)
        self.state_stack.draw(self.game_surface, lerp_amount)

        self.window.blit(p.transform.scale(self.game_surface, config.WINDOW_SIZE))







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
        print("Program closed successfully")
        print(f"error: {self.error}")