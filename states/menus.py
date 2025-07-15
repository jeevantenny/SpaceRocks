import pygame as p

from . import State

from game_objects.entities import Bullet, Asteroid, DisplayPoint






class PauseMenu(State):
    def __init__(self, state_stack = None):
        super().__init__(state_stack)



    def userinput(self, inputs):
        if inputs.check_input("escape"):
            self.state_stack.pop()

    


    def draw(self, surface, lerp_amount=0):
        self.prev_state.draw(surface)
        surface.fill((50, 50, 50), special_flags=p.BLEND_SUB)




class GameOverScreen(State):
    def __init__(self, state_stack = None):
        super().__init__(state_stack)

    
    def userinput(self, inputs):
        if inputs.check_input("select"):
            from .play import Play
            self.state_stack.pop()
            self.state_stack.pop()
            self.state_stack.push(Play())

            print(self.state_stack)

    
    def update(self):
        for obj in self.prev_state.entities.sprites():
            if isinstance(obj, (Bullet, DisplayPoint)):
                obj.kill()
            
            elif isinstance(obj, Asteroid) and not obj.health:
                obj.update()


    def draw(self, surface, lerp_amount=0):
        self.prev_state.draw(surface)
            