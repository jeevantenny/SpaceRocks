import pygame as pg
from typing import Callable, Generator, Any
from time import sleep

from custom_types import AnimData, ControllerData, Animation, AnimController
from math_functions import unit_vector, vector_min

from . import GameObject

import debug






__all__ = [
    "ObjectComponent",
    "ObjectVelocity",
    "ObjectTexture",
    "ObjectAnimation",
    "ObjectHitbox",
    "ObjectCollision",
    "BorderCollision"
]



class ObjectComponent(GameObject):
    "Object components give Game Objects special properties."


    add_methods: list[Callable] = []
    dependencies: list[type["ObjectComponent"]] = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)










class ObjectVelocity(ObjectComponent):
    "Allows game objects to have a velocity."

    _max_speed = 100

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._velocity = pg.Vector2(0, 0)



    def get_data(self):
        return super().get_data() | {"velocity": tuple(self._velocity)}

    
    @property
    def speed(self) -> float:
        return self._velocity.magnitude()



    def update(self) -> None:
        super().update()
        self.move(self._velocity)
        self._velocity = (vector_min(self._velocity, unit_vector(self._velocity)*self._max_speed))



    def get_velocity(self) -> pg.Vector2:
        return self._velocity.copy()

    def set_velocity(self, value: pg.typing.Point) -> None:
        self._velocity = pg.Vector2(value)

    def clear_velocity(self) -> None:
        self.set_velocity((0, 0))


    def accelerate(self, value: pg.typing.Point) -> None:
        self._velocity += pg.Vector2(value)










class ObjectTexture(ObjectComponent):
    "Gives an object a visible texture."

    draw_layer = 0

    def __init__(self, *, texture: pg.Surface, **kwargs):
        super().__init__(**kwargs)

        self.texture = texture
        self.__rotation = 0
        self._angular_vel = 0


    def get_data(self):
        return super().get_data() | {"rotation": self.__rotation,
                                     "angular_vel": self._angular_vel}


    @property
    def rotation(self) -> int:
        return self.__rotation
    @rotation.setter
    def rotation(self, value: int) -> None:
        value = value%360
        if value > 180:
            value -= 360
        
        self.__rotation = value


    def set_angular_vel(self, amount: float) -> None:
        self._angular_vel = amount


    def rotate(self, amount: float) -> None:
        self.rotation += amount

    def get_rotation_vector(self) -> pg.Vector2:
        return pg.Vector2(0, -1).rotate(self.rotation)
    
    def get_lerp_rotation_vector(self, lerp_amount=0.0) -> pg.Vector2:
        return pg.Vector2(0, -1).rotate(self.rotation-self._angular_vel*(1-lerp_amount))

    def set_rotation(self, value: float) -> None:
        self.rotation = value
        

    def update(self) -> None:
        super().update()
        self.rotate(self._angular_vel)


    
    def draw(self, surface: pg.Surface, lerp_amount=0.0, offset: pg.typing.Point = (0, 0)) -> None:
        blit_texture = self._get_blit_texture(lerp_amount)
        lerp_pos = self._get_lerp_pos(lerp_amount) + offset
        blit_pos = lerp_pos - pg.Vector2(blit_texture.get_size())*0.5
        surface.blit(blit_texture, blit_pos)

        if debug.debug_mode:
            pg.draw.line(surface, "white", lerp_pos, lerp_pos+self.get_rotation_vector()*10)
        
        super().draw(surface, lerp_amount, offset)


    
    def _get_blit_texture(self, lerp_amount=0.0) -> pg.Surface:
        return pg.transform.rotate(self.texture, -(self.rotation-self._angular_vel*(1-lerp_amount)))


    def _get_lerp_pos(self, lerp_amount=0.0) -> pg.Vector2:
        lerp_pos = self.position.copy()
        if isinstance(self, ObjectVelocity):
            lerp_pos -= self._velocity*(1-lerp_amount)
        
        return lerp_pos
    


        












class ObjectAnimation(ObjectTexture):
    _anim_data_dir = "assets/animations"
    _controller_data_dir = "assets/anim_controllers"

    def __init__(self, *, texture_map: dict[str, pg.Surface], anim_data: dict[str, str | dict[str, AnimData]], controller_data: ControllerData, **kwargs):
        super().__init__(texture=None, **kwargs)

        self.__texture_map = texture_map
        animations = {}
        for name, data in anim_data["animations"].items():
            animations[name] = Animation(name, data)

        self.__controller = AnimController(controller_data, animations)


    def update(self):
        super().update()
        self.update_animations()


    def update_animations(self):
        self.__controller.update(self)


    @property
    def animations_complete(self) -> bool:
        return self.__controller.animations_complete
    


    def _get_blit_texture(self, lerp_amount=0):
        self.texture = self.__controller.get_frame(self.__texture_map, lerp_amount)
        return super()._get_blit_texture(lerp_amount)
    












