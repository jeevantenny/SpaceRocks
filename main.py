import sys
import debug

if __name__ == "__main__":
    sys.setrecursionlimit(200)
    if debug.Cheats.basic_engine:
        from src.basic_engine import BasicEngine
        game = BasicEngine()
    else:
        from src.game import GameEngine
        game = GameEngine()
    
    from src import glb
    glb.game = game
    game.start()
