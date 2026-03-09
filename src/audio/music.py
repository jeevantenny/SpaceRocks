"Contains stuff for music playback."
import pygame as pg

from src.custom_types import GameMusic
from src.file_processing import assets, data





class MusicManager:
    __current_music: GameMusic | None = None

    @classmethod
    def play(cls, name: str, start=0.0, loop=True) -> None:
        cls.update_music_volume()
        cls.__current_music = assets.load_music_data(name)
        cls.__current_music.play_music(start, loop)

    @classmethod
    def pause(cls) -> None:
        pg.mixer_music.pause()

    @classmethod
    def resume(cls) -> None:
        pg.mixer_music.unpause()

    @classmethod
    def stop(cls, fadeout=0.0) -> None:
        if fadeout:
            pg.mixer_music.fadeout(fadeout)
        else:
            pg.mixer_music.stop()
        
        cls.__current_music = None


    @classmethod
    def get_track_name(cls) -> str | None:
        if cls.__current_music is not None:
            return cls.__current_music.name

        
    @classmethod
    def update_music_volume(cls) -> None:
        pg.mixer_music.set_volume(data.get_setting("music_volume"))



    def __new__(cls):
        return NotImplementedError("Cannot instantiate MusicManager")