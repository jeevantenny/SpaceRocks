"Contains the Play state that handles the actual Gameplay."

import pygame as pg
import math
import random
from typing import Self

import config
import debug

from src.misc import increment_score, level_completion_amount, weighted_choice
from src.custom_types import SaveData, Timer
from src.file_processing import assets, data

from src.game_objects import GameObject, ObjectGroup, components
from src.game_objects.spaceship import PlayerShip
from src.game_objects.obstacles import Asteroid, EnemyShip
from src.game_objects.projectiles import Projectile
from src.game_objects.powerups import PowerUp, PowerupCollectable
from src.game_objects.camera import Camera

from src.ui import font, effects, hud

from . import State
from .menus import PauseMenu, GameOverScreen
from .visuals import BackgroundTint, ShowText
from .info_states import PowerupInfo, NoMoreLevels






class Play(State):
    """
    Handles the actual Gameplay. Contains a game loop that constantly updates all game objects
    and player score.
    """
    __spawn_radius = 150
    __visible_radius = 230
    __despawn_radius = 500
    __score_limit = 99999


    def __init__(self, level_name: str):
        "The main initializer that starts a new game on a specific level. Mainly the first level."

        super().__init__()

        self._setup()
        self.__setup_level(level_name)
        self._setup_game_objects()

        self.spaceship = PlayerShip((0, 0))
        self.spaceship.set_score_limit(self.__level_data.score_range[1])
        self.entities.add(self.spaceship)


    def reinit_next_level(self, level_name: str) -> None:
        "Reinitializes the current Play object for the next level without creating another Play object."

        if level_name == "boss_level":
            self.state_stack.force_quit()
            from .boss_level import PlayBossLevel
            PlayBossLevel().add_to_stack(self.state_stack)
            return
        
        self.__setup_level(level_name)
        
        self.entities.remove(self.spaceship)
        self.entities.kill_all()
        self.entities.add(self.spaceship)

        self.spaceship.set_position((0, 0))
        self.spaceship.set_velocity(self.spaceship.get_rotation_vector()*10)
        self.spaceship.set_score_limit(self.__level_data.score_range[1])

        self.camera.set_position((0, 0))
        self.camera.reset_motion()

        self.__lvl_transition_timer.restart()
        self.__hud_timer.restart()
        self.__object_spawn_delay.restart()

        self.__display_score = self.spaceship.score
        self.__level_cleared = False

        ShowText(level_name.replace("_", " ").upper()).add_to_stack(self.state_stack)


    
    @classmethod
    def init_from_save(cls, save_data: SaveData) -> Self:
        """
        Alternate way to create a Play state by using the save data. This allows the player to
        continue right from where they left off before they closed the application.
        """

        self = cls.__new__(cls)
        super().__init__(self)
        self._setup()
        self.__setup_level(save_data.level_name)
        self._setup_game_objects()

        object_dict = {}

        for entity_data in save_data.entity_data:
            entity = GameObject.init_from_data(entity_data)
            self.entities.add(entity)
            if isinstance(entity, Asteroid):
                self.asteroids.add(entity)
            if isinstance(entity, PowerupCollectable):
                self.powerups.add(entity)
            elif isinstance(entity, PlayerShip):
                self.spaceship = entity

            object_dict[entity_data["id"]] = entity
        
        self.spaceship.set_score_limit(self.__level_data.score_range[1])

        self.camera.set_position(save_data.camera_pos)
        
        for entity in self.entities.sprites():
            entity.post_init_from_data(object_dict)

        self.__display_score = save_data.score

        self.__hud_timer.end()

        if self.spaceship.score >= self.__level_data.score_range[1]:
            self.__level_cleared = True

        return self



    def _setup(self) -> None:
        "Called by all initializers to set up needed attributes. Spaceship needs to be made separately."

        self.__display_score = 0
        self.highscore = data.load_highscore()

        self.__prev_highscore = self.highscore
        self.highscore_changed = False
        self.__progress_bar = hud.ProgressBar()
        
        self.__hud_timer = Timer(10).start()
        self.__lvl_transition_timer = Timer(60)
        self.__object_spawn_delay = Timer(15)
        self._game_over_timer = Timer(27, False, self._game_over)

        self.__level_cleared = False



    def __setup_level(self, level_name: str) -> None:
        "Assigned attributes related to the current level."

        self.__level_data = data.load_level(level_name)

        self.__parl_a: pg.Surface | None
        self.__parl_b: pg.Surface | None

        if self.__level_data.parl_a is None:
            self.__parl_a = None
        else:
            self.__parl_a = assets.load_texture(self.__level_data.parl_a, self.__level_data.background_palette)
        
        if self.__level_data.parl_b is None:
            self.__parl_b = None
        else:
            self.__parl_b = assets.load_texture(self.__level_data.parl_b, self.__level_data.background_palette)


    def _setup_game_objects(self) -> None:
        "Creates all the object groups and the camera."

        self.entities = ObjectGroup(host_state=self)
        self.spawned_entities = self.entities.make_subgroup()

        self.asteroids: ObjectGroup[Asteroid] = self.spawned_entities.make_subgroup()
        self.powerups: ObjectGroup[PowerupCollectable] = self.spawned_entities.make_subgroup()
        self.enemies = self.spawned_entities.make_subgroup()

        self.camera = Camera((0, 0))




    def userinput(self, inputs):
        if debug.DEBUG_MODE:
            if inputs.keyboard_mouse.tap_keys[pg.K_r]:
                self.spaceship.position = pg.Vector2(200, 150)
                self.spaceship.set_velocity((0, 0))

            keyboard = inputs.keyboard_mouse

            if keyboard.tap_keys[pg.K_k]:
                if keyboard.hold_keys[pg.KMOD_SHIFT]:
                    self.spaceship.kill()
                    if self.spaceship.health:
                        self.spaceship.force_kill()
                else:
                    for asteroid in self.asteroids.sprites():
                        self.spaceship.score += asteroid.points
                        asteroid.kill(False)

            if keyboard.tap_keys[pg.K_b]:
                self.spaceship.score += 100

            if keyboard.tap_keys[pg.K_c]:
                self.spaceship.combo *= 2

            if keyboard.tap_keys[pg.K_x]:
                self.entities.add(EnemyShip((0, -400)))
                print(f"Spawned EnemyShip")


            if keyboard.tap_keys[pg.K_t]:
                self.reinit_next_level(self.__level_data.next_level)
                self.spaceship.score = self.__level_data.score_range[0]

            if keyboard.tap_keys[pg.K_g]:
                debug.Cheats.show_bounding_boxes = not debug.Cheats.show_bounding_boxes


        self.spaceship.userinput(inputs)

        if self.spaceship.health and inputs.check_input("pause"):
            self._pause_game()


    


    def update(self):
        if self.__lvl_transition_timer.complete:
            if self.spaceship.health:
                # The game loop runs as long as the player ship is alive.
                self._game_loop()
            elif self._game_over_timer.complete:
                # Adds a pause between when the player dies and the game over screen is shown.
                # The timer automatically calls the game over scree once complete.
                self._game_over_timer.start()

                self.camera.clear_velocity()

                for entity in self.entities.sprites():
                    # Bullets are deleted immediately
                    if isinstance(entity, Projectile):
                        entity.force_kill()
                        continue
                    
                    if isinstance(entity, components.ObjectVelocity):
                        entity.clear_velocity()
                    if isinstance(entity, Asteroid):
                        entity.set_angular_vel(0)
            
            else:
                self.entities.update(self.camera.position)
                if self.is_top_state():
                    self._game_over_timer.update()
        
        self._join_sound_queue(self.entities.clear_sound_queue())
            
        self.__lvl_transition_timer.update()
        if self.__lvl_transition_timer.complete:
            self.__hud_timer.update()
            self.__object_spawn_delay.update()

        






    def draw(self, surface, lerp_amount=0.0):
        # if self.spaceship.get_velocity().magnitude_squared() < 1500:
        
        if data.get_setting("motion_blur") and self.is_top_state():
            surface.fill((70, 70, 70), special_flags=pg.BLEND_RGB_SUB)
            surface.fill(self.__level_data.base_color, special_flags=pg.BLEND_RGB_ADD)
        else:
            surface.fill(self.__level_data.base_color)

        if not debug.Cheats.ignore_colorkey:
            self._draw_scrolling_background(surface, lerp_amount)

        if self.__lvl_transition_timer.complete:
            self.camera.capture(surface, self.entities, lerp_amount)



        if self.spaceship.health: # type: ignore
            self._draw_hud(surface)




    def debug_info(self) -> str | None:
        return f"level: {self.__level_data.level_name}, entity count: {self.entities.count()}, asteroids_density: {self.__asteroid_density()}/{self.__required_asteroid_density()}, combo: {self.spaceship.combo:.1f}, camera: ({self.camera.position.x:.0f}, {self.camera.position.y:.0f})"












    def _draw_scrolling_background(self, surface: pg.Surface, lerp_amount=0.0) -> None:
        # Background B
        if self.__parl_b is not None:
            width, height = self.__parl_b.size
            camera_offset = -self.camera.lerp_position(lerp_amount)*0.1
            camera_offset = pg.Vector2(camera_offset[0]%width, camera_offset[1]%height)
            for x in range(-1, surface.width//width+1):
                for y in range(-1, surface.height//height+1):
                    surface.blit(self.__parl_b, (width*x, height*y)+camera_offset)

        # Background A
        if self.__parl_a is not None:
            width, height = self.__parl_a.size
            camera_offset = -self.camera.lerp_position(lerp_amount)*0.3
            camera_offset = pg.Vector2(camera_offset[0]%width, camera_offset[1]%height)
            for x in range(-1, surface.width//width+1):
                for y in range(-1, surface.height//height+1):
                    surface.blit(self.__parl_a, (width*x, height*y)+camera_offset)



    def _draw_hud(self, surface: pg.Surface) -> None:
        if not self.__hud_timer.complete:
            entrance_offset = 80*(self.__hud_timer.countdown*0.1)**2
        else:
            entrance_offset = 0
        
        y_offset = 6
        if self.__prev_highscore:
            self.__show_scores(surface, "Highscore", self.highscore, (10, y_offset-entrance_offset), (self.highscore > self.__display_score or self.__display_score == self.spaceship.score))
            y_offset += 16
        
        self.__show_scores(surface, "Score", self.__display_score, (10, y_offset-entrance_offset), self.__display_score == self.spaceship.score)
        y_offset += 22

        if self.__level_data.level_name != "level_1":
            surface.blit(self.__progress_bar.render(level_completion_amount(self.__display_score, self.__level_data.score_range)), (10, y_offset-entrance_offset))
        

        if self.is_top_state():
            surface.blit(font.font_with_icons.render("Pause<pause>"), (10, surface.height-18+entrance_offset))





    def _game_loop(self):
        if not self.__level_cleared:
            # Asteroid Spawning
            if not debug.Cheats.no_obstacles:
                if self.__should_spawn_asteroid():
                    self.__spawn_asteroid()

                if self.__should_spawn_enemy():
                    self.__spawn_enemy()

            if self.__should_spawn_powerup():
                self.__spawn_powerup()             
            
            # Stops objects from spawning once the level has been cleared
            if self.spaceship.score >= self.__level_data.score_range[1]:
                self.__level_cleared = True
                ShowText("Level Cleared").add_to_stack(self.state_stack)
                self.__delete_offscreen_spawned_entities()
        
        else:
            if self.spaceship.get_velocity().magnitude_squared() > 5000:
                self.reinit_next_level(self.__level_data.next_level)


        # Removes any asteroids beyond the despawn radius
        for obj in self.spawned_entities.sprites():
            if obj.distance_to(self.spaceship) > self.__despawn_radius:
                obj.force_kill()

        self._update_game_objects()

        # Records wether the highscore has changed.
        if not self.highscore_changed and self.spaceship.score > self.highscore:
            self.highscore_changed = True
        prev_score = self.__display_score
        self.__display_score = increment_score(self.__display_score, self.spaceship.score)
        self.highscore = max(self.highscore, self.__display_score)

        if self.__display_score > prev_score:
            self._queue_sound("game.point", 0.3)



    def _update_game_objects(self) -> None:
        self.entities.update(self.camera.position)
        self.camera.set_target(self.spaceship.position + self.spaceship.get_velocity()*2)
        self.camera.update()




    def __add_background_tint(self) -> None:
        BackgroundTint(self.__level_data.background_tint).add_to_stack(self.state_stack)



    def _pause_game(self) -> None:
        "Adds PauseMenu state to state stack as well as some background tint."
        self.__add_background_tint()
        PauseMenu().add_to_stack(self.state_stack)



    def powerup_info(self, powerup: type[PowerUp]) -> None:
        self.__add_background_tint()
        PowerupInfo(powerup).add_to_stack(self.state_stack)

    
    
    def _game_over(self) -> None:
        "Updates the score and shows the game over screen."
        self.__set_score()
        for obj in self.entities.sprites():
            if isinstance(obj, components.ObjectVelocity):
                obj.set_velocity((0, 0))
            
            if isinstance(obj, components.ObjectTexture):
                obj.set_angular_vel(0)

        self.__add_background_tint()
        GameOverScreen(self.__level_data.level_name, (self.__display_score, self.highscore, self.highscore_changed)).add_to_stack(self.state_stack)





    def __get_object_spawn_pos(self) -> pg.Vector2:
        "Returns a random position for objects like asteroids and powerups to spawn offscreen."
        distance_from_center = self.__spawn_radius+self.spaceship.get_speed()*0.3
        return self.camera.position + pg.Vector2(distance_from_center).rotate(random.randint(0, 360))
    
    def __get_object_spawn_velocity(self, start_pos: pg.typing.Point, magnitude: float) -> pg.Vector2:
        "Returns the velocity of an object so that is goes onscreen towards the spaceship."
        velocity = self.camera.position-start_pos
        velocity.scale_to_length(magnitude)
        velocity.rotate_ip(random.randint(-40, 40))
        return velocity




    def __should_spawn_asteroid(self) -> bool:
        "Returns wether an asteroid should spawn in the tick."
        return (self.__level_data.spawn_asteroids
                and self.__object_spawn_delay.complete
                and self.__required_asteroid_density() > self.__asteroid_density()
                and random.random() < self.__level_data.asteroid_frequency)

    def __spawn_asteroid(self) -> None:
        spawn_pos = self.__get_object_spawn_pos()
        velocity = self.__get_object_spawn_velocity(spawn_pos, self.__get_asteroid_speed())
        asteroid_id = weighted_choice(self.__level_data.asteroid_spawn_weights)

        asteroid = Asteroid(
            spawn_pos,
            velocity,
            asteroid_id
        )

        for a in self.asteroids.sprites():
            if asteroid.collides_with(a):
                try:
                    return self.__spawn_asteroid()
                except RecursionError:
                    print(f"Failed to spawn asteroid a {spawn_pos}")
                    return None

        self.asteroids.add(asteroid)


    def __should_spawn_enemy(self) -> bool:
        "Returns wether an enemy should spawn in the tick."
        return (self.__level_data.spawn_enemies
                and self.__object_spawn_delay.complete
                and self.enemies.count() < self.__level_data.enemy_count
                and random.random() < self.__level_data.enemy_frequency)

    def __spawn_enemy(self) -> None:
        spawn_pos = self.__get_object_spawn_pos()
        self.enemies.add(EnemyShip(spawn_pos))
    



    def __should_spawn_powerup(self) -> bool:
        "Returns wether a powerup should spawn in the tick."
        return (self.__level_data.spawn_powerups
                and self.__object_spawn_delay.complete
                and self.powerups.count() == 0
                and random.random() < self.__level_data.powerup_frequency)
    
    def __spawn_powerup(self) -> None:
        powerups_name = weighted_choice(self.__level_data.powerup_spawn_weights)
        if not self.spaceship.has_powerup(powerups_name):
            spawn_pos = self.__get_object_spawn_pos()
            velocity = self.__get_object_spawn_velocity(spawn_pos, 2)
            self.powerups.add(PowerupCollectable(spawn_pos, velocity, powerups_name))



    def __show_scores(self, surface: pg.Surface, name: str, score: int, offset: pg.typing.Point, cache=True):
        score_text = f"{score:05}"

        score_desc_surf = font.small_font.render(name)
        surface.blit(score_desc_surf, offset+pg.Vector2(0, 8))
        surface.blit(font.large_font.render(score_text, cache=cache), offset+pg.Vector2(score_desc_surf.width+max(40-score_desc_surf.width, 0), 0))
    

    def __get_relative_score(self) -> int:
        return max(self.__display_score-self.__level_data.score_range[0], 0)


    def __get_increment_percent(self) -> float:
        return (self.__get_relative_score())/(self.__level_data.score_range[1]-self.__level_data.score_range[0])


    def __required_asteroid_density(self) -> int:

        "Required asteroid density based on the player's score. Used to determine wether to spawn more asteroids."
        asteroid_density = self.__level_data.asteroid_density[0]
        asteroid_density += (self.__level_data.asteroid_density[1]-self.__level_data.asteroid_density[0])*self.__get_increment_percent()
        return math.ceil(asteroid_density)

    def __get_asteroid_speed(self) -> float:
        "Gets a random speed for the asteroid based on the current level and the player's score."
        asteroid_speed = self.__level_data.asteroid_speed[0]
        asteroid_speed += (self.__level_data.asteroid_speed[1]-self.__level_data.asteroid_speed[0])*self.__get_increment_percent()
        asteroid_speed = max(asteroid_speed + random.random()*4 - 2, 1)
        return asteroid_speed
    

    def __asteroid_density(self) -> int:
        "The sum of the points of all asteroids loaded in."
        return sum(asteroid.size for asteroid in self.asteroids if asteroid.distance_to(self.spaceship) < self.__visible_radius)


    def __delete_offscreen_spawned_entities(self) -> None:
        for obj in self.spawned_entities.sprites():
            if not obj.rect.colliderect(self.camera.get_visible_area(config.PIXEL_WINDOW_SIZE)):
                obj.force_kill()
                
    

    def __set_score(self) -> None:
        "Updates the score to match the value stored in the spaceship object. Changes highscore if score is larger."
        self.__display_score = min(self.spaceship.score, self.__score_limit)
        self.highscore = max(self.highscore, self.__display_score)

    
        



    def __save_progress(self) -> None:
        "Saves the current state of the game to a save file."
        entity_data = [entity.get_data()
                       for entity in self.entities.sprites()
                       
                       if entity.progress_save_key is not None]
        
        camera_pos = tuple(self.camera.position)
        save_data = SaveData(self.__level_data.level_name, self.spaceship.score, camera_pos, entity_data)
        data.save_progress(save_data)





    def quit(self) -> None:
        # Don't dave any data if the player has no points
        if self.spaceship.score:
            self.__set_score()
            data.save_highscore(self.highscore)

            if self.spaceship.health:
                self.__save_progress()
            else:
                data.delete_progress()

            self.entities.kill_all()