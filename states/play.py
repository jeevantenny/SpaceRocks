import pygame as p

from game_objects.entities import Spaceship

from . import State






class Play(State):
    def __init__(self, state_stack = None):
        super().__init__(state_stack)


        self.spaceship = Spaceship((200, 150))
        self.spaceship.accelerate((1, 0))


    def userinput(self, action_keys, hold_keys, mouse_pos):
        if action_keys[p.K_r]:
            self.spaceship.position = p.Vector2(200, 150)
            self.spaceship.set_velocity((0, 0))
        self.spaceship.userinput(action_keys, hold_keys)


    def update(self):
        self.spaceship.update()
        # self.spaceship.process_collision()



    def draw(self, surface, lerp_amount=0):
        surface.fill("black")
        self.spaceship.draw(surface, lerp_amount)