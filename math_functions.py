import pygame as pg
from typing import Literal




def clamp(value: int | float, Min: int | float, Max: int | float) -> int | float:
    return max(Min, min(value, Max))


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
        return vector/vector.magnitude()
    else:
        return pg.Vector2()