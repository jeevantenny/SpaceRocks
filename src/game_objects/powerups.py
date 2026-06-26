import pygame as pg
from typing import Iterator

import debug

from src.custom_types import Timer
from src.input_device import InputInterpreter
from src.file_processing import assets
from src.audio.soundfx import HasSoundQueue
from src.input_device import controller_rumble

from .components import ObjectHitbox, ObjectTexture, ObjectVelocity
from .spaceship import PlayerShip
from .asteroids import Asteroid
from .projectiles import PlayerBullet, Laser
from .particles import Particle, Emitter





class PowerUp(HasSoundQueue):
    "Gives the player's spaceship additional abilities that they can either be offensive or defensive."

    texture_key: str | None = None
    powerup_list: dict[str, type["PowerUp"]] = {}

    _display_name = None
    _powerup_info = "No information"
    _usage_instr = None

    def __init_subclass__(cls):
        cls.powerup_list[cls.__name__] = cls

    @classmethod
    def get_name(cls) -> str:
        return cls.__name__
    
    @classmethod
    def get_display_name(cls) -> str:
        """
        The name of the powerups shown to the player using the `_display_name` field.
        If not defined then it returns the name of the class.
        """
        return cls._display_name or cls.__name__

    @classmethod
    def get_info_text(cls) -> str:
        return cls._powerup_info

    @classmethod
    def get_usage_instr(cls) -> str | None:
        return cls._usage_instr
    

    def get_data(self) -> tuple:
        return ()

    def indicator_slider_amount(self) -> float:
        return 1.0

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










class PowerUpGroup(HasSoundQueue):
    "Stores a collection of powerups collected by the player."

    def __init__(self):
        super().__init__()
        self.__container: list[PowerUp] = []

    def userinput(self, inputs: InputInterpreter) -> None:
        for powerup in self.__container:
            powerup.userinput(inputs)
    
    def update(self, spaceship: PlayerShip) -> None:
        for powerup in self.__container.copy():
            powerup.update(spaceship)
            self._join_sound_queue(powerup.clear_sound_queue())

    
    def draw(self, spaceship: PlayerShip, surface: pg.Surface, lerp_amount=0.0, offset: pg.typing.Point = (0, 0)):
        for powerup in self.__container:
            powerup.draw(spaceship, surface, lerp_amount, offset)


    def kill_protection(self, spaceship: PlayerShip) -> bool:
        "Called by the `PlayerShip` object to see if any of it's powerups can shield it from a collision."
        
        for powerup in self:
            if powerup.kill_protection(spaceship):
                return True
        return False

    def add(self, powerup: PowerUp) -> None:
        self.__container.append(powerup)

    def add_by_name(self, powerup_name: str) -> None:
        try:
            self.add(PowerUp.powerup_list[powerup_name]())
        except KeyError:
            raise ValueError(F"Invalid powerup '{powerup_name}'")
        

    def remove(self, powerup: PowerUp) -> None:
        self.__container.remove(powerup)

        
    def includes(self, powerup_name: str) -> bool:
        try:
            powerup_type = PowerUp.powerup_list[powerup_name]
        except KeyboardInterrupt:
            raise ValueError(F"Invalid powerup '{powerup_name}'")
        
        for powerup in self:
            if isinstance(powerup, powerup_type):
                return True
        
        return False

    def clear(self) -> None:
        self.__container.clear()

    def __iter__(self) -> Iterator[PowerUp]:
        return iter(self.__container)
    
    
    def __len__(self):
        return len(self.__container)






class PowerupCollectable(ObjectTexture, ObjectHitbox, ObjectVelocity):
    ignore_camera_rotation=True
    progress_save_key="powerup_collectable"
    _layer = -1

    def __init__(
            self,
            position: pg.typing.Point,
            velocity: pg.typing.Point,
            powerup_name: str
            ):

        powerup_type = PowerUp.powerup_list[powerup_name]
        if powerup_type.texture_key is not None:
            texture = assets.load_texture_map("powerups")[powerup_type.texture_key]
        else:
            texture = assets.colorkey_surface((16, 16))
            texture.fill("green")

        super().__init__(
            position=position,
            texture=texture,
            hitbox_size=(25, 25)
        )

        self.accelerate(velocity)
        self.__powerup_name = powerup_name
        self.__player_ship: PlayerShip | None = None
        self.__emitter: Emitter | None = None


    def __init_from_data__(self, object_data):
        self.__init__(object_data["position"], object_data["velocity"], object_data["powerup"])
        self.set_angular_vel(object_data["angular_vel"])


    @property
    def powerup_name(self) -> str:
        return self.__powerup_name


    def get_data(self):
        data = super().get_data()
        data.update({
            "position": tuple(self.position),
            "velocity": tuple(self._velocity),
            "powerup": self.__powerup_name,
            "angular_vel": self._angular_vel
        })

        return data


    def update(self):
        super().update()

        if self.__player_ship is None:
            for obj in self.primary_group:
                if isinstance(obj, PlayerShip):
                    self.__player_ship = obj
                    break
        
        elif self.rect.colliderect(self.__player_ship.rect):
            self.__player_ship.acquire_powerup(self.__powerup_name)
            self.host_state.powerup_info(PowerUp.powerup_list[self.__powerup_name])
            self.kill()
        

        if self.__emitter is None:
            if self.primary_group is not None:
                self.__set_emitter()
        else:
            self.__emitter.emit(self.position)
    

    def __set_emitter(self) -> None:
        particle_factory = Particle.get_factory("smoke", -2, True)
        self.__emitter = Emitter(particle_factory, self.primary_group, 0, [1, 4], [12, 18])
        








