import pygame as pg

import debug

from src.custom_types import Timer
from src.file_processing import assets
from src.math_functions import unit_vector
from src.ui import font

from . import GameObject
from .components import ObjectTexture, ObjectVelocity
from .entities import Spaceship, Asteroid
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
    __lifetime = 40
    _max_speed = 100 + __speed

    def __init__(self, position: pg.typing.Point, direction: pg.typing.Point, shooter: Spaceship, attack_types: list[type[GameObject]]):
        super().__init__(
            position=position,
            texture=assets.load_texture_map("particles")["bullet"]
        )

        self.shooter = shooter

        direction = unit_vector(pg.Vector2(direction))
        self.set_velocity(direction*self.__speed+shooter.get_velocity())
        self.move(direction*5)

        self.set_rotation(-direction.angle_to((0, -1)))
        self.__attack_types = attack_types
        self.__distance_traveled = 0.0


    
    def __init_from_data__(self, object_data):
        super().__init__(
            position=object_data["position"],
            texture=assets.load_texture_map("particles")["bullet"]
        )


        self.set_velocity(object_data["velocity"])

        self.set_rotation(object_data["rotation"])
        self.__shooter_id = object_data["shooter_id"]
        self.__attack_types = object_data["attack_types"]
        self.__distance_traveled = object_data["distance_traveled"]

    
    def post_init_from_data(self, object_dict):
        # Finds the shooter entity and assigns it to the shooter attribute.
        if self.__shooter_id in object_dict:
            self.shooter = object_dict[self.__shooter_id]
        else:
            raise Exception("Bullet cannot find shooter object.")


    
    def get_data(self):
        data = super().get_data()
        data.update({"velocity": tuple(self._velocity),
                     "rotation": self._rotation,
                     "shooter_id": id(self.shooter),
                     "attack_types": self.__attack_types,
                     "distance_traveled": self.__distance_traveled})
        return data



    def update(self):
        super().update()
        self.__distance_traveled += self.__speed
        self.__lifetime -= 1
        if self.__lifetime == 0:
            self.shooter.combo = 0
            self.force_kill()
            # Combo goes back to zero if player misses.
            return


        hit = False
        for obj in self.primary_group:
            # If the game object is a type the bullet can attack and the object is
            # alive then damage or kill it.
            if isinstance(obj, Asteroid) and obj.health and obj_line_collision(obj, self.__get_collision_lines()):
                self.__damage_asteroid(obj)
                hit = True

        if hit:
            self.kill()
            
        
    


    def draw(self, surface, lerp_amount=0, offset=(0, 0)):
        super().draw(surface, lerp_amount, offset)

        if debug.debug_mode:
            for line in self.__get_collision_lines(offset):
                pg.draw.line(surface, "blue", *line)





    def __damage_asteroid(self, asteroid: Asteroid) -> None:
        "Damages asteroid and increments the shooter's score and combo accordingly."
        asteroid.damage(1, self._velocity*0.1/asteroid.size)
        if not asteroid.health:
            # Score increments by asteroid's points + current combo amount
            self.__summon_display_text(asteroid.get_display_point_pos(), asteroid.points, self.shooter.combo)
            self.shooter.score += asteroid.points + self.shooter.combo
            self.shooter.combo += 1


    def __summon_display_text(self, position: pg.typing.Point, points: int, combo=0) -> None:
            if combo:
                texture = font.small_font.render(f"COMBO +{points+combo}", cache=False)
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
        if not self.__damage_duration.complete:
            for obj in self.primary_group:
                if isinstance(obj, Asteroid) and obj.health and obj_line_collision(obj, self.__collision_lines):
                    obj.kill(False)
                    self.killed_list.append(obj)
        
        self.__damage_duration.update()


    def draw(self, surface, lerp_amount=0, offset=(0, 0)) -> None:
        for line in self.__collision_lines:
            pg.draw.line(surface, "green", pg.Vector2(line[0])+offset, pg.Vector2(line[1])+offset)

