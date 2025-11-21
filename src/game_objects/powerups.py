import pygame as pg
from typing import Iterator

import debug

from src.custom_types import Timer
from src.input_device import InputInterpreter
from src.audio import soundfx
from src.input_device import controller_rumble

from src.ui import font

from .components import ObjectVelocity, ObjectTexture, ObjectHitbox
from .entities import PlayerShip, Asteroid
from .projectiles import Laser
from .particles import DisplayText


powerup_list: dict[str, type["PowerUp"]] = {}


class PowerUp:
    "Gives the player's spaceship additional abilities that they can either be offensive or defensive."

    def __init__(self):
        ...

    def __init_subclass__(cls):
        powerup_list[cls.__name__] = cls

    @property
    def name(self) -> str:
        return type(self).__name__


    def userinput(self, inputs: InputInterpreter) -> None:
        "Processes userinput for powerup."
        ...

    def update(self, spaceship: PlayerShip) -> None:
        "Updates powerup for every frame."
        ...

    def draw(self, spaceship: PlayerShip, surface: pg.Surface, lerp_amount=0.0, offset: pg.typing.Point = (0, 0)) -> None:
        ...

    
    def kill_protection(self, spaceship: PlayerShip) -> bool:
        return False










class PowerUpGroup:
    "Stores a collection of powerups collected by the player."

    def __init__(self):
        self.__container: set[PowerUp] = set()

    def userinput(self, inputs: InputInterpreter) -> None:
        for powerup in self.__container:
            powerup.userinput(inputs)
    
    def update(self, spaceship: PlayerShip) -> None:
        for powerup in self.__container:
            powerup.update(spaceship)
    
    def draw(self, spaceship: PlayerShip, surface: pg.Surface, lerp_amount=0.0, offset: pg.typing.Point = (0, 0)):
        for powerup in self.__container:
            powerup.draw(spaceship, surface, lerp_amount, offset)


    def kill_protection(self, spaceship: PlayerShip) -> bool:
        "Called by the `PlayerShip` object to see if any of it's powerups can shield it from a collision."
        
        for powerup in self:
            if powerup.kill_protection(spaceship):
                return True
        return False

    def add(self, powerup_name: str) -> None:
        try:
            self.__container.add(powerup_list[powerup_name]())
        except KeyError:
            raise ValueError(F"Invalid powerup '{powerup_name}'")
        
    def remove(self, powerup: PowerUp) -> None:
        self.__container.remove(powerup)

        
    def includes(self, powerup_name: str) -> bool:
        try:
            powerup_type = powerup_list[powerup_name]
        except KeyboardInterrupt:
            raise ValueError(F"Invalid powerup '{powerup_name}'")
        
        for powerup in self:
            if isinstance(powerup, powerup_type):
                return True
        
        return False

    def clear(self) -> None:
        self.__container.clear()

    def __iter__(self) -> Iterator[PowerUp]:
        return self.__container.__iter__()






class PowerupCollectable(ObjectVelocity, ObjectTexture, ObjectHitbox):
    def __init__(self, position: pg.typing.Point, velocity: pg.typing.Point, powerup_name: str):
        texture = pg.Surface((16, 16))
        texture.fill("green")
        super().__init__(
            position=position,
            texture=texture,
            hitbox_size=(16, 16)
        )

        self.accelerate(velocity)
        self.__powerup_name = powerup_name
        self.__player_ship: PlayerShip | None = None


    def update(self):
        super().update()

        if self.__player_ship is None:
            for obj in self.primary_group:
                if isinstance(obj, PlayerShip):
                    self.__player_ship = obj
                    break
        
        elif self.colliderect(self.__player_ship.rect):
            self.__player_ship.acquire_powerup(self.__powerup_name)
            self.kill()








class SuperLaser(PowerUp):
    __charge_time = 16
    __cooldown = 100

    def __init__(self):
        super().__init__()

        self.__charge_timer = Timer(self.__charge_time).start()
        self.__cooldown_timer = Timer(self.__cooldown)
        self.__charging = False
        self.__laser = None


    def userinput(self, inputs):
        self.__charging = self.__cooldown_timer.complete and inputs.check_input("shoot_hold")
        
    
    def update(self, spaceship):
        if self.__charge_timer.complete and not self.__charging:
            self.__fire_laser(spaceship)

        if self.__charging:
            self.__charge_timer.update()
        else:
            self.__charge_timer.restart()

        
        if not (self.__laser is None or self.__laser.alive()):
            points = 0
            for asteroid in self.__laser.killed_list:
                points += asteroid.points
            spaceship.score += points
            if points:
                spaceship.primary_group.add(
                    DisplayText(spaceship.position+self.__laser.get_rotation_vector()*40, font.large_font.render(
                        f"+{points}", 1, "#cc8800", "#442200", False
                    ))
                )

            self.__laser = None


    def draw(self, spaceship, surface, lerp_amount=0, offset = (0, 0)):
        if not (debug.debug_mode and self.__charge_timer.complete):
            return
        
        offset = pg.Vector2(offset)
        direction = spaceship.get_rotation_vector()
        perp = direction.rotate(90)*25
        start_pos = spaceship.position + offset
        end_pos = start_pos + direction*300

        pg.draw.line(surface, "red", start_pos+perp, end_pos+perp)
        pg.draw.line(surface, "red", start_pos-perp, end_pos+direction-perp)
    

    def __fire_laser(self, spaceship: PlayerShip) -> None:
        self.__laser = Laser(spaceship.position, spaceship.get_rotation(), 50, 1)
        spaceship.primary_group.add(self.__laser)

        spaceship.accelerate(-spaceship.get_rotation_vector()*5)











class Shield(PowerUp):
    def __init__(self):
        super().__init__()

    def kill_protection(self, spaceship):
        for obj in spaceship.overlapping_objects():
            if isinstance(obj, Asteroid) and obj.health:
                push_amount = obj.position-spaceship.position
                push_amount.scale_to_length(3)
                obj.accelerate(push_amount*2)
                spaceship.accelerate(-push_amount)
        
        spaceship.remove_powerup(self)
        spaceship.invincibility_frames()
        controller_rumble("small_pulse", 0.8)
        return True