class Shield(PowerUp):
    texture_key = "shield"
    def __init__(self):
        super().__init__()
        self.__used = False



    def update(self, spaceship):
        super().update(spaceship)
        if self.__used:
            spaceship.remove_powerup(self)
    

    def kill_protection(self, spaceship):
        for obj in spaceship.overlapping_objects():
            if isinstance(obj, Asteroid) and obj.has_health():
                push_amount = obj.position-spaceship.position
                push_amount.scale_to_length(3)
                obj.accelerate(push_amount*2)
                spaceship.accelerate(-push_amount)

        self.__used = True
        spaceship.invincibility_frames()
        
        controller_rumble("small_pulse", 0.8)
        self._queue_sound("entity.asteroid.small_explode", 0.5)
        return True








class SuperLaser(PowerUp):
    __charge_time = 16
    __cooldown = 100

    _display_name = "Super Laser"
    texture_key = "super_laser"
    _usage_instr = "Hold<shoot> to charge laser, then release"

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
            for obstacle in self.__laser.killed_list:
                spaceship.host_state.player_destroy_obstacle(obstacle)

            self.__laser = None
            spaceship.remove_powerup(self)


    def draw(self, spaceship, surface, lerp_amount=0, offset = (0, 0)):
        if not (debug.Cheats.show_bounding_boxes and self.__charge_timer.complete):
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







class TripleShot(PowerUp):
    texture_key = "triple_shot"

    _display_name = "Triple Shot"
    __max_rounds = 30

    def __init__(self, rounds=__max_rounds):
        super().__init__()
        self.__rounds = rounds
        self.__shoot = False

    
    def get_data(self):
        return (self.__rounds,)
    
    def indicator_slider_amount(self):
        return self.__rounds/self.__max_rounds
    

    def userinput(self, inputs):
        if inputs.check_input("shoot"):
            self.__shoot = True
    

    def update(self, spaceship):
        if self.__shoot:
            bullet_rotation_a = spaceship.get_rotation_vector()
            self.__spawn_bullet(spaceship, bullet_rotation_a.rotate(10))
            self.__spawn_bullet(spaceship, bullet_rotation_a.rotate(-10))

            self.__shoot = False
            self.__rounds -= 1
            if self.__rounds <= 0:
                spaceship.remove_powerup(self)
    

    def __spawn_bullet(self, spaceship: PlayerShip, direction: pg.Vector2) -> None:
        spaceship.primary_group.add(PlayerBullet(
            spaceship.position+direction*40,
            direction,
            spaceship.get_velocity(),
            True
        ))









class Dodge(PowerUp):
    texture_key = "dodge"
    _usage_instr = "Hold <powerup_use> and input the direction you wanna dodge in"
    __max_dodges = 5

    def __init__(self, amount=__max_dodges, cooldown_used=0):
        super().__init__()
        self.__dodges = amount
        self.__dodge_cooldown = Timer(15)
        if cooldown_used:
            self.__dodge_cooldown.start()
            self.__dodge_cooldown.advance(cooldown_used)

        self.__dodge_direction = pg.Vector2()
        self.__dodge_duration = Timer(6, exec_after=self.__reset_dodge)
        self.__activate_dodge = False



    def get_data(self):
        return (self.__dodges, self.__dodge_cooldown.time_elapsed)
    
    def indicator_slider_amount(self):
        return self.__dodges/self.__max_dodges
    

    def userinput(self, inputs):
        if inputs.check_input("up"):
            self.__dodge_direction.y -= 1
        if inputs.check_input("down"):
            self.__dodge_direction.y += 1
        if inputs.check_input("left"):
            self.__dodge_direction.x -= 1
        if inputs.check_input("right"):
            self.__dodge_direction.x += 1
        
        
        if self.__dodge_cooldown.complete and inputs.check_input("powerup_use"):
            self.__dodge_duration.start()
            self.__activate_dodge = True

        elif self.__dodge_direction and self.__dodge_duration.complete:
            self.__dodge_duration.start()

    
    def update(self, spaceship):
        self.__dodge_cooldown.update()
        self.__dodge_duration.update()

        if self.__activate_dodge and self.__dodge_direction:
            self.__dodge_direction.scale_to_length(80)
            spaceship.move(self.__dodge_direction)
            spaceship.accelerate(spaceship.get_velocity()*-0.5)
            spaceship.invincibility_frames(15)

            self.__dodge_duration.stop()
            self.__reset_dodge()
            self.__dodge_cooldown.start()
            self.__dodges -= 1
            if self.__dodges <= 0:
                spaceship.remove_powerup(self)
    

    def __reset_dodge(self) -> None:
        self.__dodge_direction.xy = (0, 0)
        self.__activate_dodge = False
