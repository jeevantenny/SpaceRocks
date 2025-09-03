import pygame as pg
from typing import Literal




def clamp(value: int | float, Min: int | float, Max: int | float) -> int | float:
    return pg.math.clamp(value, Min, Max)


def sign(value: int | float) -> Literal[-1, 0, 1]:
    if value == 0:
        return 0
    else:
        return int(value/abs(value))


def vector_min(*values: pg.Vector2) -> pg.Vector2:
    return min(*values, key=lambda x: x.magnitude())


def vector_max(*values: pg.Vector2) -> pg.Vector2:
    return max(*values, key=lambda x: x.magnitude())


def unit_vector(vector: pg.Vector2) -> pg.Vector2:
    if vector.magnitude():
        return vector.normalize()
    else:
        return pg.Vector2()
    

def format_angle[T=int|float](angle: T) -> T:
    if angle > 180:
        angle -= 360
    return angle



def vector_direction(vector: pg.Vector2) -> float:
    return format_angle(pg.Vector2(0, -1).angle_to(vector))