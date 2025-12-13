import pygame as pg
from typing import Iterable

import debug

from src.custom_types import Timer
from src.file_processing import assets
from src.math_functions import unit_vector
from src.ui import font

from . import GameObject
from .components import ObjectTexture, ObjectVelocity, ObjectHitbox
from .particles import DisplayText



type CollisionLines = list[tuple[pg.Vector2, pg.Vector2]]

def get_collision_lines(start_pos: pg.Vector2, direction: pg.Vector2, length: int, width: int, count=3) -> CollisionLines:
    """
    Returns a list containing the coordinates for three lines. This will be used for collision
    checking projectiles as they will be moving very fast. Lasers will use this as a way of checking
    when objects come within its path.
    """

    line_offset = direction*length
    end_pos = start_pos+line_offset
    if count == 1:
        return [(start_pos, end_pos),]

    sideways: pg.Vector2 = direction.rotate(90)*width
    division_amount = 1/(count-1)

    lines = []

    for i in range(count):
        s_offset = sideways*(division_amount*i-0.5)
        lines.append(
            (start_pos+s_offset, end_pos+s_offset),
        )

    return lines



def obj_line_collision(obj: ObjectHitbox, lines: CollisionLines) -> bool:
    return any(map(obj.rect.clipline, lines))





class Projectile(ObjectTexture, ObjectVelocity):
    draw_layer = 1
    _max_speed = 200

    def __init__(
            self,
            texture: pg.Surface,
            position: pg.typing.Point,
            velocity: pg.typing.Point,
            width: int,
            lifetime: int,
            rotation=0
            ):

        super().__init__(
            position=position,
            texture=texture
        )

        self.set_velocity(velocity)
        self.__speed = self._velocity.magnitude()
        self.set_rotation(rotation)
        self.__width = width

        self._distance_traveled = 0.0
        self._lifetime = lifetime



    def update(self):
        super().update()
        self._distance_traveled += self.__speed
        self._lifetime -= 1

        if self.primary_group is None:
            return

        hit = False
        for obj in self.primary_group:
            hit = self._process_object(obj) or hit
        if hit:
            self.kill()
        
        if self._lifetime <= 0:
            self.force_kill()

            
        

    def draw(self, surface, lerp_amount=0, offset=(0, 0), rotation=0):
        super().draw(surface, lerp_amount, offset, rotation)

        if debug.Cheats.show_bounding_boxes:
            for line in self.__get_collision_lines(offset):
                pg.draw.line(surface, "blue", *line)
    
    
    def __collision_line_length(self) -> float:
        return min(self._distance_traveled*0.5-9, self.__speed*2)


    def __get_collision_lines(self, offset: pg.typing.Point = (0, 0)) -> CollisionLines:
        return get_collision_lines(
            self.position-self._velocity+offset,
            -self.get_rotation_vector(),
            self.__collision_line_length(),
            self.__width
        )
    
    def _collides_with(self, obj: ObjectHitbox) -> bool:
        return obj_line_collision(obj, self.__get_collision_lines())
    

    def _process_object(self, obj: GameObject) -> bool:
        """
        This method controls what should happen to objects in the bullet's primary group every frame. Returns
        True if the projectile should count as colliding with the object and should be deleted in the next
        frame.
        """
        return False

    

    



class PlayerBullet(Projectile):
    save_entity_progress=True
    __speed = 40
    __lifetime_value = 18

    def __init__(self, position: pg.typing.Point, direction: pg.typing.Point, shooter_vel: pg.typing.Point):
        super().__init__(
            assets.load_texture_map("particles")["bullet"],
            position,
            direction*self.__speed+shooter_vel,
            18,
            self.__lifetime_value,
            -direction.angle_to((0, -1))
        )

        from .obstacles import Asteroid
        self.hit_list = set[Asteroid]()


    
    def __init_from_data__(self, object_data):
        super().__init__(
            assets.load_texture_map("particles")["bullet"],
            object_data["position"],
            object_data["velocity"],
            18,
            object_data["lifetime"],
            object_data["rotation"]
        )
        self._distance_traveled = object_data["distance_traveled"]

        from .obstacles import Damageable
        self.hit_list = set[Damageable]()


    
    def get_data(self):
        data = super().get_data()
        data.update({"position": tuple(self.position),
                     "velocity": tuple(self._velocity),
                     "rotation": self._rotation,
                     "lifetime": self._lifetime,
                     "distance_traveled": self._distance_traveled})
        return data


    def _process_object(self, obj):
        from .obstacles import Damageable, Asteroid
        if isinstance(obj, Damageable) and obj._health and self._collides_with(obj):
            if isinstance(obj, Asteroid):
                obj.damage(1, self._velocity*0.1/obj.size)
            else:
                obj.damage(1)
                
            self.hit_list.add(obj)
            return True
        elif isinstance(obj, EnemyBullet):
            obj.kill()
            return False

        else:
            return False
    






class Laser(ObjectTexture):
    "A beam like weapon that has no range limit."

    save_entity_progress=False
    def __init__(
            self,
            position: pg.typing.Point,
            rotation: int,
            width: int,
            damage: int,
            duration=3
            ):

        super().__init__(position=position, texture=None)

        self.__damage_duration = Timer(duration, exec_after=self.kill).start()
        self.__damage = damage
        self._rotation = rotation

        self.__collision_lines = get_collision_lines(position, self.get_rotation_vector(), 300, width, 5)
        self.killed_list: list[GameObject] = []



    def set_rotation(self, value):
        raise AttributeError(f"Cannot change rotation of {type(self).__name__}")




    def update(self):
        from .obstacles import Asteroid
        if not self.__damage_duration.complete:
            for obj in self.primary_group:
                if isinstance(obj, Asteroid) and obj._health and obj_line_collision(obj, self.__collision_lines):
                    obj.kill(False)
                    self.killed_list.append(obj)
        
        self.__damage_duration.update()


    def draw(self, surface, lerp_amount=0, offset=(0, 0), rotation=0) -> None:
        for line in self.__collision_lines:
            pg.draw.line(surface, "green", pg.Vector2(line[0])+offset, pg.Vector2(line[1])+offset)







class EnemyBullet(Projectile):
    __speed = 16
    __lifetime_value = 18

    def __init__(self, position: pg.typing.Point, direction: pg.Vector2, shooter_vel: pg.typing.Point):
        direction = direction.normalize()
        super().__init__(
            assets.load_texture_map("particles")["bullet"],
            position+direction*10,
            direction*self.__speed+shooter_vel,
            10,
            self.__lifetime_value,
            -direction.angle_to((0, -1))
        )

    
    def _process_object(self, obj):
        from .spaceship import PlayerShip
        from .obstacles import Asteroid
        if isinstance(obj, PlayerShip) and self._collides_with(obj):
            obj.kill()
            return True
        elif isinstance(obj, Asteroid) and obj.health and self._collides_with(obj):
            obj.damage(1, self._velocity*0.1/obj.size)
            return True
        else:
            return False