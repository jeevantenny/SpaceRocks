import pygame as pg

from src.custom_types import TextureMap, Animation
from src.file_processing import assets

from . import font





class AnimatedText:
    "Uses the title_font to render text and apply an animations on it."
    
    __effect_mask_colors = assets.load_json("assets/title_effect_mask_colors")
    __effects_file = "title_effects"

    def __init__(self, text: str, effect_name: str, font=font.title_font) -> None:
        self.__texture_map = self.__make_title_effect(font.render(text))
        self.set_effect(effect_name)


    def _get_text_surface(self, text: str) -> pg.Surface:
        return font.title_font.render(text)


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
        self.__animation = Animation(effect_name, assets.load_anim_data("title_text")["animations"][effect_name])
        self.__animation.restart()


    def __make_title_effect(self, title_surface: pg.Surface) -> TextureMap:
        texture_map = assets.load_texture_map(self.__effects_file).copy()

        for name, surface in texture_map.items():
            if name == "main":
                texture_map[name] = title_surface
                continue

            surface = pg.transform.scale(surface, title_surface.size)
            texture_map[name] = self.__apply_masks(surface, title_surface)
        
        texture_map["blank"] = assets.colorkey_surface(title_surface.size)
        
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
    



class ProgressBar:
    "Shows how much of a level the player has completed."

    def __init__(self):
        texture_map = assets.load_texture_map("ui_elements")
        self.__base_texture = texture_map["progress_bar_base"]
        self.__overlay_texture = texture_map["progress_bar_overlay"]

    
    def render(self, amount: float) -> pg.Surface:
        "Render progress bar for the given amount between 0 and 1."

        amount = pg.math.clamp(amount, 0, 1)
        output = self.__base_texture.copy()
        overlay = self.__overlay_texture.subsurface(0, 0, int(88*amount), 8)
        output.blit(overlay, (1, 1))
        return output