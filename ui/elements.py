import pygame as pg

from custom_types import TextureMap, Animation

from file_processing import assets

from . import blit_to_center, font





class TitleText:
    __effect_mask_colors = assets.load_json("assets/title_effect_mask_colors")
    def __init__(self, text: str, effect_name: str) -> None:
        self.__texture_map = self.__make_title_effect("title_effect_1", font.title_font.render(text))
        self.set_effect(effect_name)


    @property
    def animations_complete(self) -> bool:
        return self.__animation.complete

    
    def update(self):
        self.__animation.update()
    

    def render(self, lerp_amount=0.0) -> pg.Surface:
        return self.__animation.get_frame(self.__texture_map, lerp_amount)
    

    def set_effect(self, effect_name: str) -> None:
        self.__animation = Animation("main_entrance_a", assets.load_anim_data("ui_elements")["animations"][effect_name])
        self.__animation.restart()


    def __make_title_effect(self, path: str, title_surface: pg.Surface) -> TextureMap:
        texture_map = assets.load_texture_map(path).copy()

        for name, surface in texture_map.items():
            if name == "main":
                texture_map[name] = title_surface
                continue

            surface = pg.transform.scale(surface, title_surface.size)
            texture_map[name] = self.__apply_masks(surface, title_surface)
        
        texture_map["blank"] = assets.colorkey_surface((1, 1))
        
        return texture_map
    

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