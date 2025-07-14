import pygame as p
from collections import defaultdict




type ActionKeys = defaultdict[int, bool]
type HoldKeys = defaultdict[int, int]

type Coordinate = tuple[float, float] | p.Vector2