"Contains components that game objects can inherit from to gain specific properties."

import pygame as pg
from typing import Generator, Any

import debug

from src.custom_types import Animation, AnimController
from src.math_functions import unit_vector, vector_min, format_angle

from src.file_processing import assets

from . import GameObject






__all__ = [
    "ObjectVelocity",
    "ObjectTexture",
    "ObjectAnimation",
    "ObjectHitbox",
    "ObjectCollision"
]










class ObjectVelocity(GameObject):
    "Allows game objects to have a velocity."

    _max_speed = 100

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._velocity = pg.Vector2(0, 0)




    def update(self) -> None:
        super().update()
        self.move(self._velocity)
        self._velocity = (vector_min(self._velocity, unit_vector(self._velocity)*self._max_speed))



    def get_velocity(self) -> pg.Vector2:
        return self._velocity.copy()

    def set_velocity(self, value: pg.typing.Point) -> None:
        self._velocity = pg.Vector2(value)

    
    def get_speed(self) -> float:
        return self._velocity.magnitude()

    def clear_velocity(self) -> None:
        self.set_velocity((0, 0))


    def accelerate(self, value: pg.typing.Point) -> None:
        self._velocity += pg.Vector2(value)


    def _get_lerp_pos(self, lerp_amount=0.0) -> pg.Vector2:
        return self.position - self._velocity*(1-lerp_amount)










class ObjectTexture(GameObject):
    "Gives an object a visible texture."

    draw_layer = 0

    def __init__(self, *, texture: pg.Surface, **kwargs):
        super().__init__(**kwargs)

        self.texture = texture
        self.__rotation = 0
        self._angular_vel = 0



    @property
    def _rotation(self) -> int:
        "Rotation of game object ranging from -179 to 180."
        return self.__rotation
    @_rotation.setter
    def _rotation(self, value: int) -> None:
        self.__rotation = int(format_angle(value))


    def set_angular_vel(self, amount: float) -> None:
        self._angular_vel = amount


    def rotate(self, amount: float) -> None:
        self._rotation += amount

    def get_rotation(self) -> int:
        return self._rotation

    def set_rotation(self, value: int) -> None:
        self._rotation = value

    def get_rotation_vector(self) -> pg.Vector2:
        "Gets rotation of object as a vector relative to (0, -1)."
        return pg.Vector2(0, -1).rotate(self._rotation)
    
    def get_lerp_rotation_vector(self, lerp_amount=0.0) -> pg.Vector2:
        "Gets rotation vector taking account interpolation."
        return pg.Vector2(0, -1).rotate(self._rotation-self._angular_vel*(1-lerp_amount))
        

    def update(self) -> None:
        super().update()
        self.rotate(self._angular_vel)


    
    def draw(self, surface: pg.Surface, lerp_amount=0.0, offset: pg.typing.Point = (0, 0)) -> None:
        blit_texture = self._get_blit_texture(lerp_amount)
        center = self._get_blit_pos(offset, lerp_amount)
        blit_pos = center - pg.Vector2(blit_texture.get_size())*0.5
        surface.blit(blit_texture, blit_pos)

        if debug.debug_mode:
            pg.draw.line(surface, "white", center, center+self.get_rotation_vector()*10)
        
        super().draw(surface, lerp_amount, offset)


    
    def _get_blit_texture(self, lerp_amount=0.0) -> pg.Surface:
        return pg.transform.rotate(self.texture, -(self._rotation-self._angular_vel*(1-lerp_amount)))
    

    def _get_blit_pos(self, offset: pg.typing.Point, lerp_amount=0.0) -> pg.Vector2:
        "Returns the center position of the texture/frame to be blit."
        if isinstance(self, ObjectVelocity):
            return self._get_lerp_pos(lerp_amount) + offset
        else:
            return self.position + offset

    


        












class ObjectAnimation(ObjectTexture):
    "Gives objects a set of animations controller by an animation controller."

    _anim_data_dir = "assets/animations"
    _controller_data_dir = "assets/anim_controllers"

    def __init__(self, *,
                 texture_map_path: str,
                 anim_path: str,
                 controller_path: str,
                 palette_swap: str | None = None,
                 **kwargs):

        super().__init__(texture=None, **kwargs)

        self.__texture_map_path = texture_map_path
        self.__anim_path = anim_path
        self.__controller_path = controller_path
        self._palette_swap = palette_swap

        self.__init_base()




    def __init_base(self) -> None:
        self.__texture_map = assets.load_texture_map(self.__texture_map_path, self._palette_swap)

        anim_data = assets.load_anim_data(self.__anim_path)
        animations = {}
        for name, data in anim_data["animations"].items():
            animations[name] = Animation(name, data)

        self.__controller = AnimController(assets.load_anim_controller_data(self.__controller_path), animations)


    @property
    def animations_complete(self) -> bool:
        "Returns True if all animations in the current animation controller state are complete."
        return self.__controller.animations_complete



    def update(self):
        super().update()
        self._update_animations()


    def _update_animations(self):
        self.__controller.update(self)


    
    def _do_transition(self) -> None:
        "Moves animation controller to correct state."
        self.__controller.do_transitions(self)
    


    def _get_blit_texture(self, lerp_amount=0):
        self.texture = self.__controller.get_frame(self.__texture_map, lerp_amount)
        return super()._get_blit_texture(lerp_amount)
    
    def _set_anim_state(self, state_name: str) -> None:
        self.__controller.set_state(state_name)
    












