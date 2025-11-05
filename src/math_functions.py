import pygame as pg
from typing import Literal





def sign(value: int | float) -> Literal[-1, 0, 1]:
    "Return sign of number. Return zero if number is zero."
    if value == 0:
        return 0
    else:
        return int(value/abs(value))


def vector_min(*values: pg.Vector2) -> pg.Vector2:
    "Return vector with lowest magnitude."
    return min(*values, key=lambda x: x.magnitude())


def vector_max(*values: pg.Vector2) -> pg.Vector2:
    "Return vector with highest magnitude."
    return max(*values, key=lambda x: x.magnitude())


def unit_vector(vector: pg.Vector2) -> pg.Vector2:
    """
    Normalize vector to magnitude of one. If Vector has no magnitude returns vector
    with no magnitude.
    """
    return vector.copy() and vector.normalize()
    

def format_angle[T: (int, float)](angle: T) -> T:
    "Ensures angle is between >-180 and <=180."
    if angle > 180:
        angle -= 360
    elif angle <= -180:
        angle += 360

    return angle



def vector_direction(vector: pg.Vector2) -> float:
    "Returns the direction of a vector relative to (0, -1)."
    return format_angle(pg.Vector2(0, -1).angle_to(vector))