import pygame as p
import random

import config
import debug

from math_functions import clamp, unit_vector

from file_processing import assets, data

from game_objects import ObjectGroup, components
from game_objects.entities import Spaceship, Asteroid

from ui import add_padding
from ui.font import LargeFont, SmallFont

from . import State
from .menus import PauseMenu, GameOverScreen






class Play(State):
    __safe_radius = 150
    __score_limit = 99999
    __asteroid_target_distance = 100

    def __init__(self, state_stack = None):
        super().__init__(state_stack)

        self.visible_area = p.Rect(0, 0, *config.PIXEL_WINDOW_SIZE)
        self.world_border = self.visible_area.inflate(100, 100)
        self.background_texture = assets.load_texture("main_background")

        self.entities = ObjectGroup()
        self.asteroids = ObjectGroup()

        self.__center = p.Vector2(config.PIXEL_WINDOW_SIZE)*0.5
        self.spaceship = Spaceship(self.__center)
        self.entities.add(self.spaceship)


        self.score = 0
        self.highscore = data.load_highscore()
        self.highscore_changed = False

        self.__timer = 10

        self._initialized = True


    def  userinput(self, inputs):
        if debug.debug_mode:
            if inputs.keyboard_mouse.action_keys[p.K_r]:
                self.spaceship.position = p.Vector2(200, 150)
                self.spaceship.set_velocity((0, 0))


            if inputs.keyboard_mouse.action_keys[p.K_k]:
                for asteroid in self.asteroids.sprites():
                    self.spaceship.score += asteroid.points
                    asteroid.kill(False)

            if inputs.keyboard_mouse.action_keys[p.K_p]:
                self.spaceship.score += 1000

            if inputs.keyboard_mouse.action_keys[p.K_c]:
                self.spaceship.combo += 50

        self.spaceship.userinput(inputs)

        if inputs.check_input("escape"):
            PauseMenu(self.state_stack)


    def update(self):
        if not self.spaceship.alive():
            self.game_over()
        
        elif random.random() < 0.3 and self.required_asteroid_count()*0.8 > self.asteroid_value():
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


        if not self.highscore_changed and self.spaceship.score > self.highscore:
            self.highscore_changed = True

        self.score = self.increment_score(self.score, self.spaceship.score)
        self.highscore = max(self.highscore, self.score)

        if self.__timer:
            self.__timer -= 1






    def _draw_pixel_art(self, surface, lerp_amount=0):
        surface.blit(self.background_texture)

        self.entities.draw(surface, lerp_amount)

        if debug.debug_mode:
            p.draw.circle(surface, "orange", self.spaceship.position, self.__safe_radius, 1)

        if isinstance(self.state_stack.top_state, (Play, PauseMenu)):
            if self.__timer:
                text_offset = -80*(self.__timer*0.1)**2
            else:
                text_offset = 0
            self.show_scores(surface, "highscore", self.highscore, (8, 4+text_offset))
            self.show_scores(surface, "score", self.score, (8, 20+text_offset))


        return f"entity count: {self.entities.count()}, asteroid value: {self.asteroid_value()}, combo: {self.spaceship.combo}"










    @classmethod
    def increment_score(cls, current_score: int, target_score: int) -> int:
        if target_score - current_score > 1000:
            current_score += 1000
        if target_score - current_score > 100:
            current_score += 100
        if target_score - current_score > 10:
            current_score += 10
        if target_score - current_score > 0:
            current_score += 1

        return min(current_score, cls.__score_limit)







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

            if (self.spaceship.position-start_position).magnitude() > self.__safe_radius:
                break

        velocity = unit_vector(self.__center-start_position)*random.randint(1, 3)
        velocity.rotate_ip(random.randint(-10, 10))

        asteroid = Asteroid(
            start_position,
            velocity,
            random.randint(1, 2)
        )

        self.entities.add(asteroid)
        self.asteroids.add(asteroid)



    def show_scores(self, surface: p.Surface, name: str, score: int, offset: p.typing.Point = (8, 4)):
        score_text = add_padding(str(score), 5, pad_char='0')

        score_desc_surf = SmallFont.render(name.capitalize())
        surface.blit(score_desc_surf, offset+p.Vector2(0, 8))
        surface.blit(LargeFont.render(score_text), offset+p.Vector2(score_desc_surf.width+max(40-score_desc_surf.width, 0), 0))



    def required_asteroid_count(self) -> int:
        return min(5 + int(self.score/50), 60)
    

    def get_asteroid_speed(self) -> float:
        return random.randint(1, min(3 + int(0.02*self.score), 5))
    

    def asteroid_value(self) -> int:
        asteroid_value = 0

        for asteroid in self.asteroids:
            asteroid_value += asteroid.size
        
        return asteroid_value
    

    def set_score(self) -> None:
        self.score = min(self.spaceship.score, self.__score_limit)
        self.highscore = max(self.highscore, self.score)

    

    
    
    def game_over(self) -> None:
        self.set_score()
        for obj in self.entities.sprites():
            if isinstance(obj, components.ObjectVelocity):
                obj.set_velocity((0, 0))
            
            if isinstance(obj, components.ObjectTexture):
                obj.set_angular_vel(0)

        GameOverScreen((self.score, self.highscore, self.highscore_changed), self.state_stack)




    def quit(self) -> None:
        self.set_score()
        data.save_highscore(self.highscore)