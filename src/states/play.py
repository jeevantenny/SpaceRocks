import pygame as pg
import random
from typing import Self

import debug

from src.custom_types import Timer, SaveData
from src.file_processing import assets, data

from src.game_objects import (
    GameObject, ObjectGroup, asteroids, camera, components, enemies, powerups, projectiles, spaceship, particles
)

from . import State
from .menus import PauseMenu
from .visuals import ShowText




class Play(State):
    """
    Handles the actual Gameplay. Contains a game loop that constantly updates all game objects
    and player score.
    """
    __spawn_radius = 200
    __despawn_radius = 500

    _player_max_lives = 3

    def _setup(self) -> None:
        "Called by all initializers to set up needed attributes. Spaceship needs to be made separately."
        self.__parl_a: pg.Surface | None = None
        self.__parl_b: pg.Surface | None = None
        self.__base_color: pg.typing.ColorLike = "#000000"
        self.__background_tint: pg.typing.ColorLike = "#777777"
    
        self._object_spawn_delay = Timer(15)
        self._game_over_timer = Timer(40, False, self._game_over)
        self._respawn_timer = Timer(25, False, self._respawn_player)
        self._player_lives = self._player_max_lives


    def __init__(self):
        super().__init__()
        self._setup()
        self._setup_game_objects()

        self.spaceship = spaceship.PlayerShip((0, 0))
        self.entities.add(self.spaceship)


    @classmethod
    def init_from_save(cls, save_data: SaveData) -> Self:
        """
        Alternate way to create a Play state by using the save data. This allows the player to
        continue right from where they left off before they closed the application.
        """
        self = cls.__new__(cls)
        super().__init__(self)
        self._setup()
        self._setup_game_objects()

        self.__load_objects_from_save(save_data.entity_data)
        self.camera.set_position(save_data.camera_pos)
        self._player_lives = save_data.player_lives

        return self
    

    def _setup_game_objects(self) -> None:
        "Creates all the object groups and the camera."

        self.entities = ObjectGroup(host_state=self)
        self.spawned_entities = self.entities.make_subgroup()

        self.asteroids: ObjectGroup[asteroids.Asteroid] = self.spawned_entities.make_subgroup()
        self.powerups: ObjectGroup[powerups.PowerupCollectable] = self.spawned_entities.make_subgroup()
        self.enemies = self.spawned_entities.make_subgroup()

        self.camera = camera.Camera((0, 0))



    def _setup_level(self, level_name: str) -> None:
        "Assigned attributes related to the current level."

        self._level_data = data.load_level(level_name)

        if self._level_data.parl_a is None:
            self.__parl_a = None
        else:
            self.__parl_a = assets.load_texture(self._level_data.parl_a, self._level_data.background_palette)
        
        if self._level_data.parl_b is None:
            self.__parl_b = None
        else:
            self.__parl_b = assets.load_texture(self._level_data.parl_b, self._level_data.background_palette)

        self.__base_color = self._level_data.base_color
        self.__background_tint = self._level_data.background_tint



    def __load_objects_from_save(self, entity_data: list[dict]) -> None:
        """
        Loads all objects from a save data's entity data attribute. _setup_game_objects
        must have been called beforehand.
        """
        object_dict = {}

        for entity_data in entity_data:
            entity = GameObject.init_from_data(entity_data)
            self.entities.add(entity)
            if isinstance(entity, asteroids.Asteroid):
                self.asteroids.add(entity)
            if isinstance(entity, powerups.PowerupCollectable):
                self.powerups.add(entity)
            elif isinstance(entity, spaceship.PlayerShip):
                self.spaceship = entity

            object_dict[entity_data["id"]] = entity
        
        for entity in self.entities.sprites():
            entity.post_init_from_data(object_dict)







    def userinput(self, inputs):
        if debug.DEBUG_MODE:
            if inputs.keyboard_mouse.tap_keys[pg.K_r]:
                self.spaceship.position = pg.Vector2(200, 150)
                self.spaceship.set_velocity((0, 0))

            keyboard = inputs.keyboard_mouse

            if keyboard.tap_keys[pg.K_k]:
                if keyboard.hold_keys[pg.KMOD_SHIFT]:
                    self._player_lives = 1
                    self.spaceship.kill()
                    if self.spaceship.health:
                        self.spaceship.force_kill()
                else:
                    for asteroid in self.asteroids.sprites():
                        asteroid.kill(False)

            if keyboard.tap_keys[pg.K_c]:
                self.spaceship.combo *= 2

            if keyboard.tap_keys[pg.K_g]:
                debug.Cheats.show_bounding_boxes = not debug.Cheats.show_bounding_boxes


        self.spaceship.userinput(inputs)

        if self.spaceship.health and inputs.check_input("pause"):
            self._pause_game()





    def update(self):
        if not self._game_over_timer.complete or not self._respawn_timer.complete:
            self.entities.update(self.camera.position, (components.Obstacle, powerups.PowerupCollectable))
            for obj in self.asteroids.sprites() + self.enemies.sprites():
                if not obj.has_health():
                    obj.update()
        else:
            self._game_loop()

        self._join_sound_queue(self.entities.clear_sound_queue())

        self._object_spawn_delay.update()
        self._game_over_timer.update()
        self._respawn_timer.update()




    def draw(self, surface, lerp_amount=0):
        self._draw_base(surface)
        if not debug.Cheats.ignore_colorkey:
            self._draw_scrolling_background(surface, lerp_amount)

        self._draw_entities(surface, lerp_amount)



    def debug_info(self) -> str | None:
        return f"entity count: {self.entities.count()}, combo: {self.spaceship.combo:.1f}, camera: ({self.camera.position.x:.0f}, {self.camera.position.y:.0f})"





    
    def _delete_distant_objects(self) -> None:
        "Deletes objects that are beyond the despawn radius of the spaceship."
        for obj in self.spawned_entities.sprites():
            if obj.distance_to(self.spaceship) > self.__despawn_radius:
                obj.force_kill()


    def _update_game_objects(self) -> None:
        self.entities.update(self.camera.position)
        self.camera.set_target(self.spaceship.position + self.spaceship.get_velocity()*2)
        self.camera.update()


    def _freeze_gameplay(self) -> None:
        return not self._respawn_timer.complete or not self._game_over_timer.complete


    
    def _game_loop(self) -> None:
        self._update_game_objects()
        self._delete_distant_objects()

        if not self.spaceship.health:
            self._player_lives -= 1
            self.camera.clear_velocity()

            for smoke in self.entities.get_type(particles.ShipSmoke):
                smoke.clear_velocity()

            if self._player_lives > 0:
                self._respawn_timer.start()
            else:
                self._game_over_timer.start()




    def _pause_game(self) -> None:
        "Adds PauseMenu state to state stack as well as some background tint."
        PauseMenu(self.__background_tint).add_to_stack(self.state_stack)


    def _respawn_player(self) -> None:
        score = self.spaceship.score
        self.spaceship = spaceship.PlayerShip(self._player_respawn_pos())
        self.spaceship.score = score
        self.entities.add(self.spaceship)
        self.spaceship.invincibility_frames()

        self.powerups.kill_all()
    
    def _player_respawn_pos(self) -> pg.Vector2:
        spaceship_pos = self.spaceship.position.xy
        if self.spaceship.position == (0, 0):
            return pg.Vector2(0, -self.__despawn_radius)
        else:
            spaceship_pos.scale_to_length(spaceship_pos.magnitude() - self.__despawn_radius)
            return spaceship_pos

    
    def _game_over(self) -> None:
        self.state_stack.quit()
        type(self)().add_to_stack(self.state_stack)



    def _draw_base(self, surface: pg.Surface) -> None:
        if data.get_setting("motion_blur") and self.is_top_state():
            surface.fill((70, 70, 70), special_flags=pg.BLEND_RGB_SUB)
            surface.fill(self.__base_color, special_flags=pg.BLEND_RGB_ADD)
        else:
            surface.fill(self.__base_color)


    def _draw_scrolling_background(self, surface: pg.Surface, lerp_amount=0.0) -> None:
        cam_lerp_pos = self.camera.lerp_position(lerp_amount)

        # Background B
        if self.__parl_b is not None:
            self.__scrolling_texture(surface, self.__parl_b, cam_lerp_pos, 0.1)

        # Background A
        if self.__parl_a is not None:
            self.__scrolling_texture(surface, self.__parl_a, cam_lerp_pos, 0.3)

    
    def _draw_entities(self, surface: pg.Surface, lerp_amount=0.0) -> None:
        self.camera.capture(surface, self.entities, lerp_amount)











    def __scrolling_texture(self, surface: pg.Surface, background_surface: pg.Surface, camera_pos: pg.Vector2, scroll_amount: float) -> None:
        center = pg.Vector2(surface.size)*0.5
        width, height = background_surface.size
        camera_offset = -camera_pos*scroll_amount
        camera_offset = pg.Vector2(camera_offset[0]%width - width*0.5, camera_offset[1]%height - width*0.5)
        scroll_width = int(surface.width//width)
        scroll_height = int(surface.height//height)

        for x in range(-scroll_width-1, scroll_width+1):
            for y in range(-scroll_height-1, scroll_height+1):
                surface.blit(background_surface, center+(width*x, height*y)+camera_offset)



    def _get_object_spawn_pos(self) -> pg.Vector2:
        "Returns a random position for objects like asteroids and powerups to spawn offscreen."
        distance_from_center = self.__spawn_radius+self.spaceship.get_speed()*0.3
        return self.camera.position + pg.Vector2(distance_from_center).rotate(random.randint(0, 360))
    

    def _get_object_spawn_velocity(self, start_pos: pg.typing.Point, magnitude: float) -> pg.Vector2:
        "Returns the velocity of an object so that is goes onscreen towards the spaceship."
        velocity = self.camera.position-start_pos
        velocity.scale_to_length(magnitude)
        velocity.rotate_ip(random.randint(-40, 40))
        return velocity



    def _save_progress(self) -> None:
        "Saves the current state of the game to a save file."
        
        if not self._respawn_timer.complete:
            respawn_pos = self._player_respawn_pos()
            self.spaceship.set_position(respawn_pos)


        entity_data = [entity.get_data()
                       for entity in self.entities.sprites()
                       
                       if entity.progress_save_key is not None]
        
        camera_pos = tuple(self.camera.position)
        save_data = SaveData(self._level_data.level_name, self.spaceship.score, self._player_lives, camera_pos, entity_data)
        data.save_progress(save_data)