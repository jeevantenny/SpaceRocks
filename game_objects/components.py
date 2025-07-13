import pygame as p
from typing import Callable

from custom_types import Coordinate
from math_functions import unit_vector

import debug





class ObjectComponent:
    "Object components give Game Objects special properties."

    # The priority of a component indicates what order component methods will be called
    # if two components have the same method.
    priority = 99

    add_methods: list[Callable] = []
    dependencies: list[type["ObjectComponent"]] = []

    def __init__(self):
        pass



    def __repr__(self) -> str:
        return f"{type(self).__name__}()"







class ObjectVelocity(ObjectComponent):
    "Allows game objects to have a velocity."

    priority = 5

    def __init__(self) -> None:
        super().__init__()
        self.velocity = p.Vector2(0, 0)

        self.add_methods = [self.update, self.get_velocity, self.set_velocity, self.accelerate]



    def update(self, obj) -> None:
        obj.move(self.velocity)


    def get_velocity(self, obj) -> None:
        "Returns the velocity for object"
        return self.velocity.copy()
    
    def set_velocity(self, obj, value: Coordinate) -> None:
        self.velocity = p.Vector2(value)
    

    def accelerate(self, obj, value: Coordinate) -> None:
        self.velocity += p.Vector2(value)









class ObjectTexture(ObjectComponent):
    "Gives an object a visible texture."

    priority = 4

    def __init__(self, texture: p.Surface):
        super().__init__()

        self.texture = texture
        self.size = texture.get_size()
        self.rotation = 0
        self.angular_vel = 0

        self.add_methods = [
            self.rotate,
            self.get_rotation,
            self.get_rotation_vector,
            self.set_rotation,
            self.set_angular_vel,
            self.update,
            self.draw
        ]




    def rotate(self, obj, amount: float) -> None:
        self.rotation += amount

    def get_rotation(self, obj) -> float:
        return self.rotation
    
    def get_rotation_vector(self, obj) -> p.Vector2:
        return p.Vector2(0, -1).rotate(self.rotation) 

    def set_rotation(self, obj, value: float) -> None:
        self.rotation = value

    def set_angular_vel(self, obj, value: float) -> None:
        self.angular_vel = value



    def update(self, obj) -> None:
        self.rotate(obj, self.angular_vel)


    
    def draw(self, obj, surface: p.Surface, lerp_amount=0.0) -> None:
        blit_texture = p.transform.rotate(self.texture, -(self.rotation-self.angular_vel*(1-lerp_amount)))
        lerp_pos = obj.position.copy()
        if obj.has_component(ObjectVelocity):
            lerp_pos -= obj.get_velocity()*(1-lerp_amount)
        
        blit_pos = lerp_pos - p.Vector2(blit_texture.get_size())*0.5
        surface.blit(blit_texture, blit_pos)

        if debug.debug_mode:
            p.draw.line(surface, "white", lerp_pos, lerp_pos+self.get_rotation_vector(obj)*10)







