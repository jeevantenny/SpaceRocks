import pygame as pg

import debug

from src.custom_types import Timer
from src.file_processing import assets
from src.math_functions import unit_vector
from src.ui import font

from . import GameObject
from .components import ObjectTexture, ObjectVelocity
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



def obj_line_collision(obj: GameObject, lines: CollisionLines) -> bool:
    return any(map(obj.rect.clipline, lines))



class Bullet(ObjectTexture, ObjectVelocity):
    draw_layer = 1

    __speed = 40
    __lifetime = 18
    _max_speed = 100 + __speed

    def __init__(self, position: pg.typing.Point, direction: pg.typing.Point, shooter_vel: pg.typing.Point):
        super().__init__(
            position=position,
            texture=assets.load_texture_map("particles")["bullet"]
        )

        direction = unit_vector(pg.Vector2(direction))
        self.set_velocity(direction*self.__speed+shooter_vel)
        self.move(direction*5)

        self.set_rotation(-direction.angle_to((0, -1)))
        self.__distance_traveled = 0.0

        from .entities import Asteroid
        self.hit_list = set[Asteroid]()


    
    def __init_from_data__(self, object_data):
        super().__init__(
            position=object_data["position"],
            texture=assets.load_texture_map("particles")["bullet"]
        )


        self.set_velocity(object_data["velocity"])
        self.set_rotation(object_data["rotation"])
        self.__lifetime = object_data["lifetime"]
        self.__distance_traveled = object_data["distance_traveled"]


    
    def get_data(self):
        data = super().get_data()
        data.update({"velocity": tuple(self._velocity),
                     "rotation": self._rotation,
                     "lifetime": self.__lifetime,
                     "distance_traveled": self.__distance_traveled})
        return data



    def update(self):
        super().update()
        self.__distance_traveled += self.__speed
        self.__lifetime -= 1

        from .entities import Asteroid

        hit = False
        for obj in self.primary_group:
            # If the game object is a type the bullet can attack and the object is
            # alive then damage or kill it.
            if isinstance(obj, Asteroid) and obj.health and obj_line_collision(obj, self.__get_collision_lines()):
                obj.damage(1, self._velocity*0.1/obj.size)
                self.hit_list.add(obj)
                hit = True

        if hit:
            self.kill()
        
        if self.__lifetime <= 0:
            self.force_kill()
            
        
    


    def draw(self, surface, lerp_amount=0, offset=(0, 0)):
        super().draw(surface, lerp_amount, offset)

        if debug.Cheats.show_bounding_boxes:
            for line in self.__get_collision_lines(offset):
                pg.draw.line(surface, "blue", *line)



    def __summon_display_text(self, position: pg.typing.Point, points: int, has_combo=False) -> None:
            if has_combo:
                texture = font.small_font.render(f"COMBO +{points}", cache=False)
            else:
                texture = font.small_font.render(f"+{points}", color_a="#eeeeee", color_b="#333333", cache=False)
            self.primary_group.add(DisplayText(position, texture))
    
    
    def __collision_line_length(self) -> float:
        return min(self.__distance_traveled*0.5-9, self.__speed*2)


    def __get_collision_lines(self, offset: pg.typing.Point = (0, 0)) -> CollisionLines:
        return get_collision_lines(
            self.position-self._velocity+offset,
            -self.get_rotation_vector(),
            self.__collision_line_length(),
            18
        )
    










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
        from .entities import Asteroid
        if not self.__damage_duration.complete:
            for obj in self.primary_group:
                if isinstance(obj, Asteroid) and obj.health and obj_line_collision(obj, self.__collision_lines):
                    obj.kill(False)
                    self.killed_list.append(obj)
        
        self.__damage_duration.update()


    def draw(self, surface, lerp_amount=0, offset=(0, 0)) -> None:
        for line in self.__collision_lines:
            pg.draw.line(surface, "green", pg.Vector2(line[0])+offset, pg.Vector2(line[1])+offset)

