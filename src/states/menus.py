import pygame as pg

import config
import debug

from src.misc import increment_score, get_start_level
from src.custom_types import LevelData
from src.input_device import InputInterpreter
from src.file_processing import data

from src.ui import blit_to_center, font, effects, elements, hud

from . import State, StateStack
from .info_states import InfoState, DeleteUserDataOption
from .visuals import add_background_tint





def option_to_delete_user_data(state_stack: StateStack, inputs: InputInterpreter) -> None:
    tap_keys = inputs.keyboard_mouse.tap_keys
    hold_keys = inputs.keyboard_mouse.hold_keys

    if hold_keys[pg.KMOD_ALT] and hold_keys[pg.KMOD_SHIFT] and tap_keys[pg.K_d]:
        state_stack.push(DeleteUserDataOption())





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
                    Settings("#4E6382").add_to_stack(self.state_stack)
    
        else:
            self.prev_state.spaceship.userinput(inputs)

        
        # Tell the player what controls to use depending on weather they use keyboard or controller.
        if inputs.current_input_type() == "keyboard_mouse":
            self.__info_text = font.icon_font.render("forward<ship_forward>     shoot<shoot>     turn<left><right>")
        else:
            self.__info_text = font.icon_font.render("forward<ship_forward>     shoot<shoot>     turn<l_stick>")
        




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

            if self.is_top_state():
                info_offset = 18
                if not debug.Cheats.demo_mode:
                    if data.get_setting("show_version_number"):
                        version_text = font.small_font.render(self.__version_text, 1, "#ffffff", "#333333")
                        surface.blit(version_text, (3, surface.height-12))
                        info_offset += 10

                settings_info = font.icon_font.render("Settings<settings>")
                surface.blit(settings_info, (10, surface.height-info_offset))






class PauseMenu(State):
    "Shows the pause menu with the game title. This freezes the gameplay in the previous state."
    def __init__(self, background_tint_color: pg.typing.ColorLike = "#777777"):
        super().__init__()

        self.title = effects.AnimatedText(config.WINDOW_CAPTION, "main_entrance_b")
        self.__exit_menu = False
        self.__tint_color = background_tint_color

        # Assigned default values to avoid raising Attribute Errors.
        self.__info_text = pg.Surface((1, 1))

        from .play import Play
        self.prev_state: Play



    def userinput(self, inputs):
        if inputs.check_input("settings"):
            Settings(self.__tint_color).add_to_stack(self.state_stack)
        elif self.title.animations_complete:
            if inputs.check_input("pause") or inputs.check_input("select") or inputs.check_input("back"):
                self.title.set_effect("main_exit")
                self.__exit_menu = True

            elif inputs.check_input("quit"):
                if self.prev_state.is_saving_progress:
                    InfoState(
                        "Quit to Main Menu",
                        "Are you sure you want to quit?",
                        confirm_action=self.quit_to_main_menu,
                        can_escape=True
                    ).add_to_stack(self.state_stack)
                else:
                    self.quit_to_main_menu()
                

        
        
        if inputs.current_input_type() == "keyboard_mouse":
            self.__info_text = font.icon_font.render("forward<ship_forward>     shoot<shoot>     turn<left><right>")
        else:
            self.__info_text = font.icon_font.render("forward<ship_forward>     shoot<shoot>     turn<l_stick>")
        


    def update(self):
        self.title.update()
        if self.__exit_menu and self.title.animations_complete:
            prev_state = self.prev_state
            self.state_stack.pop()
            prev_state.update()
    

    def draw(self, surface, lerp_amount=0):
        self.prev_state.draw(surface, 1)
        if not self.is_top_state():
            return

        add_background_tint(surface, self.__tint_color)
        
        blit_to_center(self.title.render(lerp_amount), surface, (0, -40))
        if not self.__exit_menu:
            blit_to_center(self.__info_text, surface, (0, 30))
            surface.blit(font.icon_font.render("Continue<select>     Quit<quit>     Settings<settings>"), (10, surface.height-18))
            surface.blit(font.small_font.render("F11 to toggle fullscreen mode"), (surface.width-112, surface.height-18))


    def debug_info(self):
        return self.prev_state.debug_info()
    

    def quit_to_main_menu(self):
        from .init_state import Initializer
        self.prev_state.can_save_progress(False)
        self.state_stack.quit()
        Initializer.main_title_screen(self.state_stack)

    





class Settings(State):
    def __init__(self, background_tint_color: pg.typing.ColorLike = "#777777"):
        super().__init__()
        settings_elements = [
            elements.Slider("Sound FX", (0, 100), int(data.get_setting("soundfx_volume")*100), 10,
                            lambda x: data.update_settings(soundfx_volume=round(x*0.01, 2))),
            elements.Slider("Music", (0, 100), int(data.get_setting("music_volume")*100), 10,
                            lambda x: data.update_settings(music_volume=round(x*0.01, 2))),
            elements.Toggle("Controller Rumble", data.get_setting("controller_rumble"),
                            lambda x: data.update_settings(controller_rumble=x)),
            elements.Toggle("Motion blur", data.get_setting("motion_blur"),
                            lambda x: data.update_settings(motion_blur=x)),
            elements.Toggle("Pixel blur", data.get_setting("scale_blur"),
                            lambda x: data.update_settings(scale_blur=x)),

            elements.UIPadding(8),

            elements.Toggle("Show version number", data.get_setting("show_version_number"),
                            lambda x: data.update_settings(show_version_number=x)),
        ]

        self.__elements = elements.ElementList(settings_elements, wrap_list=True)

        self.__background: pg.Surface | None = None
        self.__tint_color = background_tint_color

    def userinput(self, inputs):
        if not debug.Cheats.demo_mode:
            option_to_delete_user_data(self.state_stack, inputs)
        
        if debug.DEBUG_MODE and inputs.check_input("settings"):
            self.state_stack.push(DebugMenu())

        if inputs.check_input("back"):
            self.state_stack.pop()
        
        self.__elements.userinput(inputs)


    def update(self):
        self.prev_state.update()
        self.__elements.update()
    
    def draw(self, surface, lerp_amount=0):
        self.__draw_background(surface)
        add_background_tint(surface, self.__tint_color)
        # self.prev_state.draw(surface)
        surface.blit(font.large_font.render("Settings"), (20, 20))
        self.__elements.draw(surface.subsurface(20, 50, min(250, surface.width-40), max(surface.height-50, 0)))
        
        surface.blit(font.icon_font.render("Back<back>"), (10, surface.height-18))
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
        data.save_settings()