class ObjectCollision(ObjectComponent):
    "Gives objects a hitbox which can be used for collision."

    dependencies = [ObjectVelocity]
    priority = 6
    speed_bias = 0.5

    def __init__(self, size: Coordinate, bounce=0.0):
        super().__init__()

        self.size = tuple(size)
        from . import GameObject
        self.GameObjectType = GameObject
        self.bounce = bounce*0.5

        self.add_methods = [
            self.update,
            self.get_rect,
            self.get_side_contacts,
            self.process_collision,
            self.draw
        ]



    def update(self, obj) -> None:
        obj.process_collision()

    
    def get_rect(self, obj) -> p.FRect:
        rect = p.FRect(0, 0, *self.size)
        rect.center = obj.position
        return rect
    


    def get_side_contacts(self, obj) -> dict[str, bool]:
        output = {"top": False, "bottom": False, "left": False, "right": False}

        obj_rect = self.get_rect(obj)
        
        if obj.group is None:
            return None
        
        for other_obj in obj.group.sprites():
            if other_obj is not obj and other_obj.has_component(ObjectCollision):

                rect = other_obj.get_rect()
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



    def process_collision(self, obj) -> None:
        obj_rect: p.Rect = self.get_rect(obj)
        obj_velocity: p.Vector2 = obj.get_velocity()
        prev_pos: p.Vector2 = obj.position - obj_velocity


        def set_change(change: float | None, new_value: float) -> float:
            if change is None or abs(new_value) < abs(change):
                return new_value
            else:
                return change

        y_change = None
        x_change = None
        resultant_vel = p.Vector2(0, 0)
        
        if obj.group is None:
            return None
        
        for other_obj in obj.group.sprites():
            if other_obj is not obj and other_obj.has_component(ObjectCollision):
                rect: p.Rect = other_obj.get_rect()
                other_obj_vel: p.Vector2 = other_obj.get_velocity()
                resultant_vel = obj_velocity - other_obj_vel
                
                if obj_rect.colliderect(rect):
                    if resultant_vel.y > 0:
                        y_change = set_change(y_change, rect.top-obj_rect.bottom)
                    elif resultant_vel.y < 0:
                        y_change = set_change(y_change, rect.bottom-obj_rect.top)

                    if resultant_vel.x > 0:
                        x_change = set_change(x_change, rect.left-obj_rect.right)
                    elif resultant_vel.x < 0:
                        x_change = set_change(x_change, rect.right-obj_rect.left)

                    if x_change:
                        other_obj_vel.x += obj_velocity.x*self.bounce
                    if y_change:
                        other_obj_vel.y += obj_velocity.y*self.bounce

                    other_obj.set_velocity(other_obj_vel)
                    other_obj.move(other_obj_vel)
        

        if x_change:
            option_x: p.Vector2 = obj.position + p.Vector2(x_change, 0)
        
        if y_change:
            option_y: p.Vector2 = obj.position + p.Vector2(0, y_change)
        
        if y_change and (not x_change or (prev_pos-option_y).magnitude() < (prev_pos-option_x).magnitude()):
            obj.position.y += y_change
            obj_velocity.y = -obj_velocity.y*self.bounce
        elif x_change:
            obj.position.x += x_change
            obj_velocity.x = -obj_velocity.x*self.bounce

        obj.set_velocity(obj_velocity)



    def draw(self, obj, surface: p.Surface, lerp_amount=0.0):
        blit_rect: p.Rect = obj.get_rect()
        rect_center = obj.position - obj.get_velocity()*(1-lerp_amount)
        blit_rect.center = rect_center

        if debug.debug_mode and obj.has_component(ObjectCollision):
            p.draw.rect(surface, "red", blit_rect, 1)









class BorderCollision(ObjectComponent):

    dependencies = [ObjectVelocity]

    def __init__(self, area: p.typing.RectLike, bounce=0.0):
        super().__init__()

        self.bounding_area = p.Rect(area)
        self.bounce = bounce

        self.add_methods = [self.get_bounding_area, self.set_bounding_area, self.process_collision]



    def get_bounding_area(self, obj) -> None:
       return self.bounding_area.copy()


    def set_bounding_area(self, obj, area: p.typing.RectLike) -> None:
        self.bounding_area = p.Rect(area)


    def process_collision(self, obj) -> None:
        obj_vel: p.Vector2 = obj.get_velocity()
        obj_rect: p.Rect = obj.get_rect()

        if obj_rect.left <= self.bounding_area.left and obj_vel.x < 0:
            obj_rect.left = self.bounding_area.left
            obj_vel.x = abs(obj_vel.x*self.bounce)
        
        if obj_rect.right >= self.bounding_area.right and obj_vel.x > 0:
            obj_rect.right = self.bounding_area.right
            obj_vel.x = -abs(obj_vel.x*self.bounce)
        
        if obj_rect.top <= self.bounding_area.top and obj_vel.y < 0:
            obj_rect.top = self.bounding_area.top
            obj_vel.y = abs(obj_vel.y*self.bounce)
        
        if obj_rect.bottom >= self.bounding_area.bottom and obj_vel.y > 0:
            obj_rect.bottom = self.bounding_area.bottom
            obj_vel.y = -abs(obj_vel.y*self.bounce)

        obj.position = p.Vector2(obj_rect.center)
        obj.set_velocity(obj_vel)
