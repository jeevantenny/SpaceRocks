import pygame as p
import random

import config
from custom_types import Coordinate
from math_functions import unit_vector

from game_objects import ObjectGroup
from game_objects.entities import Spaceship, Asteroid

from ui import LargeFont, SmallFont

from . import State






class Play(State):
    safe_radius = 100
    def __init__(self, state_stack = None):
        super().__init__(state_stack)

        self.window_border = p.Rect(0, 0, *config.PIXEL_WINDOW_SIZE)
        self.entities = ObjectGroup()
        self.asteroids = ObjectGroup()

        self.spaceship = Spaceship((200, 120))
        self.entities.add(self.spaceship)

        self.new_asteroids = []

        self.score = 0
        self.highscore = 12


    def userinput(self, action_keys, hold_keys, mouse_pos):
        if action_keys[p.K_r]:
            self.spaceship.position = p.Vector2(200, 150)
            self.spaceship.set_velocity((0, 0))
        self.spaceship.userinput(action_keys, hold_keys)


        if action_keys[p.K_k]:
            for asteroid in self.asteroids.sprites():
                asteroid.kill()

        if action_keys[p.K_p]:
            self.score += 1000


    def update(self):
        # if random.random() < 0.3 and self.required_asteroid_count() > self.asteroid_value():
        #     self.spawn_asteroid()

        # for asteroid in self.new_asteroids.copy():
        #     if self.window_border.contains(asteroid.get_rect()):
        #         asteroid.set_bounding_area(self.window_border)
        #         self.new_asteroids.remove(asteroid)
        
        self.entities.update()

        if self.spaceship.score > self.score:
            self.score += 1
        
        self.highscore = max(self.highscore, self.score)



    def spawn_asteroid(self) -> None:
        window_size = config.PIXEL_WINDOW_SIZE
        initial_border = p.Rect(0, 0, *p.Vector2(window_size)/config.PIXEL_SCALE).inflate(100, 100)
        start_position = p.Vector2()

        while True:
            if random.randint(0, 1):
                start_position.x = random.randint(0, window_size[0])
                start_position.y = random.choice([-32, window_size[1]+32])
            
            else:
                start_position.x = random.choice([-32, window_size[0]+32])
                start_position.y = random.randint(0, window_size[1])

            if (self.spaceship.position-start_position).magnitude() > self.safe_radius:
                break


        asteroid = Asteroid(
            start_position,
            unit_vector(self.spaceship.position-start_position)*self.get_asteroid_speed(),
            initial_border,
            random.randint(1, 2)
        )

        self.entities.add(asteroid)
        self.asteroids.add(asteroid)
        self.new_asteroids.append(asteroid)



    def show_scores(self, surface: p.Surface, name: str, score: int, offset: Coordinate = (8, 4)):
        score_text = str(score)
        score_text = "0"*max(5-len(score_text), 0)+score_text

        score_desc_surf = SmallFont().render(name.capitalize())
        surface.blit(score_desc_surf, offset+p.Vector2(0, 8))
        surface.blit(LargeFont().render(score_text), offset+p.Vector2(score_desc_surf.width+max(40-score_desc_surf.width, 0), 0))



    def required_asteroid_count(self) -> int:
        return 7 + int(self.score**0.9 * 0.04)
    

    def get_asteroid_speed(self) -> float:
        return random.randint(1, min(3 + int(0.02*self.score), 5))
    

    def asteroid_value(self) -> int:
        asteroid_value = 0

        for asteroid in self.asteroids:
            asteroid_value += asteroid.size
        
        return asteroid_value



    def draw(self, surface, lerp_amount=0):
        surface.fill("black")

        self.entities.draw(surface, lerp_amount)

        self.show_scores(surface, "highscore", self.highscore)
        self.show_scores(surface, "score", self.score, (8, 20))