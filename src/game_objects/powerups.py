import pygame as pg
from typing import Iterator, Literal

import debug

from src.custom_types import Timer
from src.input_device import InputInterpreter
from src.file_processing import assets
from src.audio.soundfx import HasSoundQueue
from src.input_device import controller_rumble

from .components import ObjectHitbox, ObjectTexture, ObjectVelocity, Obstacle
from .spaceship import PlayerShip
from .asteroids import Asteroid
from .projectiles import PlayerBullet, Laser
from .particles import Particle, Emitter





class PowerUp(HasSoundQueue):
    "Gives the player's spaceship additional abilities that they can either be offensive or defensive."

    texture_key: str | None = None
    powerup_list: dict[str, type["PowerUp"]] = {}
    priority = 0
    collectable_despawn = True

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
        "Updates powerup for every game tick."
        ...

    def draw(self, spaceship: PlayerShip, surface: pg.Surface, lerp_amount=0.0, offset: pg.typing.Point = (0, 0)) -> None:
        "Draws powerup for every frame."
        ...

    
    def on_kill(self, spaceship: PlayerShip) -> bool:
        return True
    
    def on_shoot(self, spaceship: PlayerShip) -> bool:
        return True
    
    def on_thrust(self, spaceship: PlayerShip) -> bool:
        return True
    
    def on_turn(self, spaceship: PlayerShip, direction: Literal[-1, 1]) -> bool:
        return True

    def do_collision(self, spaceship: PlayerShip) -> bool:
        return True










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


    def on_kill(self, spaceship: PlayerShip) -> bool:
        """Run when kill method is called on PlayerShip

        Returns True if the kill should continue, False if it should be cancelled.
        """
        for powerup in self:
            if not powerup.on_kill(spaceship):
                return False
        return True
    
    def on_shoot(self, spaceship: PlayerShip) -> bool:
        """Run when shoot method is called on PlayerShip
        
        Returns True if the shoot should continue, False if it should be cancelled.
        """
        for powerup in self:
            if not powerup.on_shoot(spaceship):
                return False
        return True

    def on_thrust(self, spaceship: PlayerShip) -> bool:
        """Run when _thrust method is called on PlayerShip
        
        Returns True if the thrust should continue, False if it should be cancelled.
        """
        for powerup in self:
            if not powerup.on_thrust(spaceship):
                return False
        return True
    
    def on_turn(self, spaceship: PlayerShip, direction: Literal[-1, 1]) -> bool:
        """Run when _turn method is called on PlayerShip
        
        Returns True if the turn should continue, False if it should be cancelled.
        """
        for powerup in self:
            if not powerup.on_turn(spaceship, direction):
                return False
        return True
    
    def do_collision(self, spaceship: PlayerShip) -> bool:
        """Run when do_collision method is called on PlayerShip
        
        Returns True if the collision should continue, False if it should be cancelled.
        """
        for powerup in self:
            if not powerup.do_collision(spaceship):
                return False
        return True



    def add(self, powerup: PowerUp) -> None:
        for i, p in enumerate(self):
            if p.priority <= powerup.priority:
                self.__container.insert(i, powerup)
                break
        else:
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

        if not powerup_type.collectable_despawn:
            self.can_despawn = False


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
    priority = 1
    def __init__(self):
        super().__init__()
        self.__used = False



    def update(self, spaceship):
        super().update(spaceship)
        if self.__used:
            spaceship.remove_powerup(self)
    

    def on_kill(self, spaceship):
        for obj in spaceship.overlapping_objects():
            if isinstance(obj, Asteroid) and obj.has_health():
                push_amount = obj.position-spaceship.position
                push_amount.scale_to_length(3)
                obj.accelerate(push_amount*2)
                spaceship.accelerate(-push_amount)

        self.__used = True
        spaceship.invincibility_frames()
        
        self._queue_sound("entity.asteroid.small_explode", 0.5)
        controller_rumble("small_pulse", 0.8)
        return False







class TripleShot(PowerUp):
    texture_key = "triple_shot"
    priority = 2

    _display_name = "Triple Shot"
    __max_rounds = 30

    def __init__(self, rounds=__max_rounds):
        super().__init__()
        self.__rounds = rounds

    def get_data(self):
        return (self.__rounds,)
    
    def indicator_slider_amount(self):
        return self.__rounds/self.__max_rounds

    def on_shoot(self, spaceship: PlayerShip) -> bool:
        bullet_rotation_a = spaceship.get_rotation_vector()
        self.__spawn_bullet(spaceship, bullet_rotation_a.rotate(10))
        self.__spawn_bullet(spaceship, bullet_rotation_a.rotate(-10))
        self.__spawn_bullet(spaceship, bullet_rotation_a)
        self._queue_sound("entity.ship.shoot", 0.8)
        controller_rumble("gun_fire")

        self.__rounds -= 1
        if self.__rounds <= 0:
            spaceship.remove_powerup(self)
        
        return False
    

    def __spawn_bullet(self, spaceship: PlayerShip, direction: pg.Vector2) -> None:
        spaceship.primary_group.add(PlayerBullet(
            spaceship.position+direction*12,
            direction,
            spaceship.get_velocity(),
            True
        ))









