"Contains useful stuff for debugging."

from functools import wraps
from time import perf_counter
from typing import Callable

DEBUG_MODE = False
PAUSE_ON_CRASH = False

class Cheats():
    """
    ## Cheats

    **invincible** - makes spaceship immune to asteroids and go through them  
    **no_obstacles** - prevents spawning of obstacles like asteroid or enemies 
    **show_bounding_boxes** - shows bounding boxes for entities  
    **instant_respawn** - UNIMPLEMENTED  
    **enemy_ship** - UNIMPLEMENTED  
    
    **test_state** - loads a test state instead of regular game states
    **test_level"" - loads a level to test out when Play state is used

    **demo_mode:**  
    Loads the game in demo mode. The game will show a message indicating
    that it's in demo mode. No data will be read from or written to user_data
    folder the game always starts as if loaded up for the first time.
    """

    invincible = False
    no_obstacles = False
    show_bounding_boxes = False
    instance_respawn = False
    enemy_ship = False
    demo_mode = False
    no_lerp = False

    test_state = None
    test_level = None



def timeit(func: Callable):
    "Times how long it takes a function to run and prints this value to console."
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = perf_counter()
        output = func(*args, **kwargs)
        print(f"{func.__name__} took {perf_counter()-start:.4f}s")
        return output
    
    return wrapper