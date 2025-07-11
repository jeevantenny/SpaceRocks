import pygame as p




def vector_min(*values: p.Vector2) -> p.Vector2:
    return min(*values, key=lambda x: x.magnitude())


def vector_max(*values: p.Vector2) -> p.Vector2:
    return max(*values, key=lambda x: x.magnitude())


def unit_vector(vector: p.Vector2) -> p.Vector2:
    if vector.magnitude():
        return vector/vector.magnitude()
    else:
        return p.Vector2()