# SpaceRocks
**Version:** 0.10.5 | **Environment:** Python 3.13 | **Engine:** Pygame-CE 2.5.6

![Gameplay](./readme_assets/demo_clip_new.gif)

SpaceRocks is an arcade-style space shooter inspired by Atari's classic *Asteroids*, styled using a retro NES color palette and original pixel art assets. 

The primary objective of this project was to design and implement a decoupled, reusable **2D Game Engine Framework** built on top of Pygame-CE to handle scene management, asset loading, and system configurations for future development.

## ![](/readme_assets/heading_icon.png) Architectural & Technical Features

- **Custom Engine Framework:** Implemented an event-driven state machine architecture to cleanly separate game states (Main Menu, Gameplay, Pause Menus, Settings).

- **Framerate Independance:** Developed a way to keep framerate and tickrate completely independant of each other using two threads. Display and event handling run on main thread while game logic and file processing run in secondary thread. Making sure game runs at the same speed across various fps is now easier (compared to using delta-time)

- **Dynamic Resolution Scaling:** Developed a robust window management system that maintains a constant surface area in terms of pixels no matter the size and aspect ratio. Supports fullscreen via toggling **F11** .

- **State Persistence & Serialization:** Implemented background user-data tracking that automatically serializes game state to local disk storage, allowing the player to seamlessly continue their session after restarting the game.

- **Distance-Attenuated Audio Engine:** Programmed a dynamic sound effects subsystem that scales audio volume and panning dynamically based on vector distances relative to the player's position.

- **Cross-Platform Input Mapping:** Supports simultaneous polling for both keyboard layouts and standard game controller hardware mappings.

## ![](/readme_assets/heading_icon.png) Controls

### Keyboard
* `W` : Move Forwards
* `A` / `D` : Turn Left / Right
* `SPACE` : Primary Weapon Fire

### Controller
* `RT` / `RB` : Move Forwards
* `Left Stick` / `D-Pad` : Turn Left / Right
* `A Button` : Primary Weapon Fire

### System Shortcuts
* `F11` : Toggle Fullscreen Mode
* `ALT` + `SHIFT` + `D` : Trigger User Data Factory Reset (Settings Menu Only)

## ![](/readme_assets/heading_icon.png) Assets & Compliance
All graphical and audio assets are original, with the exception of the open-source typography integrations (`Upheaval` and `Tiny5`). The Open Font License documentation for the `Tiny5` font can be found [here](/assets/fonts/OFL.txt).
