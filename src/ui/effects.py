import pygame as pg

from src.custom_types import TextureMap, Animation, LazyDict
from src.file_processing import assets

from . import font





class AnimatedTexture:
    "Uses the title_font to render text and apply an animations on it."
    
    __effect_mask_colors = assets.load_json("assets/title_effect_mask_colors")

    def __init__(self, texture: pg.Surface, texture_map_path: str, anim_path: str, effect_name: str) -> None:
        self.__base = texture
        self.__effect_texture_map = assets.load_texture_map(texture_map_path)
        self.__anim_data = assets.load_anim_data(anim_path)["animations"]
        self.__texture_map = LazyDict[str, pg.Surface](self.__get_frame)
        self.set_effect(effect_name)


    @property
    def animations_complete(self) -> bool:
        return self.__animation.complete

    
    def update(self):
        "Updates the animation for every game tick."
        self.__animation.update()
    

    def render(self, lerp_amount=0.0) -> pg.Surface:
        "Gets the current frame of the animations."
        return self.__animation.get_frame(self.__texture_map, lerp_amount)
    

    def get_effect_name(self) -> str:
        return self.__animation.name

    def set_effect(self, effect_name: str) -> None:
        "Sets the current animation effect to play on the text."
        self.__animation = Animation(effect_name, self.__anim_data[effect_name])
        self.__animation.restart()


    def __get_frame(self, key: str) -> pg.Surface:
        if key == "main":
            return self.__base
        effect_surface = self.__effect_texture_map.get(key)
        if effect_surface is None:
            raise KeyError(key)
        return self.__apply_masks(pg.transform.scale(effect_surface, self.__base.size), self.__base)
    

    def __apply_masks(self, effect_surface: pg.Surface, title_surface: pg.Surface) -> None:
        output_surface = title_surface.copy()
        for mask_color, data in self.__effect_mask_colors.items():
            base_mask = pg.mask.from_threshold(effect_surface, mask_color, (1, 1, 1, 255))
            base_mask.to_surface(output_surface, setcolor=data["default_color"], unsetcolor=None)
            for old_c, new_c in data.get("change_colors", {}).items():
                overlay_mask = pg.mask.from_threshold(title_surface, old_c, (1, 1, 1, 255))
                overlay_mask = overlay_mask.overlap_mask(base_mask, (0, 0))
                overlay_mask.to_surface(output_surface, setcolor=new_c, unsetcolor=None)

        return output_surface
    



class AnimatedText(AnimatedTexture):
    def __init__(self, text: str, effect_name: str, font_type=font.title_font) -> None:
        super().__init__(font_type.render(text), "title_effects", "title_text", effect_name)