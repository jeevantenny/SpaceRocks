import sys
import debug

if __name__ == "__main__":
    sys.setrecursionlimit(200)
    if debug.Cheats.basic_engine:
        from src.basic_engine import BasicEngine
        BasicEngine().start()
    else:
        from src.game import GameEngine
        GameEngine().start()
