import pygame as p
from typing import Callable

from custom_types import Coordinate

from debug import DEBUG





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
        self.velocity += value




class ObjectGravity(ObjectComponent):

    dependencies = [ObjectVelocity]
    priority = 4


    def __init__(self, value=(0, 5)):
        super().__init__()

        self.value = p.Vector2(value)

        self.add_methods = [self.update, self.set_gravity]



    def set_gravity(self, obj, value) -> None:
        self.value = p.Vector2(value)


    
    def update(self, obj) -> None:
        if not (obj.has_component(ObjectGravity) and obj.get_side_contacts()["bottom"]):
            obj.accelerate(self.value)






class ObjectTexture(ObjectComponent):
    "Gives an object a visible texture."

    priority = 4

    def __init__(self, texture: p.Surface):
        super().__init__()

        self.texture = texture
        self.size = texture.get_size()
        self.rotation = 0

        self.add_methods = [self.rotate, self.get_rotation, self.set_rotation, self.draw]




    def rotate(self, obj, amount: float) -> None:
        self.rotation += amount

    def get_rotation(self, obj) -> float:
        return self.rotation
    
    def get_rotation_vector(self, obj) -> p.Vector2:
        return p.Vector2(0, -1).rotate(self.rotation) 

    def set_rotation(self, obj, value: float) -> None:
        self.rotation = value


    
    def draw(self, obj, surface: p.Surface, lerp_amount=0.0) -> None:
        blit_texture = p.transform.rotate(self.texture, -self.rotation)
        lerp_pos = obj.position.copy()
        if obj.has_component(ObjectVelocity):
            lerp_pos -= obj.get_velocity()*(1-lerp_amount)
        
        blit_pos = lerp_pos - p.Vector2(blit_texture.get_size())*0.5
        surface.blit(blit_texture, blit_pos)

        if DEBUG:
            p.draw.line(surface, "white", lerp_pos, lerp_pos+self.get_rotation_vector(obj)*10)







class ObjectCollision(ObjectComponent):
    "Gives objects a hitbox which can be used for collision."

    dependencies = [ObjectVelocity]
    priority = 6
    speed_bias = 0.1

    def __init__(self, size: Coordinate, collision_objects: list[p.typing.RectLike] = []):
        super().__init__()

        self.size = tuple(size)
        from . import GameObject
        self.GameObjectType = GameObject
        self.collision_objects: list[p.typing.RectLike | GameObject] = collision_objects

        self.add_methods = [
            self.update,
            self.get_rect,
            self.collision_effected,
            self.get_side_contacts,
            self.process_collision,
            self.draw
        ]



    def update(self, obj) -> None:
        obj.process_collision()

    
    def collision_effected(self, obj) -> bool:
        return bool(self.collision_objects)

    
    def get_rect(self, obj) -> p.FRect:
        rect = p.FRect(0, 0, *self.size)
        rect.center = obj.position
        return rect
    


    def get_side_contacts(self, obj) -> dict[str, bool]:
        output = {"top": False, "bottom": False, "left": False, "right": False}

        obj_rect = self.get_rect(obj)
        for other_obj in self.collision_objects:
            if other_obj is not self and isinstance(other_obj, self.GameObjectType):
                if other_obj.has_component(ObjectCollision):
                    rect = other_obj.get_rect()
                else:
                    raise ValueError("Game object without Object Collision cannot be used with collision check")
            else:
                rect = other_obj

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
        obj_rect = self.get_rect(obj)
        obj_velocity: p.Vector2 = obj.get_velocity()


        def set_change(change: float | None, new_value: float) -> float:
            if change is None or abs(new_value) < abs(change):
                return new_value
            else:
                return change

        y_change = None
        x_change = None
        resultant_vel = p.Vector2(0, 0)
        for other_obj in self.collision_objects:
            if isinstance(other_obj, self.GameObjectType):
                if other_obj.has_component(ObjectCollision):
                    rect = other_obj.get_rect()
                    resultant_vel = obj_velocity - other_obj.get_velocity()
                else:
                    raise ValueError("Game object without Object Collision cannot be used with collision check")
            else:
                rect = other_obj
                resultant_vel = obj_velocity
                
            if obj_rect.colliderect(rect):
                if resultant_vel.y > 0:
                    y_change = set_change(y_change, rect.top-obj_rect.bottom)
                elif resultant_vel.y < 0:
                    y_change = set_change(y_change, rect.bottom-obj_rect.top)

                if resultant_vel.x > 0:
                    x_change = set_change(x_change, rect.left-obj_rect.right)
                elif resultant_vel.x < 0:
                    x_change = set_change(x_change, rect.right-obj_rect.left)

        x_bias = -abs(resultant_vel.x)*0.5
        y_bias = -abs(resultant_vel.y)*0.5
        
        if y_change and (not x_change or abs(y_change)+y_bias <= abs(x_change+x_bias)):
            obj.position.y += y_change
            obj_velocity.y = 0
        elif x_change:
            obj.position.x += x_change
            obj_velocity.x = 0



    def draw(self, obj, surface: p.Surface, lerp_amount=0.0):
        if DEBUG and obj.has_component(ObjectCollision):
            p.draw.rect(surface, "red", obj.get_rect(), 1)









class BorderCollision(ObjectComponent):

    dependencies = [ObjectCollision]

    def __init__(self, area: p.typing.RectLike, bounce=0.0):
        super().__init__()

        self.bounding_area = p.Rect(area)
        self.bounce = bounce

        self.add_methods = [self.process_collision]


    def process_collision(self, obj) -> None:
        obj_vel = obj.get_velocity()
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
