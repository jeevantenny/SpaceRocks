import pygame as p
import random

import config
import debug

from math_functions import unit_vector
from misc import increment_score

from file_processing import assets, data
from audio import soundfx

from game_objects import ObjectGroup, components
from game_objects.entities import Spaceship, Asteroid

from ui import add_padding, font

from . import State
from .menus import PauseMenu, GameOverScreen






class Play(State):
    __safe_radius = 150
    __score_limit = 99999

    def __init__(self, state_stack = None):
        super().__init__(state_stack)

        self.visible_area = p.Rect(0, 0, *config.PIXEL_WINDOW_SIZE)
        self.world_border = self.visible_area.inflate(100, 100)
        self.background_texture = assets.load_texture("backgrounds/space_background")
        self.__info_text = font.SmallFont.render("")

        self.entities = ObjectGroup()
        self.asteroids = ObjectGroup[Asteroid]()

        self.__center = p.Vector2(config.PIXEL_WINDOW_SIZE)*0.5
        self.spaceship = Spaceship(self.__center)
        self.entities.add(self.spaceship)

        self.score = 0
        self.highscore = data.load_highscore()
        self.highscore_changed = False

        self.__timer = 10

        self._initialized = True


    def userinput(self, inputs):
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

        if self.spaceship.operational and inputs.check_input("pause"):
            PauseMenu(self.state_stack)


    def update(self):
        if self.spaceship.operational:
            self.__game_loop()
        elif self.spaceship.alive():
            for entity in self.entities:
                if not isinstance(entity, Asteroid):
                    entity.update()
        
        else:
            self.__game_over()






    def draw(self, surface, lerp_amount=0.0):
        surface.blit(self.background_texture)
        # surface.fill("#333333")

        if self.spaceship.operational:
            self.entities.draw(surface, lerp_amount)
        else:
            self.entities.draw(surface)


        if debug.debug_mode:
            p.draw.circle(surface, "orange", self.spaceship.position, self.__safe_radius, 1)

        if isinstance(self.state_stack.top_state, (Play, PauseMenu)): # type: ignore
            if self.__timer:
                text_offset = -80*(self.__timer*0.1)**2
            else:
                text_offset = 0
            self.__show_scores(surface, "highscore", self.highscore, (10, 4+text_offset))
            self.__show_scores(surface, "score", self.score, (10, 20+text_offset))

        if self.spaceship.operational and self.is_top_state():
            surface.blit(self.__info_text, (10, config.PIXEL_WINDOW_SIZE[1]-20))


        return f"entity count: {self.entities.count()}, asteroid value: {self.__asteroid_value()}, combo: {self.spaceship.combo}"













    def __game_loop(self):
        if random.random() < 0.3 and self.required_asteroid_value()*0.8 > self.__asteroid_value():
            self.__spawn_asteroid()

        for asteroid in self.asteroids.sprites():
            if (
                not asteroid.rect.colliderect(self.world_border)
                or (not asteroid.rect.colliderect)
                ):
                asteroid.force_kill()


        self.entities.update()


        if not self.highscore_changed and self.spaceship.score > self.highscore:
            self.highscore_changed = True
        prev_score = self.score
        self.score = increment_score(self.score, self.spaceship.score)
        self.highscore = max(self.highscore, self.score)

        if self.score > prev_score:
            soundfx.play_sound("game.point", 0.3)

        if self.__timer:
            self.__timer -= 1

        self.__info_text = font.FontWithIcons.render("Press<pause> to pause")







    def __spawn_asteroid(self) -> None:
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

        if random.random() < self.score*0.00002:
            target_pos = self.spaceship.position
        else:
            target_pos = self.__center

        velocity = unit_vector(target_pos-start_position)*self.__get_asteroid_speed()
        velocity.rotate_ip(random.randint(-10, 10))

        asteroid = Asteroid(
            start_position,
            velocity,
            random.randint(1, 2) # type: ignore
        )

        self.entities.add(asteroid)
        self.asteroids.add(asteroid)




    def __show_scores(self, surface: p.Surface, name: str, score: int, offset: p.typing.Point):
        score_text = add_padding(str(score), 5, pad_char='0')

        score_desc_surf = font.SmallFont.render(name.capitalize())
        surface.blit(score_desc_surf, offset+p.Vector2(0, 8))
        surface.blit(font.LargeFont.render(score_text), offset+p.Vector2(score_desc_surf.width+max(40-score_desc_surf.width, 0), 0))



    def required_asteroid_value(self) -> int:
        return min(5 + int(self.score/500), 60)
    

    def __get_asteroid_speed(self) -> float:
        return random.random()*self.score*0.005+1
    

    def __asteroid_value(self) -> int:
        return sum(asteroid.size for asteroid in self.asteroids)
    

    def __set_score(self) -> None:
        self.score = min(self.spaceship.score, self.__score_limit)
        self.highscore = max(self.highscore, self.score)

    

    
    
    def __game_over(self) -> None:
        self.__set_score()
        for obj in self.entities.sprites():
            if isinstance(obj, components.ObjectVelocity):
                obj.set_velocity((0, 0))
            
            if isinstance(obj, components.ObjectTexture):
                obj.set_angular_vel(0)

        GameOverScreen((self.score, self.highscore, self.highscore_changed), self.state_stack)




    def quit(self) -> None:
        self.__set_score()
        data.save_highscore(self.highscore)