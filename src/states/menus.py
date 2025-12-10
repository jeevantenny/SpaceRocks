import pygame as pg

import config
import debug

from src.misc import increment_score, get_start_level
from src.custom_types import LevelData
from src.input_device import InputInterpreter
from src.file_processing import data

from src.ui import blit_to_center, font, effects, elements, hud

from . import State, StateStack
from .info_states import DeleteUserDataOption
from .visuals import BackgroundTint





def option_to_delete_user_data(state_stack: StateStack, inputs: InputInterpreter) -> None:
    tap_keys = inputs.keyboard_mouse.tap_keys
    hold_keys = inputs.keyboard_mouse.hold_keys

    if hold_keys[pg.KMOD_ALT] and hold_keys[pg.KMOD_SHIFT] and tap_keys[pg.K_d]:
        state_stack.push(DeleteUserDataOption())
        return





class TitleScreen(State):
    "Shows the game's title screen."
    def __init__(self):
        super().__init__()

        self.title = effects.AnimatedText(config.WINDOW_CAPTION, "main_entrance_a")
        self.__version_text = f"version {".".join(map(str, config.VERSION_NUM))}   pygame-ce {pg.ver}"

        self.__start_gameplay = False

        # Shows the controls for the game
        # This attribute is assigned a blank surface to avoid an raising an AttributeError due to
        # race condition from the drawing thread.
        self.__info_text = pg.Surface((1, 1))





    def userinput(self, inputs):
        if inputs.keyboard_mouse.hold_keys[pg.KMOD_SHIFT]:
            return

        if not self.__start_gameplay:
            if self.title.animations_complete:
                self.prev_state.spaceship.userinput(inputs)

                # The game will start once the player presses one of the controls
                if (not inputs.keyboard_mouse.hold_keys[pg.KMOD_CTRL]
                    and (inputs.check_input("select")
                         or inputs.check_input("ship_forward")
                         or inputs.check_input("shoot")
                         or inputs.check_input("ship_left")
                         or inputs.check_input("ship_right"))
                    ):
                    self.__start_gameplay = True
                    self.title.set_effect("main_exit")
                
                if inputs.check_input("settings"):
                    BackgroundTint("#4E6382").add_to_stack(self.state_stack)
                    Settings().add_to_stack(self.state_stack)
    
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
        blit_to_center(self.title.render(), surface, (0, -50))

        if not self.__start_gameplay and self.title.animations_complete:
            blit_to_center(self.__info_text, surface, (0, 50))

            if not debug.Cheats.demo_mode and self.is_top_state():
                settings_info = font.font_with_icons.render("Settings<settings>")
                info_offset = 18
                if data.load_settings().show_version_number:
                    version_text = font.small_font.render(self.__version_text, 1, "#ffffff", "#333333")
                    surface.blit(version_text, (3, config.PIXEL_WINDOW_HEIGHT-11))
                    info_offset += 10

                surface.blit(settings_info, (10, surface.height-info_offset))






class PauseMenu(State):
    "Shows the pause menu with the game title. This freezes the gameplay in the previous state."
    def __init__(self):
        super().__init__()

        self.title = effects.AnimatedText(config.WINDOW_CAPTION, "main_entrance_b")
        self.__exit_menu = False

        # Assigned default values to avoid raising Attribute Errors due to race conditions.
        self.__info_text = pg.Surface((1, 1))



    def userinput(self, inputs):
        if self.title.animations_complete:
            if inputs.check_input("pause") or inputs.check_input("select") or inputs.check_input("back"):
                self.title.set_effect("main_exit")
                self.__exit_menu = True

            elif inputs.check_input("settings"):
                Settings().add_to_stack(self.state_stack)

        
        
        if inputs.current_input_type() == "keyboard_mouse":
            self.__info_text = font.font_with_icons.render("forward<ship_forward>     shoot<shoot>     turn<left><right>")
        else:
            self.__info_text = font.font_with_icons.render("forward<ship_forward>     shoot<shoot>     turn<l_stick>")
        


    def update(self):
        self.title.update()
        if self.__exit_menu and self.title.animations_complete:
            self.state_stack.pop()
    

    def draw(self, surface, lerp_amount=0):
        self.prev_state.draw(surface, 1)
        if not self.is_top_state():
            return
        
        blit_to_center(self.title.render(lerp_amount), surface, (0, -40))
        if not self.__exit_menu:
            blit_to_center(self.__info_text, surface, (0, 30))
            surface.blit(font.font_with_icons.render("Continue<select>     settings<settings>"), (10, surface.height-18))


    def debug_info(self):
        return self.prev_state.debug_info()
    





