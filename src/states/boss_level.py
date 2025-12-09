import pygame as pg

from src.math_functions import vector_direction
from src.file_processing import assets
from src import ui

from src.game_objects.camera import RotoZoomCamera


from .play import Play










class PlayBossLevel(Play):
    def __init__(self):
        super().__init__("level_2")
    
    def _setup_game_objects(self):
        super()._setup_game_objects()
        self.camera = RotoZoomCamera((0, 0))
    
    def debug_info(self):
        return f"{super().debug_info()}\ncamera_rotation: {self.camera.get_rotation()}"

    
    def _update_game_objects(self):
        if self.spaceship.thrust and self.spaceship.get_speed() > 10:
            self.camera.set_target_rotation(-vector_direction(self.spaceship.get_velocity()))

        super()._update_game_objects()

    
    def _draw_scrolling_background(self, surface, lerp_amount=0):
        temp_surface = assets.colorkey_surface(pg.Vector2(surface.size)*2)
        super()._draw_scrolling_background(temp_surface, lerp_amount)
        ui.blit_to_center(pg.transform.rotate(temp_surface, -self.camera.get_lerp_rotation(lerp_amount)), surface)
    

    def quit(self) -> None:
        pass