class Dodge(PowerUp):
    texture_key = "dodge"
    priority = 3

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

    def on_thrust(self, spaceship) -> bool:
        return not self.__activate_dodge
    
    def on_turn(self, spaceship, direction):
        return not self.__activate_dodge

    def __reset_dodge(self) -> None:
        self.__dodge_direction.xy = (0, 0)
        self.__activate_dodge = False








class SuperLaser(PowerUp):
    priority = 4

    _display_name = "Super Laser"
    texture_key = "super_laser"
    _usage_instr = "Hold<shoot> to charge laser, then release"

    __charge_time = 18
    __laser_duration = 25
    __rotation_speed = 4

    def __init__(self, laser_spawned=False, time_used=0):
        super().__init__()

        self.__charge_timer = Timer(self.__charge_time).start()
        self.__laser_timer = Timer(self.__laser_duration)
        self.__charging = False
        self.__laser = None
        self.__laser_from_save = laser_spawned

        if laser_spawned:
            self.__laser_timer.start()
            self.__laser_timer.advance(time_used)

    def get_data(self):
        return (self.__laser is not None, self.__laser_timer.time_elapsed)


    def indicator_slider_amount(self):
        return self.__laser_timer.complete or 1 - self.__laser_timer.completion_amount

    def userinput(self, inputs):
        self.__charging = inputs.check_input("shoot_hold")
        
    
    def update(self, spaceship):
        self.__laser_timer.update()
        if self.__laser_from_save or self.__charge_timer.complete and not self.__charging:
            self.__fire_laser(spaceship)
            self.__laser_from_save = False

        if self.__charging:
            self.__charge_timer.update()
        else:
            self.__charge_timer.restart()

        if self.__laser is not None:
            if self.__laser.alive():
                direction = spaceship.get_rotation_vector()
                spaceship.accelerate(direction*-0.3)
                spaceship.host_state.set_camera_target(spaceship.position + direction*50)
            else:
                for obstacle in self.__laser.killed_list:
                    spaceship.host_state.player_damage_obstacle(obstacle)

                self.__laser = None
                spaceship.host_state.set_camera_target(spaceship)
                spaceship.remove_powerup(self)


    def draw(self, spaceship, surface, lerp_amount=0, offset = (0, 0)):
        if self.__charge_timer.complete:
            pg.draw.circle(surface, "purple", spaceship.get_lerp_pos(lerp_amount)+offset, 15, 1)

        if not (debug.Cheats.show_bounding_boxes and self.__charge_timer.complete):
            return
        
        offset = pg.Vector2(offset)
        ship_rotation = spaceship.get_rotation()
        direction = pg.Vector2(0, -1).rotate(ship_rotation - self.__rotation_speed*(1-lerp_amount))
        perp = direction.rotate(90)*15
        start_pos = spaceship.position + offset
        end_pos = start_pos + direction*300

        pg.draw.line(surface, "blue", start_pos+perp, end_pos+perp)
        pg.draw.line(surface, "blue", start_pos-perp, end_pos-perp)
    

    def __fire_laser(self, spaceship: PlayerShip) -> None:
        if self.__laser_timer.complete:
            self.__laser_timer.start()

        self.__laser = Laser(spaceship,
                             30, 1, self.__laser_timer.countdown,
                             (Obstacle,),
                             spaceship.host_state.player_damage_obstacle)

        spaceship.primary_group.add(self.__laser)
        spaceship.set_velocity(spaceship.get_velocity().clamp_magnitude(8))

    def on_thrust(self, spaceship):
        return self.__laser_timer.complete
    
    def on_shoot(self, spaceship):
        return self.__laser_timer.complete
    
    def on_turn(self, spaceship, direction):
        if self.__laser_timer.complete:
            return True
        else:
            spaceship.rotate(direction*self.__rotation_speed)
            return False




class Hyperdrive(PowerUp):
    texture_key = "hyperdrive"
    collectable_despawn = False

    __drive_speed = 70

    def __init__(self):
        super().__init__()
        self.__timer = Timer(45).start()

    def indicator_slider_amount(self):
        return self.__timer.completion_amount
    

    def update(self, spaceship):
        if (spaceship.thrust
            and -80 < spaceship.get_rotation_vector().angle_to(spaceship.get_velocity()) < 80
            and spaceship.get_velocity().magnitude_squared() > self.__drive_speed**2):
            self.__timer.update()
            if self.__timer.complete:
                spaceship.host_state.start_next_level()
                spaceship.remove_powerup(self)
        else:
            self.__timer.advance(-1)
            
        

