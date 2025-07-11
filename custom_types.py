import pygame as p
from collections import defaultdict




type ActionKeys = defaultdict[int, bool]
type HoldKeys = defaultdict[int, float]

type Coordinate = tuple[float, float] | p.Vector2