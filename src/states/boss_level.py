import pygame as pg

import debug

from src.math_functions import vector_direction
from src.custom_types import Timer
from src.file_processing import assets
from src.ui import font, hud, blit_to_center
from src.misc import scrolling_texture

from src.game_objects.camera import RotoZoomCamera
from src.game_objects.boss import BossShip


from .play import Play










class PlayBossLevel(Play):
    "Plays through the final level of the game (Boss level). NOT FINISHED"
    _player_max_lives=5
    _player_respawn_radius=800

    def __init__(self):
        super().__init__()
        self._setup_level("boss_level")
        self._score = 500


    @classmethod
    def init_from_save(cls, save_data):
        raise NotImplementedError


    def _setup(self):
        super()._setup()
        self.__lives_indicator = hud.LivesIndicator(self._player_max_lives)
        self.__background_surface = assets.colorkey_surface((550, 550))
    
    def _setup_game_objects(self):
        super()._setup_game_objects()
        self._camera = RotoZoomCamera((0, 0), 20)
        self.boss = BossShip((0, -500))
        # self.enemies.add(self.boss)


    def userinput(self, inputs):
        super().userinput(inputs)
        zoom = self._camera.get_zoom()
        if inputs.keyboard_mouse.hold_keys[pg.K_z]:
            zoom += 0.0615
        if inputs.keyboard_mouse.hold_keys[pg.K_x]:
            zoom -= 0.0615
        if inputs.keyboard_mouse.tap_keys[pg.K_v]:
            zoom -= 0.5
        self._camera.set_zoom(pg.math.clamp(zoom, 0.5, 3.0))
        
        if inputs.keyboard_mouse.hold_keys[pg.K_DOWN]:
            self.spaceship.move((0, 10))
        
        if inputs.keyboard_mouse.hold_keys[pg.K_r]:
            self._camera.set_zoom(1.0)


    # def update(self):
    #     self._game_loop()
    #     self._join_sound_queue(self.entities.clear_sound_queue())
    #     if not self.spaceship.health:
    #         self.camera.set_angular_vel(0)
        
    #     self._game_over_timer.update()


    def draw(self, surface, lerp_amount=0):
        super().draw(surface, lerp_amount)
        self._draw_hud(surface)



    def debug_info(self):
        return f"{super().debug_info()}\ncamera_rotation: {self._camera.get_rotation()}, camera_zoom: {self._camera.get_zoom()}, boss_health: {self.boss.health}"

    
    def _update_game_objects(self):
        if self.boss.alive():
            boss_displacement = self.boss.position-self.spaceship.position
            boss_distance = boss_displacement.magnitude()
            if boss_distance < 300:
                self.set_camera_target(self.spaceship.position + self.spaceship.get_velocity()*2 + boss_displacement*0.2)
            else:
                self.set_camera_target(self.spaceship)
            self._camera.set_target_rotation(vector_direction(boss_displacement))
            super()._update_game_objects()
            
            boss_displacement.scale_to_length(pg.math.clamp((boss_distance-250)*0.5, 3, 500))
            # self.spaceship.accelerate(boss_displacement)
            if self.spaceship.health:
                self.boss.set_velocity(-boss_displacement)
        else:
            vel = self.spaceship.get_velocity()
            if vel.magnitude_squared() > 500:
                self._camera.set_target_rotation(vector_direction(vel))
            super()._update_game_objects()

    
    def _draw_scrolling_background(self, surface, lerp_amount=0):
        self.__background_surface.fill(assets.COLORKEY)
        camera_pos = self._camera.blit_position(lerp_amount)
        blit_scale = 1/self._camera.get_zoom()

        # Background B
        if self._parl_b is not None:
            scrolling_texture(self.__background_surface, self._parl_b, camera_pos*0.1, blit_scale*0.1 + 0.9)
        # Background A
        if self._parl_a is not None:
            scrolling_texture(self.__background_surface, self._parl_a, camera_pos*0.3, blit_scale*0.3 + 0.7)
        blit_to_center(pg.transform.rotate(self.__background_surface, self._camera.get_lerp_rotation(lerp_amount)), surface)


    def _draw_hud(self, surface):
        indicator_surface = self.__lives_indicator.render(self._player_lives)
        surface.blit(indicator_surface, ((surface.width-indicator_surface.width)*0.5, surface.height-22))
        if self.spaceship.health and self.is_top_state():
            surface.blit(font.icon_font.render("Pause<pause>"), (10, surface.height-18))


    # def _game_loop(self):
    #     self._update_game_objects()



    def _game_over(self):
        self.state_stack.quit()
        PlayBossLevel().add_to_stack(self.state_stack)
