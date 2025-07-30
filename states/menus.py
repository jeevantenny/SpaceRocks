import pygame as p
from typing import Literal
import random

import config
from misc import increment_score, instructions_text

from file_processing import assets

from game_objects.entities import Bullet, Asteroid, DisplayPoint, ShipSmoke
from game_objects.components import ObjectAnimation

from ui import add_padding, font, elements

from . import State






class TitleScreen(State):
    def __init__(self, state_stack = None):
        from .play import Play
        Play(state_stack)
        super().__init__(state_stack)
        self.prev_state: Play

        self.title = elements.TitleText((92, 60), "title_entrance")
        self.version_number = font.SmallFont.render(f"version {config.VERSION_NUM}", 1, "#ffffff", "#000000")

        self.__start_gameplay = False

        self._initialized = True



    def userinput(self, inputs):
        

        if not self.__start_gameplay:
            if self.title.current_anim_name == "title_glint":
                self.prev_state.spaceship.userinput(inputs)

                if (
                    inputs.check_input("ship_forward")
                    or inputs.check_input("ship_backward")
                    or inputs.check_input("shoot")
                    or inputs.check_input("left")
                    or inputs.check_input("right")
                    ):
                    self.__start_gameplay = True
                    self.title.set_current_animation("title_exit")
        else:
            self.prev_state.spaceship.userinput(inputs)
        




    def update(self):
        self.title.update()
        if not self.__start_gameplay:
            if self.title.animations_complete:
                self.title.set_current_animation("title_glint")
            if self.title.current_anim_name == "title_glint":
                self.prev_state.spaceship.update()

        else:
            self.prev_state.update()
            if self.title.animations_complete:
                self.state_stack.pop()

    def draw(self, surface, lerp_amount=0):
        self.prev_state.draw(surface, lerp_amount)
        super().draw(surface, lerp_amount)


    def _draw_pixel_art(self, surface, lerp_amount=0):
        surface.blit(self.version_number, (2, config.PIXEL_WINDOW_SIZE[1]-10))
        self.title.draw(surface, lerp_amount)

        if self.title.current_anim_name != "title_entrance":
            text_surface = font.SmallFont.render(instructions_text())
            surface.blit(text_surface, ((config.PIXEL_WINDOW_SIZE[0]-text_surface.width)*0.5, 170))






class PauseMenu(State):
    def __init__(self, state_stack = None):
        super().__init__(state_stack)

        self.title_text = font.LargeFont.render("Game Paused")
        self.text_blit_pos = (p.Vector2(config.PIXEL_WINDOW_SIZE)-self.title_text.size)*0.5 + (0, -40)

        self._initialized = True



    def userinput(self, inputs):
        if inputs.check_input("escape"):
            self.state_stack.pop()

    

    def draw(self, surface, lerp_amount=0):
        self.prev_state.draw(surface)
        surface.fill("#505050", special_flags=p.BLEND_SUB)
        return super().draw(surface, lerp_amount)


    def _draw_pixel_art(self, surface, lerp_amount=0):
        surface.blit(self.title_text, self.text_blit_pos)




class GameOverScreen(State):
    def __init__(self, score_data: tuple[int, int, bool], state_stack = None):
        super().__init__(state_stack)
        from .play import Play
        self.prev_state: Play

        self.__timer = 30

        self.score_data = score_data
        self.display_score = 0

        self._initialized = True

    
    def userinput(self, inputs):
        if inputs.check_input("select"):
            self.__timer = 0

    
    def update(self):
        for obj in self.prev_state.entities.sprites():
            if isinstance(obj, (Bullet, DisplayPoint)):
                obj.kill()
            
            elif (isinstance(obj, Asteroid) and not obj.health) or isinstance(obj, ShipSmoke):
                obj.update()

        if self.__timer == 0:
            self.state_stack.pop()
            ShowScore(self.score_data, self.state_stack)
        else:
            self.__timer -= 1


    def draw(self, surface, lerp_amount=0):
        self.prev_state.draw(surface, lerp_amount)
            





class ShowScore(State):
    def __init__(self, score_data: tuple[int, int, bool], state_stack = None):
        super().__init__(state_stack)
        self.score = score_data[0]
        self.highscore = str(score_data[1])
        self.new_highscore = str(score_data[2])
        self.display_score = 0

        self.__timer = 30

        self.__final_stats: p.Surface | None = None

        self._initialized = True


    def userinput(self, inputs):
        if inputs.check_input("select"):
            if self.__timer:
                self.display_score = self.score
                self.__timer = 0
            else:
                from .play import Play

                self.state_stack.quit()
                Play(self.state_stack)
                



    def update(self):
        if self.display_score < self.score:
            self.display_score = increment_score(self.display_score, self.score, 0.15)
        elif self.__timer:
            self.__timer -= 1
        
        elif self.__final_stats is None:
            pass



    def draw(self, surface, lerp_amount=0):
        self.prev_state.draw(surface)
        surface.fill("#404040", special_flags=p.BLEND_RGB_SUB)
        return super().draw(surface, lerp_amount)
    

    def __display_score(self, surface: p.Surface, name: str, score: int, position=(0, 0)) -> None:
        position = p.Vector2(position)
        text_surface = font.SmallFont.render(name, 2)
        surface.blit(text_surface, position+(60, 0)-p.Vector2(text_surface.width, 0)*0.5)

        number_surface = font.LargeFont.render(add_padding(str(score), 5, pad_char='0'), 2)
        surface.blit(number_surface, position+(0, 15))



    def _draw_pixel_art(self, surface, lerp_amount=0):

        if self.__timer:
            text_surface = font.LargeFont.render(add_padding(str(self.display_score), 5, pad_char='0'), 2)
            surface.blit(text_surface, (99, 101))
        else:
            self.__display_score(surface, "Highscore", self.highscore, (102, 50))
            self.__display_score(surface, "Score", self.score, (102, 120))
        





    