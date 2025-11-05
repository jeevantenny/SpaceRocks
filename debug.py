"Contains useful stuff for debugging."

from functools import wraps
from time import perf_counter
from typing import Callable

PAUSE_ON_CRASH = __debug__

debug_mode = False

class Cheats():
    invincible = False
    instance_respawn = False
    enemy_ship = False
    test_state = False
    demo_mode = False



def timeit(func: Callable):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = perf_counter()
        output = func(*args, **kwargs)
        print(f"{func.__name__} took {perf_counter()-start:.4f}s")
        return output
    
    return wrapper