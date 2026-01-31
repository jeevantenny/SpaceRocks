import pygame as pg

import debug

from src.math_functions import vector_direction
from src.custom_types import Timer
from src.file_processing import assets
from src.ui import font, hud, blit_to_center
from src.misc import get_start_level

from src.game_objects.camera import RotoZoomCamera
from src.game_objects.boss import BossShip


from .play import Play










class PlayBossLevel(Play):
    def __init__(self):
        super().__init__("boss_level")

        self.spaceship.score = 500


    @classmethod
    def init_from_save(cls, save_data):
        return super().init_from_save(save_data)


    def _setup(self):
        super()._setup()
        self.__lives_indicator = hud.LivesIndicator()
    
    def _setup_game_objects(self):
        super()._setup_game_objects()
        self.camera = RotoZoomCamera((0, 0))
        self.boss = BossShip((0, -500))
        self.enemies.add(self.boss)


    def userinput(self, inputs):
        if debug.DEBUG_MODE:
            if inputs.keyboard_mouse.tap_keys[pg.K_r]:
                self.spaceship.set_position((0, 0))
                self.spaceship.clear_velocity()

        self.spaceship.userinput(inputs)
        if self.spaceship.health and inputs.check_input("pause"):
            self._pause_game()


    def update(self):
        self._game_loop()
        self._join_sound_queue(self.entities.clear_sound_queue())
        if not self.spaceship.health:
            self.camera.set_angular_vel(0)
        
        self._game_over_timer.update()



    def debug_info(self):
        return f"{super().debug_info()}\ncamera_rotation: {self.camera.get_rotation()}"

    
    def _update_game_objects(self):
        self.entities.update(self.camera.position)
        
        boss_displacement = self.boss.position-self.spaceship.position
        self.camera.set_target_rotation(vector_direction(boss_displacement))
        # self.camera.set_zoom(pg.math.clamp((boss_displacement.magnitude()-200)*0.007, 1, 3))
        self.camera.set_target(self.spaceship.position + boss_displacement*0.3)
        self.camera.update()
        boss_displacement.scale_to_length(0.1)
        self.spaceship.accelerate(boss_displacement)

    
    def _draw_scrolling_background(self, surface, lerp_amount=0):
        temp_surface = assets.colorkey_surface(pg.Vector2(surface.size)*2)
        super()._draw_scrolling_background(temp_surface, lerp_amount)
        blit_to_center(pg.transform.rotate(temp_surface, self.camera.get_lerp_rotation(lerp_amount)), surface)


    def _draw_hud(self, surface):
        indicator_surface = self.__lives_indicator.render(3)
        surface.blit(indicator_surface, ((surface.width-indicator_surface.width)*0.5, surface.height-22))
        if self.spaceship.health and self.is_top_state():
            surface.blit(font.font_with_icons.render("Pause<pause>"), (10, surface.height-18))


    def _game_over(self):
        self.state_stack.quit()
        PlayBossLevel().add_to_stack(self.state_stack)


    def _game_loop(self):
        self._update_game_objects()
        if not self.spaceship.health and self._game_over_timer.complete:
            self._game_over_timer.start()

    

    def quit(self) -> None:
        pass