class DebugMenu(State):
    def __init__(self):
        super().__init__()

        self.__elements = elements.ElementList([
            elements.Toggle("invincible", debug.Cheats.invincible, lambda x: setattr(debug.Cheats, "invincible", x)),
            elements.Toggle("no_obstacles", debug.Cheats.no_obstacles, lambda x: setattr(debug.Cheats, "no_obstacles", x)),
            elements.Toggle("no_point_combo", debug.Cheats.no_point_combo, lambda x: setattr(debug.Cheats, "no_point_combo", x)),
            elements.Toggle("show_bounding_boxes", debug.Cheats.show_bounding_boxes, lambda x: setattr(debug.Cheats, "show_bounding_boxes", x)),
            elements.Toggle("instance_respawn", debug.Cheats.instance_respawn, lambda x: setattr(debug.Cheats, "instance_respawn", x)),
            elements.Toggle("no_lerp", debug.Cheats.no_lerp, lambda x: setattr(debug.Cheats, "no_lerp", x)),
        ], wrap_list=True)


    def userinput(self, inputs):
        if inputs.check_input("back"):
            self.state_stack.pop()
            return

        self.__elements.userinput(inputs)
    
    def update(self):
        self.__elements.update()
    
    def draw(self, surface, lerp_amount=0):
        surface.fill("black")
        surface.blit(font.large_font.render("Debug Menu"), (20, 20))
        self.__elements.draw(surface.subsurface(20, 50, min(250, surface.width-40), max(surface.height-50, 0)))
        surface.blit(font.icon_font.render("Back<back>"), (10, surface.height-18))






class GameOverScreen(State):
    def __init__(self, level_name: str, score_data: tuple[int, int, bool]):
        super().__init__()
        from .play_level import PlayLevel
        self.prev_state: PlayLevel

        self.__timer = 35

        self.__level_name = level_name
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
            ShowScore(self.__level_name, self.__score_data).add_to_stack(self.state_stack)
        else:
            self.__timer -= 1


    def draw(self, surface, lerp_amount=0):
        self.prev_state.draw(surface, 1)
        add_background_tint(surface, "#777777")
        blit_to_center(self.title.render(lerp_amount), surface)
        
            





class ShowScore(State):
    "Shows the player what score they got on their play-through before comparing it to the highscore."
    def __init__(self, level_name: str, score_data: tuple[int, int, bool]):
        super().__init__()
        self.__level_display_name = level_name.replace('_', ' ').upper()

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
                from .play_level import PlayLevel

                # Empties the state stack and adds a new Play state.
                self.state_stack.quit()
                PlayLevel(get_start_level()).add_to_stack(self.state_stack)
        
        if not self.__timer and inputs.check_input("quit"):
            from .init_state import Initializer
            self.state_stack.quit()
            Initializer.main_title_screen(self.state_stack)
                



    def update(self):
        if self.display_score < self.score:
            self.display_score = increment_score(self.display_score, self.score, 0.15)
            self._queue_sound("game.point", 0.3)
        elif self.__timer:
            self.__timer -= 1



    def draw(self, surface, lerp_amount=0):
        self.prev_state.draw(surface)
        add_background_tint(surface, "#777777")

        if self.__timer:
            self.__draw_a(surface)
        else:
            self.__draw_b(surface)


    def __draw_a(self, surface: pg.Surface) -> None:
        blit_to_center(font.large_font.render(self.__level_display_name), surface, (0, -30))
        text_surface = font.large_font.render(f"{self.display_score:05}", 2, cache=(self.display_score==self.score))
        surface.blit(text_surface, (surface.width*0.5 - 61, surface.height*0.5 - 19))


    def __draw_b(self, surface: pg.Surface) -> None:
        self.__display_score(surface, "Highscore", self.highscore, -35)
        self.__display_score(surface, "Score", self.score, 35)

        info_text = font.icon_font.render("Play Again<select>")
        blit_to_center(info_text, surface, (0, 70))
        surface.blit(font.icon_font.render("Main menu<quit>"), (10, surface.height-18))


    def __display_score(self, surface: pg.Surface, name: str, score: int, y_offset: int) -> None:
        text_surface = font.small_font.render(name, 2)
        blit_to_center(text_surface, surface, (0, y_offset-24))

        # print(f"{score:05}", score)
        number_surface = font.large_font.render(f"{score:05}", 2)
        blit_to_center(number_surface, surface, (0, y_offset+1))