class Settings(State):
    def __init__(self):
        super().__init__()
        settings = data.load_settings()
        self.__soundfx = elements.Slider((0, 100), int(settings.soundfx_volume*100), 10, "Sound FX")
        self.__controller_rumble = elements.Toggle(settings.controller_rumble, "Controller Rumble")
        self.__show_version_num = elements.Toggle(settings.show_version_number, "Show version number")
        self.__elements = elements.ElementList([
            self.__soundfx,
            self.__controller_rumble,
            # elements.Slider((0, 100), 0, 5, "Congo Bongo!"),
            elements.UIPadding(15),
            self.__show_version_num
        ], wrap_list=True)

        self.__background: pg.Surface | None = None

    def userinput(self, inputs):
        if not debug.Cheats.demo_mode:
            option_to_delete_user_data(self.state_stack, inputs)

        if inputs.check_input("back"):
            self.state_stack.pop()
        
        self.__elements.userinput(inputs)


    def update(self):
        self.__elements.update()
    

    def draw(self, surface, lerp_amount=0):
        self.__draw_background(surface)
        # self.prev_state.draw(surface)
        surface.blit(font.large_font.render("Settings"), (20, 20))
        self.__elements.draw(surface.subsurface(20, 50, 200, surface.height-50))
        
        surface.blit(font.font_with_icons.render("Back<back>"), (10, surface.height-18))
        surface.blit(font.small_font.render("F11 to toggle fullscreen mode"), (surface.width-112, surface.height-18))


    def __draw_background(self, surface: pg.Surface) -> None:
        """
        Background is copied and drawn over to avoid having to call draw methods of previous states. This
        was causing a major performance drop for some reason even though the settings state isn't very performance
        intensive on it's own.
        """
        if self.__background is None or self.__background.size != surface.size:
            self.prev_state.draw(surface)
            self.__background = surface.copy()
        else:
            surface.blit(self.__background)



    def quit(self):
        data.update_settings(
            soundfx_volume=round(self.__soundfx.value*0.01, 2),
            controller_rumble=self.__controller_rumble.on,
            show_version_number=self.__show_version_num.on
        )






class GameOverScreen(State):
    def __init__(self, level_data: LevelData, score_data: tuple[int, int, bool]):
        super().__init__()
        from .play import Play
        self.prev_state: Play

        self.__timer = 35

        self.__level_data = level_data
        self.__score_data = score_data
        self.display_score = 0
        self.title = effects.AnimatedText("game over", "main_entrance_a")

    
    def userinput(self, inputs):
        if inputs.check_input("select") or inputs.keyboard_mouse.tap_keys[pg.K_SPACE]:
            self.__timer = 0

    
    def update(self):
        self.title.update()
        if self.__timer == 0:
            self.state_stack.pop()
            ShowScore(self.__level_data, self.__score_data).add_to_stack(self.state_stack)
        else:
            self.__timer -= 1


    def draw(self, surface, lerp_amount=0):
        self.prev_state.draw(surface, 1)
        blit_to_center(self.title.render(lerp_amount), surface)
        
            





class ShowScore(State):
    "Shows the player what score they got on their play-through before comparing it to the highscore."
    def __init__(self, level_data: LevelData, score_data: tuple[int, int, bool]):
        super().__init__()
        self.__level_data = level_data
        self.__display_level_name = level_data.level_name.replace('_', ' ').upper()
        self.__progress_bar = hud.ProgressBar()

        self.score = score_data[0]
        self.highscore = score_data[1]
        self.new_highscore = score_data[2]
        self.display_score = 0

        # The state will go straight to comparing to highscore if the player scored not points.
        if self.score == 0:
            self.__timer = 0
        else:
            self.__timer = 30



    def userinput(self, inputs):
        if inputs.check_input("select") or inputs.keyboard_mouse.tap_keys[pg.K_SPACE]:
            if self.__timer:
                self.display_score = self.score
                self.__timer = 0
            else:
                from .play import Play

                # Empties the state stack and adds a new Play state.
                self.state_stack.quit()
                Play(get_start_level()).add_to_stack(self.state_stack)
                



    def update(self):
        if self.display_score < self.score:
            self.display_score = increment_score(self.display_score, self.score, 0.15)
            self._queue_sound("game.point", 0.3)
        elif self.__timer:
            self.__timer -= 1



    def draw(self, surface, lerp_amount=0):
        self.prev_state.draw(surface)

        if self.__timer:
            self.__draw_a(surface)
        else:
            self.__draw_b(surface)


    def __draw_a(self, surface: pg.Surface) -> None:
        blit_to_center(font.large_font.render(self.__display_level_name), surface, (0, -30))
        text_surface = font.large_font.render(f"{self.display_score:05}", 2, cache=(self.display_score==self.score))
        surface.blit(text_surface, (99, 101))


    def __draw_b(self, surface: pg.Surface) -> None:
        self.__display_score(surface, "Highscore", self.highscore, (102, 50))
        self.__display_score(surface, "Score", self.score, (102, 120))

        info_text = font.font_with_icons.render("Play Again<select>")
        surface.blit(info_text, ((surface.width-info_text.width)*0.5, 200))


    def __display_score(self, surface: pg.Surface, name: str, score: int, position=(0, 0)) -> None:
        position = pg.Vector2(position)
        text_surface = font.small_font.render(name, 2)
        surface.blit(text_surface, position+(60, 0)-pg.Vector2(text_surface.width, 0)*0.5)

        # print(f"{score:05}", score)
        number_surface = font.large_font.render(f"{score:05}", 2)
        surface.blit(number_surface, position+(0, 15))
