import pygame as pg

import config
from misc import increment_score

from file_processing import data
from custom_types import Timer

import ui
from ui import font, elements

from . import State







class TitleScreen(State):
    "Shows the game's title screen."
    def __init__(self):
        super().__init__()

        self.title = elements.TitleText(config.WINDOW_CAPTION, "main_entrance_a")
        version_text = ".".join(map(str, config.VERSION_NUM))
        self.version_text_surface = font.small_font.render(f"version {version_text}   pygame-ce {pg.ver}", 1, "#ffffff", "#333333", False)

        self.__start_gameplay = False

        # Shows the controls for the game
        # This attribute is assigned a blank surface to avoid an raising an AttributeError due to
        # race condition from the drawing thread.
        self.__info_text = pg.Surface((1, 1))





    def userinput(self, inputs):
        if not self.__start_gameplay:
            if self.title.animations_complete:
                self.prev_state.spaceship.userinput(inputs)

                # The game will start once the player presses one of the controls
                if (
                    inputs.check_input("select")
                    or inputs.check_input("ship_forward")
                    or inputs.check_input("ship_backward")
                    or inputs.check_input("shoot")
                    or inputs.check_input("left")
                    or inputs.check_input("right")
                    ):
                    self.__start_gameplay = True
                    self.title.set_effect("main_exit")
    
        else:
            self.prev_state.spaceship.userinput(inputs)

        
        # Tell the player what controls to use depending on weather they use keyboard or controller.
        if inputs.current_input_type() == "keyboard_mouse":
            self.__info_text = font.font_with_icons.render("forward<ship_forward>     shoot<shoot>     turn<left><right>")
        else:
            self.__info_text = font.font_with_icons.render("forward<ship_forward>     shoot<shoot>     turn<l_stick>")
        




    def update(self):
        self.title.update()
        if not self.__start_gameplay:
            if self.title.animations_complete:
                self.prev_state.spaceship.update()

        else:
            self.prev_state.update()
            if self.title.animations_complete:
                self.state_stack.pop()





    def draw(self, surface, lerp_amount=0):
        self.prev_state.draw(surface, lerp_amount*self.__start_gameplay)
        ui.blit_to_center(self.title.render(), surface, (0, -50))

        if not self.__start_gameplay and self.title.animations_complete:
            surface.blit(self.version_text_surface, (3, config.PIXEL_WINDOW_HEIGHT-11))
            ui.blit_to_center(self.__info_text, surface, (0, 50))






class PauseMenu(State):
    "Shows the pause menu with the game title. This freezes the gameplay in the previous state."
    def __init__(self):
        super().__init__()

        self.title = elements.TitleText(config.WINDOW_CAPTION, "main_entrance_b")
        self.__exit_menu = False

        # Assigned default values to avoid raising Attribute Errors due to race conditions.
        self.__info_text_a = pg.Surface((1, 1))
        self.__info_text_b = pg.Surface((1, 1))



    def userinput(self, inputs):
        if self.title.animations_complete and (inputs.check_input("pause") or inputs.check_input("select")):
            self.title.set_effect("main_exit")
            self.__exit_menu = True

        
        
        if inputs.current_input_type() == "keyboard_mouse":
            self.__info_text_b = font.font_with_icons.render("forward<ship_forward>     shoot<shoot>     turn<left><right>")
        else:
            self.__info_text_b = font.font_with_icons.render("forward<ship_forward>     shoot<shoot>     turn<l_stick>")
        
        self.__info_text_a = font.font_with_icons.render("Press<select> to continue")


    def update(self):
        self.title.update()
        if self.__exit_menu and self.title.animations_complete:
            self.state_stack.pop()
    

    def draw(self, surface, lerp_amount=0):
        self.prev_state.draw(surface)
        ui.blit_to_center(self.title.render(lerp_amount), surface, (0, -40))
        if not self.__exit_menu:
            ui.blit_to_center(self.__info_text_b, surface, (0, 30))
            surface.blit(self.__info_text_a, (10, surface.height-35))
            surface.blit(ui.font.small_font.render("Alt + F11 to toggle fullscreen mode"), (10, surface.height-20))


    def debug_info(self):
        return self.prev_state.debug_info()








class GameOverScreen(State):
    def __init__(self, score_data: tuple[int, int, bool]):
        super().__init__()
        from .play import Play
        self.prev_state: Play

        self.__timer = 35

        self.score_data = score_data
        self.display_score = 0
        self.title = elements.TitleText("game over", "main_entrance_a")

    
    def userinput(self, inputs):
        if inputs.check_input("select") or inputs.keyboard_mouse.action_keys[pg.K_SPACE]:
            self.__timer = 0

    
    def update(self):
        self.title.update()
        if self.__timer == 0:
            self.state_stack.pop()
            ShowScore(self.score_data).add_to_stack(self.state_stack)
        else:
            self.__timer -= 1


    def draw(self, surface, lerp_amount=0):
        self.prev_state.draw(surface, lerp_amount)
        ui.blit_to_center(self.title.render(), surface)
        
            





class ShowScore(State):
    "Shows the player what score they got on their play-through before comparing it to the highscore."
    def __init__(self, score_data: tuple[int, int, bool]):
        super().__init__()
        self.score = score_data[0]
        self.highscore = str(score_data[1])
        self.new_highscore = score_data[2]
        self.display_score = 0

        # The state will go straight to comparing to highscore if the player scored not points.
        if self.score == 0:
            self.__timer = 0
        else:
            self.__timer = 30

        self.__info_text = pg.Surface((1, 1))



    def userinput(self, inputs):
        if inputs.check_input("select") or inputs.keyboard_mouse.action_keys[pg.K_SPACE]:
            if self.__timer:
                self.display_score = self.score
                self.__timer = 0
            else:
                from .play import Play

                # Empties the state stack and adds a new Play state.
                self.state_stack.quit()
                Play("level_1").add_to_stack(self.state_stack)
                



    def update(self):
        if self.display_score < self.score:
            self.display_score = increment_score(self.display_score, self.score, 0.15)
            self._queue_sound("game.point", 0.3)
        elif self.__timer:
            self.__timer -= 1
        else:
            self.__info_text = font.font_with_icons.render("Play Again<select>")



    def draw(self, surface, lerp_amount=0):
        self.prev_state.draw(surface)

        if self.__timer:
            text_surface = font.large_font.render(ui.add_text_padding(str(self.display_score), 5, pad_char='0'), 2, cache=False)
            surface.blit(text_surface, (99, 101))
        else:
            self.__display_score(surface, "Highscore", self.highscore, (102, 50))
            self.__display_score(surface, "Score", self.score, (102, 120))
            surface.blit(self.__info_text, ((config.PIXEL_WINDOW_WIDTH-self.__info_text.width)*0.5, 200))




    def __display_score(self, surface: pg.Surface, name: str, score: int, position=(0, 0)) -> None:
        position = pg.Vector2(position)
        text_surface = font.small_font.render(name, 2)
        surface.blit(text_surface, position+(60, 0)-pg.Vector2(text_surface.width, 0)*0.5)

        number_surface = font.large_font.render(ui.add_text_padding(str(score), 5, pad_char='0'), 2)
        surface.blit(number_surface, position+(0, 15))
