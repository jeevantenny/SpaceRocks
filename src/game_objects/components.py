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
        self._velocity = vector_min(self._velocity, unit_vector(self._velocity)*self._max_speed)



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


    def get_lerp_pos(self, lerp_amount=0.0) -> pg.Vector2:
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


    
    def draw(self, surface: pg.Surface, lerp_amount=0.0, offset: pg.typing.Point = (0, 0), rotation=0) -> None:
        blit_texture = self._get_blit_texture(lerp_amount, rotation)
        center = self._get_blit_pos(offset, lerp_amount)
        blit_pos = center - pg.Vector2(blit_texture.get_size())*0.5
        surface.blit(blit_texture, blit_pos)

        if debug.Cheats.show_bounding_boxes:
            pg.draw.line(surface, "white", center, center+self.get_rotation_vector()*10)
        
        super().draw(surface, lerp_amount, offset)


    
    def _get_blit_texture(self, lerp_amount=0.0, rotation=0) -> pg.Surface:
        return pg.transform.rotate(self.texture, -(self._rotation-self._angular_vel*(1-lerp_amount)) - rotation)
    

    def _get_blit_pos(self, offset: pg.typing.Point, lerp_amount=0.0) -> pg.Vector2:
        "Returns the center position of the texture/frame to be blit."
        if isinstance(self, ObjectVelocity):
            return self.get_lerp_pos(lerp_amount) + offset
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

        self.__texture_map = assets.load_texture_map(self.__texture_map_path, self._palette_swap)
        self.__controller = AnimController(
            assets.load_anim_controller_data(self.__controller_path),
            Animation.load_from_dict(assets.load_anim_data(self.__anim_path))
        )


    @property
    def animations_complete(self) -> bool:
        "Returns True if all animations in the current animation controller state are complete."
        return self.__controller.animations_complete



    def update(self):
        super().update()
        self._update_animations()


    def _update_animations(self):
        self.__controller.update(self)

    
    def _advance_animation(self, amount: float) -> None:
        self.__controller.advance_animations(amount)

    def _skip_animation_to_end(self) -> None:
        self.__controller.skip_to_end()


    
    def _do_transition(self) -> None:
        "Moves animation controller to correct state."
        self.__controller.do_transitions(self)
    


    def _get_blit_texture(self, lerp_amount=0, rotation=0):
        self.texture = self.__controller.get_frame(self.__texture_map, lerp_amount)
        return super()._get_blit_texture(lerp_amount, rotation)
    
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



    def draw(self, surface: pg.Surface, lerp_amount=0.0, offset: pg.typing.Point = (0, 0), rotation=0) -> str | None:
        super().draw(surface, lerp_amount, offset, rotation)
        if debug.Cheats.show_bounding_boxes:
            self._draw_rect(self.rect, "orange", surface, lerp_amount, offset)


    def _draw_rect(
            self,
            rect: pg.typing.RectLike,
            color: pg.typing.ColorLike,
            surface: pg.Surface,
            lerp_amount=0.0,
            offset=(0, 0)) -> None:

        blit_rect = rect.copy()
        if isinstance(self, ObjectVelocity):
            blit_rect.center = self.get_lerp_pos(lerp_amount)+offset
        pg.draw.rect(surface, color, blit_rect, 1)

    


    def _set_hitbox_size(self, size: pg.typing.Point):
        self.__hitbox_size = tuple(size)






class ObjectCollision(ObjectVelocity):
    "Allows object to collide with and bounce of other game objects."

    speed_bias = 0.5

    def __init__(self, *, radius: int, bounce=0.0, **kwargs):
        super().__init__(**kwargs)

        self.__radius = radius
        self.__bounce = bounce*0.5


    @property
    def radius(self) -> int:
        return self.__radius


    def update(self) -> None:
        super().update()
        self.process_collision()


    def draw(self, surface, lerp_amount=0, offset=(0, 0), rotation=0):
        super().draw(surface, lerp_amount, offset, rotation)
        if debug.Cheats.show_bounding_boxes:
            pg.draw.circle(surface, "red", self.get_lerp_pos(lerp_amount)+offset, self.__radius, 1)

    

    def colliding_objects(self) -> Generator["ObjectCollision", Any, None]:
        "Returns all game collision objects in the primary group that collide with this object."
        for obj in self.primary_group:
            if (obj is not self
                and isinstance(obj, ObjectCollision)
                and obj.do_collision()
                and self.collides_with(obj)):
                yield obj


    def collides_with(self, other: "ObjectCollision") -> bool:
        if isinstance(other, ObjectCollision):
            return (other.position-self.position).magnitude_squared() < (other.radius+self.radius)**2
        else:
            raise TypeError(f"Other object must be of type {ObjectCollision.__name__} not {type(other).__name__}")
    

    def process_collision(self) -> None:
        for other_obj in self.colliding_objects():
            prev_position = self.position.copy()
            normal: pg.Vector2 = self.position-other_obj.position
            normal.scale_to_length(self.radius+other_obj.radius)

            speed = (self.get_speed() + other_obj.get_speed())*0.5

            self.process_collision_internal(other_obj.position, speed, normal)
            other_obj.process_collision_internal(prev_position, speed, -normal)
            other_obj.on_collide(self)

            self.on_collide(other_obj)
            break

        super().process_collision()


    def process_collision_internal(self, other_pos: pg.Vector2, speed: float, normal: pg.Vector2) -> None:
        self.position = other_pos + normal
        try:
            self._velocity.scale_to_length(speed*self.__bounce)
            self._velocity.reflect_ip(normal)
        except ValueError:
            # If the magnitude of velocity is very small the scale_to_length function
            # raises a ValueError saying that it can't scale a zero vector
            self.clear_velocity()


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