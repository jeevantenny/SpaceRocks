from functools import wraps
from time import perf_counter
from typing import Callable

debug_mode = False


class Cheats():
    invincible = False
    instance_respawn = False
    enemy_ship = False
    test_state = False
    dont_save_progress = False



def timeit(func: Callable):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = perf_counter()
        output = func(*args, **kwargs)
        print(f"{func.__name__} took {perf_counter()-start:.4f}s")
        return output
    
    return wrapper