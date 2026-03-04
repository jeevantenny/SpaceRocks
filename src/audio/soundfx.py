"Contains stuff for playing and queueing sound effects."

import pygame as pg

from src.file_processing import assets, data


type SoundQueue = list[tuple[str, float, int]]
type LoopingSounds = dict[tuple[str, int], pg.Channel]


class SoundFXManager:
    __looping_sounds: LoopingSounds = {}

    @classmethod
    def play_sound(cls, name: str, volume=1.0, loops=0) -> pg.Channel | None:
        if pg.mixer.get_init() is not None:
            sound = assets.load_sound(name)
            return sound.play(pg.math.clamp(volume, 0, 1)*data.get_setting("soundfx_volume"), loops)



    @classmethod
    def play_sound_queue(cls, queue: SoundQueue) -> None:
        new_loop_sounds: dict[tuple[str, int], float] = {}
        for name, volume, object_id in queue:
            if object_id == 0:
                cls.play_sound(name, volume)
            else:
                new_loop_sounds[(name, object_id)] = volume
        
        for loop_id, channel in list(cls.__looping_sounds.items()):
            # If a currently looping sound should continue in next tick
            if loop_id in new_loop_sounds:
                channel.set_volume(new_loop_sounds[loop_id])
                new_loop_sounds.pop(loop_id)
            # If currently playing sound should not continue in next tick
            else:
                channel.stop()
                cls.__looping_sounds.pop(loop_id)

        for loop_id, volume in new_loop_sounds.items():
            # If a looping sound to play on next tick is not currently playing
            new_channel = cls.play_sound(loop_id[0], volume, -1)
            if new_channel is not None:
                cls.__looping_sounds[loop_id] = new_channel



    @classmethod
    def stop_looping_sounds(cls) -> None:
        "Stops all currently playing looping sounds"
        for channel in cls.__looping_sounds.values():
            channel.stop()
        cls.__looping_sounds.clear()




class HasSoundQueue:
    "Has methods for storing sounds in queue and removing theme all at once."
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__sound_queue: SoundQueue = []


    def get_sound_queue(self) -> SoundQueue:
        return self.__sound_queue.copy()


    def _queue_sound(self, sound_name: str, volume=1.0, loop=False) -> None:
        if loop:
            loop_id = id(self)
        else:
            loop_id = 0

        self.__sound_queue.append((sound_name, volume, loop_id))

    def _join_sound_queue(self, queue: SoundQueue) -> None:
        "Adds all sounds from a queue."
        for sound_data in queue:
            self._queue_sound(*sound_data)
    
    def clear_sound_queue(self) -> SoundQueue:
        queue = self.__sound_queue
        self.__sound_queue = []
        # if len(queue) > pg.mixer.get_num_channels():
        #     raise OverflowError("Too many sounds in queue")
        return queue