import pygame as pg
from typing import Literal
import random

import config
from misc import increment_score

from game_objects.entities import Bullet, Asteroid, DisplayPoint, ShipSmoke
from game_objects.components import ObjectAnimation

import ui
from ui import font, elements

from . import State






def darken_surface(surface: pg.Surface) -> None:
    surface.fill("#335588", special_flags=pg.BLEND_RGB_MULT)




class TitleScreen(State):
    def __init__(self, state_stack = None):
        from .play import Play
        Play(state_stack)
        super().__init__(state_stack)
        self.prev_state: Play

        self.title = elements.TitleText((0, -50), "main_entrance_a")
        version_text = ".".join(map(str, config.VERSION_NUM))
        self.version_text_surface = font.SmallFont.render(f"version {version_text}   pygame-ce {pg.ver}", 1, "#ffffff", "#333333")

        self.__start_gameplay = False
        self.__info_text = font.SmallFont.render("")

        self._initialized = True





    def userinput(self, inputs):
        if not self.__start_gameplay:
            if self.title.current_anim_name == "main_glint":
                self.prev_state.spaceship.userinput(inputs)

                if (
                    inputs.check_input("select")
                    or inputs.check_input("ship_forward")
                    or inputs.check_input("ship_backward")
                    or inputs.check_input("shoot")
                    or inputs.check_input("left")
                    or inputs.check_input("right")
                    ):
                    self.__start_gameplay = True
                    self.title.set_current_animation("main_exit")
    
        else:
            self.prev_state.spaceship.userinput(inputs)
        




    def update(self):
        self.title.update()
        if not self.__start_gameplay:
            if self.title.animations_complete:
                self.title.set_current_animation("main_glint")
            if self.title.current_anim_name == "main_glint":
                self.prev_state.spaceship.update()

        else:
            self.prev_state.update()
            if self.title.animations_complete:
                self.state_stack.pop()
        
        self.__info_text = font.FontWithIcons.render("forward<ship_forward>     shoot<shoot>     turn<left><right>")

    def draw(self, surface, lerp_amount=0):
        self.prev_state.draw(surface, lerp_amount)
        self.title.draw(surface, lerp_amount)

        if self.title.current_anim_name == "main_glint":
            surface.blit(self.version_text_surface, (3, config.PIXEL_WINDOW_HEIGHT-11))
            ui.blit_to_centre(self.__info_text, surface, (0, 50))






class PauseMenu(State):
    def __init__(self, state_stack = None):
        super().__init__(state_stack)

        self.title = elements.TitleText((0, -35), "main_entrance_b")
        self.__exit_menu = False
        self.__info_text = font.SmallFont.render("")

        self._initialized = True



    def userinput(self, inputs):
        if self.title.animations_complete and (inputs.check_input("pause") or inputs.check_input("select")):
            self.title.set_current_animation("main_exit")
            self.__exit_menu = True


    def update(self):
        self.title.update()
        if self.__exit_menu and self.title.animations_complete:
            self.state_stack.pop()
        
        self.__info_text = font.FontWithIcons.render("Press<select> to continue")
    

    def draw(self, surface, lerp_amount=0):
        self.prev_state.draw(surface)
        darken_surface(surface)
        self.title.draw(surface, lerp_amount)
        if not self.__exit_menu:
            ui.blit_to_centre(self.__info_text, surface, (0, 50))




class GameOverScreen(State):
    def __init__(self, score_data: tuple[int, int, bool], state_stack = None):
        super().__init__(state_stack)
        from .play import Play
        self.prev_state: Play

        self.__timer = 30

        self.score_data = score_data
        self.display_score = 0
        self.title = elements.TitleText((0, 0), "game_over")

        self._initialized = True

    
    def userinput(self, inputs):
        if inputs.check_input("select") or inputs.keyboard_mouse.action_keys[pg.K_SPACE]:
            self.__timer = 0

    
    def update(self):
        if self.__timer == 0:
            self.state_stack.pop()
            ShowScore(self.score_data, self.state_stack)
        else:
            self.__timer -= 1


    def draw(self, surface, lerp_amount=0):
        self.prev_state.draw(surface, lerp_amount)
        darken_surface(surface)
        self.title.draw(surface, lerp_amount)
        
            





class ShowScore(State):
    def __init__(self, score_data: tuple[int, int, bool], state_stack = None):
        super().__init__(state_stack)
        self.score = score_data[0]
        self.highscore = str(score_data[1])
        self.new_highscore = score_data[2]
        self.display_score = 0

        if self.score == 0:
            self.__timer = 0
        else:
            self.__timer = 30

        self.__info_text = font.SmallFont.render("")

        self._initialized = True


    def userinput(self, inputs):
        if inputs.check_input("select") or inputs.keyboard_mouse.action_keys[pg.K_SPACE]:
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
            self._queue_sound("game.point", 0.3)
        elif self.__timer:
            self.__timer -= 1
        else:
            self.__info_text = font.FontWithIcons.render("Play Again<select>")



    def draw(self, surface, lerp_amount=0):
        self.prev_state.draw(surface)
        darken_surface(surface)

        if self.__timer:
            text_surface = font.LargeFont.render(ui.add_text_padding(str(self.display_score), 5, pad_char='0'), 2)
            surface.blit(text_surface, (99, 101))
        else:
            self.__display_score(surface, "Highscore", self.highscore, (102, 50))
            self.__display_score(surface, "Score", self.score, (102, 120))
            surface.blit(self.__info_text, ((config.PIXEL_WINDOW_WIDTH-self.__info_text.width)*0.5, 200))




    def __display_score(self, surface: pg.Surface, name: str, score: int, position=(0, 0)) -> None:
        position = pg.Vector2(position)
        text_surface = font.SmallFont.render(name, 2)
        surface.blit(text_surface, position+(60, 0)-pg.Vector2(text_surface.width, 0)*0.5)

        number_surface = font.LargeFont.render(ui.add_text_padding(str(score), 5, pad_char='0'), 2)
        surface.blit(number_surface, position+(0, 15))

        





