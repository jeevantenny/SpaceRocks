import pygame as p
import random

import config
import debug

from math_functions import clamp, unit_vector

from file_processing import assets, data

from game_objects import ObjectGroup, components
from game_objects.entities import Spaceship, Asteroid

from ui import LargeFont, SmallFont

from . import State
from .menus import PauseMenu, GameOverScreen






class Play(State):
    safe_radius = 100
    score_limit = 99999

    def __init__(self, state_stack = None):
        super().__init__(state_stack)

        self.visible_area = p.Rect(0, 0, *config.PIXEL_WINDOW_SIZE)
        self.world_border = self.visible_area.inflate(100, 100)
        self.entities = ObjectGroup()
        self.asteroids = ObjectGroup()

        self.spaceship = Spaceship(p.Vector2(config.PIXEL_WINDOW_SIZE)*0.5)
        self.entities.add(self.spaceship)


        self.score = 0
        self.highscore = data.load_highscore()


    def  userinput(self, inputs):
        if debug.debug_mode:
            if inputs.keyboard_mouse.action_keys[p.K_r]:
                self.spaceship.position = p.Vector2(200, 150)
                self.spaceship.set_velocity((0, 0))


            if inputs.keyboard_mouse.action_keys[p.K_k]:
                for asteroid in self.asteroids.sprites():
                    asteroid.force_kill()

            if inputs.keyboard_mouse.action_keys[p.K_p]:
                self.score += 1000

            if inputs.keyboard_mouse.action_keys[p.K_c]:
                self.spaceship.combo += 50

        self.spaceship.userinput(inputs)

        if inputs.check_input("escape"):
            self.state_stack.push(PauseMenu())


    def update(self):
        if not self.spaceship.alive():
            self.game_over()
        
        elif random.random() < 0.05 and self.required_asteroid_count()*0.8 > self.asteroid_value():
            self.spawn_asteroid()

        for asteroid in self.asteroids.sprites():
            if (
                not asteroid.rect.colliderect(self.world_border)
                or (not asteroid.rect.colliderect)
                ):
                asteroid.force_kill()

        for obj in self.entities:
            if isinstance(obj, Asteroid) and obj not in self.asteroids:
                self.asteroids.add(obj)
        
        self.entities.update()


        self.score = self.increment_score(self.score, self.spaceship.score)
        self.highscore = max(self.highscore, self.score)



    def draw(self, surface, lerp_amount=0):
        surface.fill((8, 8, 8))

        self.entities.draw(surface, lerp_amount)

        if not isinstance(self.state_stack.top_state, GameOverScreen):
            self.show_scores(surface, "highscore", self.highscore)
            self.show_scores(surface, "score", self.score, (8, 20))


        return f"entity count: {len(self.entities)}, asteroid value: {self.asteroid_value()}, combo: {self.spaceship.combo}"










    @classmethod
    def increment_score(cls, current_score: int, spaceship_score: int) -> int:
        if spaceship_score - current_score > 1000:
            current_score += 1000
        if spaceship_score - current_score > 100:
            current_score += 100
        if spaceship_score - current_score > 10:
            current_score += 10
        if spaceship_score - current_score > 0:
            current_score += 1

        return min(current_score, cls.score_limit)







    def spawn_asteroid(self) -> None:
        window_size = config.PIXEL_WINDOW_SIZE
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


        velocity = unit_vector(p.Vector2(window_size)*0.5-start_position)*random.randint(1, 3)


        asteroid = Asteroid(
            start_position,
            velocity,
            random.randint(1, 2)
        )

        self.entities.add(asteroid)
        self.asteroids.add(asteroid)



    def show_scores(self, surface: p.Surface, name: str, score: int, offset: p.typing.Point = (8, 4)):
        score_text = str(score)
        score_text = "0"*max(5-len(score_text), 0)+score_text

        score_desc_surf = SmallFont().render(name.capitalize())
        surface.blit(score_desc_surf, offset+p.Vector2(0, 8))
        surface.blit(LargeFont().render(score_text), offset+p.Vector2(score_desc_surf.width+max(40-score_desc_surf.width, 0), 0))



    def required_asteroid_count(self) -> int:
        return min(5 + int(self.score/50), 40)
    

    def get_asteroid_speed(self) -> float:
        return random.randint(1, min(3 + int(0.02*self.score), 5))
    

    def asteroid_value(self) -> int:
        asteroid_value = 0

        for asteroid in self.asteroids:
            asteroid_value += asteroid.size
        
        return asteroid_value
    

    
    
    def game_over(self) -> None:
        self.score = self.spaceship.score
        self.state_stack.push(GameOverScreen())




    def quit(self) -> None:
        self.highscore = clamp(self.highscore, self.spaceship.score, self.score_limit)
        data.save_highscore(self.highscore)