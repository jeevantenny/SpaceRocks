import pygame as pg

from math_functions import clamp

from file_processing import assets


SoundQueue = list[tuple[str, float]]



def play_sound(name: str, volume=1.0, loops=0) -> pg.Channel:
    sound = assets.load_sound(name)
    return sound.play(clamp(volume, 0, 1), loops)



def play_sound_queue(queue: SoundQueue) -> None:
    for sound_values in queue:
        play_sound(*sound_values)



class HasSoundQueue:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__sound_queue: SoundQueue = []


    def _queue_sound(self, sound_name: str, volume=1.0) -> None:
        self.__sound_queue.append((sound_name, volume))

    def _join_sound_queue(self, queue: SoundQueue) -> None:
        for sound_data in queue:
            self._queue_sound(*sound_data)
    
    def clear_sound_queue(self) -> SoundQueue:
        queue = self.__sound_queue
        self.__sound_queue = []
        # if len(queue) > pg.mixer.get_num_channels():
        #     raise OverflowError("Too many sounds in queue")
        return queue