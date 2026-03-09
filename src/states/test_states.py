import pygame as pg

from src.ui import elements, font, blit_to_center
from src.audio.music import MusicManager
from src.file_processing import data

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



class TestMusic(State):
    def __init__(self):
        super().__init__()
        MusicManager.play("test_music")
        self.__volume_slider = elements.Slider((0, 1), data.get_setting("music_volume"), 0.1)
        self.__volume_slider.on_slide(lambda x: (data.update_settings(music_volume=x), MusicManager.update_music_volume()))

    def userinput(self, inputs):
        if inputs.check_input("shoot"):
            if pg.mixer_music.get_busy():
                MusicManager.pause()
            else:
                MusicManager.resume()
        
        self.__volume_slider.userinput(inputs)

    
    def update(self):
        self.__volume_slider.update()


    def draw(self, surface, lerp_amount=0):
        blit_to_center(font.large_font.render("Music Test"), surface, (0, -30))
        blit_to_center(font.small_font.render(f"Track name: {MusicManager.get_track_name()}"), surface, (0, -12))
        blit_to_center(font.icon_font.render("Pause/Resume<shoot>"), surface)
        blit_to_center(self.__volume_slider.render(), surface, (0, 20))