class ObjectHitbox(ObjectComponent):
    draw_layer = 0

    def __init__(self, *, hitbox_size: pg.typing.Point, **kwargs):
        super().__init__(**kwargs)
        self.__hitbox_size = tuple(hitbox_size)


    def get_data(self):
        return super().get_data() | {"hitbox": self.__hitbox_size}


    @property
    def rect(self) -> pg.FRect:
        rect = pg.FRect(0, 0, *self.__hitbox_size)
        rect.center = self.position
        return rect
    

    def colliding_objects(self) -> Generator[GameObject, Any, None]:
        for obj in self.primary_group:
            if obj is not self and isinstance(obj, ObjectCollision) and obj.do_collision() and self.rect.colliderect(obj.rect):
                yield obj



    def draw(self, surface: pg.Surface, lerp_amount=0.0, offset: pg.typing.Point = (0, 0)) -> str | None:
        super().draw(surface, lerp_amount, offset)
        if debug.debug_mode:
            blit_rect: pg.Rect = self.rect
            if isinstance(self, ObjectVelocity):
                rect_center = self.position - self.get_velocity()*(1-lerp_amount)
                blit_rect.center = rect_center+offset
            pg.draw.rect(surface, "red", blit_rect, 1)






class ObjectCollision(ObjectHitbox, ObjectVelocity):
    "Gives objects a hitbox which can be used for collision."

    speed_bias = 0.5

    def __init__(self, *, bounce=0.0, **kwargs):
        super().__init__(**kwargs)

        self.__bounce = bounce*0.5


    def get_data(self):
        return super().get_data() | {"Obj_coll_bounce": self.__bounce}


    def update(self) -> None:
        super().update()
        self.process_collision()
    


    def get_side_contacts(self) -> dict[str, bool]:
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
        "Called when entity collides with another entity"
        pass


    def do_collision(self) -> bool:
        return True









class BorderCollision(ObjectHitbox, ObjectVelocity):


    def __init__(self, *, bounding_area: pg.typing.RectLike, border_bounce=0.0, **kwargs):
        super().__init__(**kwargs)

        self.__bounding_area = pg.Rect(bounding_area)
        self.__bounce = border_bounce


    def get_data(self):
        return super().get_data() | {"bord_coll_bounce": self.__bounce,
                                     "bounding_topleft": self.__bounding_area.topleft,
                                     "bounding_bottomright": self.__bounding_area.bottomright}


    def get_bounding_area(self) -> None:
       return self.__bounding_area.copy()


    def set_bounding_area(self, area: pg.typing.RectLike) -> None:
        self.__bounding_area = pg.Rect(area)


    def update(self):
        super().update()
        if not isinstance(self, ObjectCollision):
            self.process_collision()


    def process_collision(self) -> None:
        super().process_collision()
        obj_rect: pg.Rect = self.rect
        prev_vel = self._velocity.copy()

        if obj_rect.left <= self.__bounding_area.left and self._velocity.x < 0:
            obj_rect.left = self.__bounding_area.left
            self._velocity.x = abs(self._velocity.x*self.__bounce)
        
        if obj_rect.right >= self.__bounding_area.right and self._velocity.x > 0:
            obj_rect.right = self.__bounding_area.right
            self._velocity.x = -abs(self._velocity.x*self.__bounce)
        
        if obj_rect.top <= self.__bounding_area.top and self._velocity.y < 0:
            obj_rect.top = self.__bounding_area.top
            self._velocity.y = abs(self._velocity.y*self.__bounce)
        
        if obj_rect.bottom >= self.__bounding_area.bottom and self._velocity.y > 0:
            obj_rect.bottom = self.__bounding_area.bottom
            self._velocity.y = -abs(self._velocity.y*self.__bounce)

        
        if prev_vel.x != self._velocity.x:
            self.on_collide("vertical_border")
        elif prev_vel.y != self._velocity.y:
            self.on_collide("horizontal_border")

        self.position = pg.Vector2(obj_rect.center)




    def on_collide(self, collided_with) -> None:
        pass