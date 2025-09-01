import pygame as pg

from custom_types import Animation

from file_processing import assets



class TitleText:
    __texture_map_name = "ui_elements"
    __animations_path = "ui_elements.animation"
    
    def __init__(self, corner_pos: pg.typing.Point, animation_name: str):
        self.corner_pos = pg.Vector2(corner_pos)
        self.__texture_map = assets.load_texture_map(self.__texture_map_name)
        self.__animations = {}

        for name, anim_data in assets.load_animations(self.__animations_path)["animations"].items():
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
        surface.blit(self.__get_texture(lerp_amount), self.corner_pos)