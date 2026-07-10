import sys
import os
import debug

os.add_dll_directory(os.getcwd())

from steamworks import STEAMWORKS, SteamNotRunningException
from src import glb

if __name__ == "__main__":
    glb.steamworks = STEAMWORKS()
    try:
        glb.steamworks.initialize()
    except SteamNotRunningException:
        print("Steam not running, relaunching with Steam")
        glb.steamworks.relaunch(glb.steamworks.app_id)
        exit(0)

    sys.setrecursionlimit(200)
    if debug.Cheats.basic_engine:
        from src.basic_engine import BasicEngine
        game = BasicEngine()
    else:
        from src.game import GameEngine
        game = GameEngine()
    
    glb.game = game
    game.start()
