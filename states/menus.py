import pygame as p

from config import PIXEL_WINDOW_SIZE

from game_objects.entities import Bullet, Asteroid, DisplayPoint
from ui import LargeFont

from . import State






class PauseMenu(State):
    def __init__(self, state_stack = None):
        super().__init__(state_stack)

        self.title_text = LargeFont().render("Game Paused")
        self.text_blit_pos = (p.Vector2(PIXEL_WINDOW_SIZE)-self.title_text.size)*0.5 + (0, -40)



    def userinput(self, inputs):
        if inputs.check_input("escape"):
            self.state_stack.pop()

    


    def draw(self, surface, lerp_amount=0):
        self.prev_state.draw(surface)
        surface.fill((80, 80, 80), special_flags=p.BLEND_SUB)
        surface.blit(self.title_text, self.text_blit_pos)




class GameOverScreen(State):
    def __init__(self, state_stack = None):
        super().__init__(state_stack)

    
    def userinput(self, inputs):
        if inputs.check_input("select"):
            from .play import Play
            self.state_stack.pop()
            self.state_stack.pop()
            self.state_stack.push(Play())

    
    def update(self):
        for obj in self.prev_state.entities.sprites():
            if isinstance(obj, (Bullet, DisplayPoint)):
                obj.kill()
            
            elif isinstance(obj, Asteroid) and not obj.health:
                obj.update()


    def draw(self, surface, lerp_amount=0):
        self.prev_state.draw(surface)
            