class ObjectHitbox(GameObject):
    "Gives objects a hitbox that can be used to perform collision checks."
    draw_layer = 0

    def __init__(self, *, hitbox_size: pg.typing.Point, **kwargs):
        super().__init__(**kwargs)
        self._set_hitbox_size(hitbox_size)



    @property
    def rect(self) -> pg.FRect:
        rect = pg.FRect(0, 0, *self.__hitbox_size)
        rect.center = self.position
        return rect
    

    def colliderect(self, rect: pg.typing.RectLike) -> bool:
        return self.rect.colliderect(rect)
    

    def overlapping_objects(self) -> Generator["ObjectHitbox", Any]:
        "Returns a generator all objects in primary group whose hitbox overlaps with this objects's."
        for obj in self.primary_group:
            if obj is not self and isinstance(obj, ObjectHitbox) and self.colliderect(obj.rect):
                yield obj



    def draw(self, surface: pg.Surface, lerp_amount=0.0, offset: pg.typing.Point = (0, 0)) -> str | None:
        super().draw(surface, lerp_amount, offset)
        if debug.debug_mode:
            blit_rect: pg.Rect = self.rect
            if isinstance(self, ObjectVelocity):
                blit_rect.center = self._get_lerp_pos(lerp_amount)+offset
            pg.draw.rect(surface, "red", blit_rect, 1)
    


    def _set_hitbox_size(self, size: pg.typing.Point):
        self.__hitbox_size = tuple(size)






class ObjectCollision(ObjectHitbox, ObjectVelocity):
    "Allows object to collide with and bounce of other game objects."

    speed_bias = 0.5

    def __init__(self, *, bounce=0.0, **kwargs):
        super().__init__(**kwargs)

        self.__bounce = bounce*0.5



    def update(self) -> None:
        super().update()
        self.process_collision()

    

    def colliding_objects(self) -> Generator[GameObject, Any, None]:
        "Returns all game collision objects in the primary group that collide with this object."
        for obj in self.overlapping_objects():
            if isinstance(obj, ObjectCollision) and obj.do_collision():
                yield obj
    


    def get_side_contacts(self) -> dict[str, bool]:
        "Returns which sides of the hitbox are in contact with other game objects."
        output = {"top": False, "bottom": False, "left": False, "right": False}

        obj_rect = self.rect
        
        if self.primary_group is None:
            return None
        
        for other_obj in self.primary_group.sprites():
            if other_obj is not self and isinstance(other_obj, ObjectCollision):

                rect = other_obj.rect
                if obj_rect.right > rect.left and obj_rect.left < rect.right:
                    if obj_rect.top == rect.bottom:
                        output["top"] = True
                    if obj_rect.bottom == rect.top:
                        output["bottom"] = True
                        
                if obj_rect.bottom > rect.top and obj_rect.top < rect.bottom:
                    if obj_rect.left == rect.right:
                        output["left"] = True
                    if obj_rect.right == rect.left:
                        output["right"] = True
        
        return output



    def process_collision(self) -> None:
        "Processes collision for one game tick."
        obj_rect = self.rect
        prev_pos: pg.Vector2 = self.position - self._velocity


        def set_change(change: float | None, new_value: float) -> float:
            if change is None or abs(new_value) < abs(change):
                return new_value
            else:
                return change

        y_change = None
        x_change = None
        resultant_vel = pg.Vector2(0, 0)
        
        if self.primary_group is None:
            return None
        
        for other_obj in self.colliding_objects():
            rect: pg.Rect = other_obj.rect
            other_obj_vel: pg.Vector2 = other_obj.get_velocity()
            resultant_vel = self._velocity - other_obj_vel

            if x_change is None and y_change is None:
                self.on_collide(other_obj)
            
            if obj_rect.colliderect(rect):
                
                if resultant_vel.y != 0:
                    y_change = min(
                        set_change(y_change, rect.top-obj_rect.bottom),
                        set_change(y_change, rect.bottom-obj_rect.top),
                        key=lambda x: abs(x)
                    )
                
                if resultant_vel.x != 0:
                    x_change = min(
                        set_change(x_change, rect.left-obj_rect.right),
                        set_change(x_change, rect.right-obj_rect.left),
                        key=lambda x: abs(x)
                    )

                if x_change:
                    other_obj_vel.x += self._velocity.x*self.__bounce
                if y_change:
                    other_obj_vel.y += self._velocity.y*self.__bounce

                other_obj.set_velocity(other_obj_vel)
                other_obj.move(other_obj_vel)
        

        if x_change:
            option_x: pg.Vector2 = self.position + pg.Vector2(x_change, 0)
        
        if y_change:
            option_y: pg.Vector2 = self.position + pg.Vector2(0, y_change)
        
        if y_change and (not x_change or (prev_pos-option_y).magnitude() < (prev_pos-option_x).magnitude()):
            self.position.y += y_change
            self._velocity.y = -self._velocity.y*self.__bounce
        elif x_change:
            self.position.x += x_change
            self._velocity.x = -self._velocity.x*self.__bounce
        
        
        super().process_collision()






    def on_collide(self, collided_with) -> None:
        "Used to perform an action upon collision."
        pass


    def do_collision(self) -> bool:
        return True






class ObjectHealth(GameObject):
    def __init__(self, *, max_health: int, **kwargs):
        super().__init__(**kwargs)

        self.__health, self.__max_health = max_health

    
    @property
    def health(self) -> int:
        return self.__health

    
    def damage(self, amount: int) -> None:
        self.__health -= min(self.__health, amount)
    
    def heal(self, amount: int) -> None:
        self.health = min(self.health+amount, self.__max_health)