import pygame as pg

from custom_types import Animation

from file_processing import assets
import ui



class TitleText:
    __asset_key = "ui_elements"
    
    def __init__(self, center_offset: pg.typing.Point, animation_name: str):
        self.__center_offset = pg.Vector2(center_offset)
        self.__texture_map = assets.load_texture_map(self.__asset_key)
        self.__animations = {}

        for name, anim_data in assets.load_anim_data(self.__asset_key)["animations"].items():
            self.__animations[name] = Animation(name, anim_data)

        self.set_current_animation(animation_name)


    @property
    def __current_animation(self) -> Animation | None:
        if self.current_anim_name is not None:
            return self.__animations[self.current_anim_name]
        else:
            return None
        

    @property
    def animations_complete(self) -> bool:
        return self.__current_animation.complete
    

        


    def set_current_animation(self, name: str) -> None:
        if name in self.__animations:
            self.current_anim_name = name
            self.__current_animation.restart()
        else:
            raise ValueError(f"'{name}' is not a valid animation name.")
        
    
    def update(self) -> None:
        self.__current_animation.update()


    
    def __get_texture(self, lerp_amount=0.0) -> pg.Surface:
        return self.__current_animation.get_frame(self.__texture_map, lerp_amount)
    

    def draw(self, surface: pg.Surface, lerp_amount=0.0) -> None:
        ui.blit_to_center(self.__get_texture(lerp_amount), surface, self.__center_offset)