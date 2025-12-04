import pygame as pg

from src.ui import elements


from . import State




class TestElementList(State):
    def __init__(self):
        super().__init__()

        self.__elements = elements.ElementList(
            [
                elements.Toggle(False, "Test Toggle")
                for _ in range(6)
            ]
            + [
                elements.Slider((0, 100), 0, 10, "test Slider")
                for _ in range(6)
            ],
        wrap_list=True)

    def userinput(self, inputs):
        self.__elements.userinput(inputs)

    def update(self):
        self.__elements.update()
    
    def draw(self, surface, lerp_amount=0):
        surface.fill("#333333")
        self.__elements.draw(surface)