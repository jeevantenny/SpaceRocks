# SpaceRocks (A Game inspired by Asteroids)
**version 0.9.1**  
*python-3.13.3*

![SpaceRocks Gameplay](/demo/demo_clip.gif)

I made this game to test out a new framework I made for any games I would want to make in the future using pygame.
It takes a inspiration from Atari's Asteroids Arcade Game. You control a spaceship that can move forward, turn and
shoot. Shoot asteroids to gain points.

The games uses the NES color palette to try and mimic the feel of an NES title. All assets used in the game are
original apart from the two fonts, Upheaval and Tiny5. The Open Font License for the Tiny5 font can be found
[here](/assets/fonts/OFL.txt).

## Features
- Infinitely scrolling world in all directions
- Soundfx volume scale with distance.
- Press **F11** to toggle fullscreen mode
- Support for select number of controllers
- Progress is not lost when application is closed. Player can continue from exactly where they left off.
- **Ctrl D** to toggle debug mode (for testing)
- Press **ALT** + **SHIFT** + **D** when in settings to clear user data.

## Controls
### Keyboard
- **W** to move forward
- **A**-**D** to turn
- **SPACE** to shoot

### Controller
- **Right Trigger**/**Bumper** to move forward
- **Left Stick**/**D-pad** to turn
- **A** to shoot


## Libraries
`pygame-ce - 2.5.5`
