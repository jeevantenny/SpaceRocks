"Contains the Play state that handles the actual Gameplay."

import pygame as pg
import math
import random
from typing import Self

import config
import debug

from src.misc import increment_score, level_completion_amount, weighted_choice
from src.custom_types import SaveData, Timer
from src.file_processing import data

from src.game_objects import asteroids, components, enemies, powerups

from src.ui import font, hud

from .menus import GameOverScreen
from .visuals import ShowText
from .info_states import PowerupInfo
from .play import Play







class PlayLevel(Play):
    """
    Plays a through a level by passing the level name as the argument. Once the level is complete
    the player will move on to the next level as defined in the level data of the current level.
    """
    __visible_radius = 230
    __score_limit = 99999

    _player_max_lives = 3

    def __init__(self, level_name: str):
        "The main initializer that starts a new game on a specific level. Mainly the first level."

        super().__init__()
        self._setup_level(level_name)
        self.spaceship.score = self._level_data.score_range[0]
        self.spaceship.set_score_limit(self._level_data.score_range[1])


    def reinit_next_level(self, level_name: str) -> None:
        "Reinitializes the current Play object for the next level without creating another Play object."

        if level_name == "boss_level":
            self.state_stack.quit()
            from .boss_level import PlayBossLevel
            PlayBossLevel().add_to_stack(self.state_stack)
            return
        
        self._setup_level(level_name)
        
        self.entities.remove(self.spaceship)
        self.entities.kill_all()
        self.entities.add(self.spaceship)

        self.spaceship.set_position((0, 0))
        self.spaceship.set_velocity(self.spaceship.get_rotation_vector()*10)
        self.spaceship.set_score_limit(self._level_data.score_range[1])

        self.camera.set_position((0, 0))
        self.camera.reset_motion()

        self.__lvl_transition_timer.restart()
        self.__hud_timer.restart()
        self._object_spawn_delay.restart()

        self.__display_score = self.spaceship.score
        self.__level_cleared = False

        ShowText(level_name.replace("_", " ").upper()).add_to_stack(self.state_stack)


    
    @classmethod
    def init_from_save(cls, save_data: SaveData) -> Self:
        self = super().init_from_save(save_data)
        self._setup_level(save_data.level_name)
        
        self.spaceship.set_score_limit(self._level_data.score_range[1])

        self.__display_score = save_data.score
        self.__hud_timer.stop()

        if self.spaceship.score >= self._level_data.score_range[1]:
            self.__level_cleared = True

        return self


    def _setup(self):
        super()._setup()

        self.__display_score = 0
        self.highscore = data.load_highscore()
        self.__prev_highscore = self.highscore
        self.highscore_changed = False
        self.__progress_bar = hud.ProgressBar()
        
        self.__hud_timer = Timer(10).start()
        self.__lvl_transition_timer = Timer(60)
        self.__level_cleared = False
        self.__lives_indicator = hud.LivesIndicator(self._player_max_lives)


    
    def userinput(self, inputs):
        super().userinput(inputs)

        if debug.DEBUG_MODE:
            if inputs.keyboard_mouse.tap_keys[pg.K_b]:
                self.spaceship.score += 1000

            if inputs.keyboard_mouse.tap_keys[pg.K_t]:
                self.reinit_next_level(self._level_data.next_level)
                self.spaceship.score = self._level_data.score_range[0]



    def update(self):
        self.__lvl_transition_timer.update()
        if self.__lvl_transition_timer.complete:
            super().update()
            self.__hud_timer.update()
            



    def draw(self, surface, lerp_amount=0.0):
        self._draw_base(surface)

        if self._freeze_gameplay():
            lerp_amount = 0.0

        if not debug.Cheats.ignore_colorkey:
            self._draw_scrolling_background(surface, lerp_amount)

        if self.__lvl_transition_timer.complete:
            self._draw_entities(surface, lerp_amount)# if self.spaceship.health else 1)


        if self.spaceship.health or self._player_lives:
            self._draw_hud(surface)




    def debug_info(self) -> str | None:
        return f"level: {self._level_data.level_name}, lives: {self._player_lives}, entity count: {self.entities.count()}, asteroids_density: {self.__asteroid_density()}/{self.__required_asteroid_density()}, combo: {self.spaceship.combo:.1f}, camera: ({self.camera.position.x:.0f}, {self.camera.position.y:.0f})"




    def _draw_hud(self, surface: pg.Surface) -> None:
        if not self.__hud_timer.complete:
            entrance_offset = 80*(self.__hud_timer.countdown*0.1)**2
        else:
            entrance_offset = 0
        
        y_offset = 6

        # Show highscore if it is not 0
        if self.__prev_highscore:
            self.__show_scores(surface, "Highscore", self.highscore, (10, y_offset-entrance_offset), (self.highscore > self.__display_score or self.__display_score == self.spaceship.score))
            y_offset += 16
        
        # Show score
        self.__show_scores(surface, "Score", self.__display_score, (10, y_offset-entrance_offset), self.__display_score == self.spaceship.score)
        y_offset += 22

        # Show progress bar from level_2 onwards
        if self._level_data.level_name != "level_1":
            surface.blit(self.__progress_bar.render(level_completion_amount(self.__display_score, self._level_data.score_range)), (10, y_offset-entrance_offset))

        # Show lives indicator
        lives_render = self.__lives_indicator.render(self._player_lives)
        surface.blit(lives_render, (surface.width-lives_render.width-10, 10-entrance_offset))
        

        if self.is_top_state():
            surface.blit(font.icon_font.render("Pause<pause>"), (10, surface.height-18+entrance_offset))





    def _game_loop(self):
        if not self.__level_cleared:
            self.__do_object_spawning()            
            
            # Stops objects from spawning once the level has been cleared
            if self.spaceship.score >= self._level_data.score_range[1]:
                self.__level_cleared = True
                ShowText("Level Cleared").add_to_stack(self.state_stack)
                # self.__delete_offscreen_spawned_entities()
                for asteroid in self.asteroids.sprites():
                    asteroid.kill(False)
        
        else:
            if self.spaceship.get_velocity().magnitude_squared() > 5000:
                self.reinit_next_level(self._level_data.next_level)


        super()._game_loop()

        # Records wether the highscore has changed.
        if not self.highscore_changed and self.spaceship.score > self.highscore:
            self.highscore_changed = True
        prev_score = self.__display_score
        self.__display_score = increment_score(self.__display_score, self.spaceship.score)
        self.highscore = max(self.highscore, self.__display_score)

        if self.__display_score > prev_score:
            self._queue_sound("game.point", 0.3)


    def _freeze_gameplay(self):
        return super()._freeze_gameplay() or not self.__lvl_transition_timer.complete



    def powerup_info(self, powerup: type[powerups.PowerUp]) -> None:
        PowerupInfo(powerup, self._level_data.background_tint).add_to_stack(self.state_stack)

    
    
    def _game_over(self) -> None:
        "Updates the score and shows the game over screen."
        self.__set_score()
        for obj in self.entities.sprites():
            if isinstance(obj, components.ObjectVelocity):
                obj.set_velocity((0, 0))
            
            if isinstance(obj, components.ObjectTexture):
                obj.set_angular_vel(0)

        GameOverScreen(self._level_data.level_name, (self.__display_score, self.highscore, self.highscore_changed)).add_to_stack(self.state_stack)




    def __do_object_spawning(self) -> None:
        if not debug.Cheats.no_obstacles:
            if self.__should_spawn_asteroid():
                self.__spawn_asteroid()

            if self.__should_spawn_enemy():
                self.__spawn_enemy()

        if self.__should_spawn_powerup():
            self.__spawn_powerup()


    def __should_spawn_asteroid(self) -> bool:
        "Returns wether an asteroid should spawn in the tick."
        return (self._level_data.spawn_asteroids
                and self._object_spawn_delay.complete
                and self.__required_asteroid_density() > self.__asteroid_density()
                and random.random() < self._level_data.asteroid_frequency)


    def __spawn_asteroid(self) -> None:
        spawn_pos = self._get_object_spawn_pos()
        velocity = self._get_object_spawn_velocity(spawn_pos, self.__get_asteroid_speed())
        asteroid_id = weighted_choice(self._level_data.asteroid_spawn_weights)

        asteroid = asteroids.Asteroid(
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
        return (self._level_data.spawn_enemies
                and self._object_spawn_delay.complete
                and self.enemies.count() < self._level_data.enemy_count
                and random.random() < self._level_data.enemy_frequency)


    def __spawn_enemy(self) -> None:
        spawn_pos = self._get_object_spawn_pos()
        self.enemies.add(enemies.EnemyShip(spawn_pos))


    def __should_spawn_powerup(self) -> bool:
        "Returns wether a powerup should spawn in the tick."
        return (self._level_data.spawn_powerups
                and self._object_spawn_delay.complete
                and self.powerups.count() == 0
                and random.random() < self._level_data.powerup_frequency)


    def __spawn_powerup(self) -> None:
        powerups_name = weighted_choice(self._level_data.powerup_spawn_weights)
        if not self.spaceship.has_powerup(powerups_name):
            spawn_pos = self._get_object_spawn_pos()
            velocity = self._get_object_spawn_velocity(spawn_pos, 2)
            self.powerups.add(powerups.PowerupCollectable(spawn_pos, velocity, powerups_name))


    def __show_scores(self, surface: pg.Surface, name: str, score: int, offset: pg.typing.Point, cache=True):
        score_text = f"{score:05}"

        score_desc_surf = font.small_font.render(name)
        surface.blit(score_desc_surf, offset+pg.Vector2(0, 8))
        surface.blit(font.large_font.render(score_text, cache=cache), offset+pg.Vector2(score_desc_surf.width+max(40-score_desc_surf.width, 0), 0))
    

    def __get_relative_score(self) -> int:
        return max(self.__display_score-self._level_data.score_range[0], 0)


    def __get_increment_percent(self) -> float:
        return (self.__get_relative_score())/(self._level_data.score_range[1]-self._level_data.score_range[0])


    def __required_asteroid_density(self) -> int:

        "Required asteroid density based on the player's score. Used to determine wether to spawn more asteroids."
        asteroid_density = self._level_data.asteroid_density[0]
        asteroid_density += (self._level_data.asteroid_density[1]-self._level_data.asteroid_density[0])*self.__get_increment_percent()
        return math.ceil(asteroid_density)

    def __get_asteroid_speed(self) -> float:
        "Gets a random speed for the asteroid based on the current level and the player's score."
        asteroid_speed = self._level_data.asteroid_speed[0]
        asteroid_speed += (self._level_data.asteroid_speed[1]-self._level_data.asteroid_speed[0])*self.__get_increment_percent()
        asteroid_speed = max(asteroid_speed + random.random()*4 - 2, 1)
        return asteroid_speed
    

    def __asteroid_density(self) -> int:
        "The sum of the points of all asteroids loaded in."
        return sum(asteroid.size for asteroid in self.asteroids if asteroid.distance_to(self.spaceship) < self.__visible_radius)


    def __delete_offscreen_spawned_entities(self) -> None:
        for obj in self.spawned_entities.sprites():
            if not obj.rect.colliderect(self.camera.get_visible_area((config.CANVAS_SIDES, config.CANVAS_SIDES))):
                obj.force_kill()
                
    

    def __set_score(self) -> None:
        "Updates the score to match the value stored in the spaceship object. Changes highscore if score is larger."
        self.__display_score = min(self.spaceship.score, self.__score_limit)
        self.highscore = max(self.highscore, self.__display_score)





    def quit(self) -> None:
        # Don't dave any data if the player has no points
        if self.spaceship.score:
            self.__set_score()
            data.save_highscore(self.highscore)

            if self.spaceship.health or self._player_lives:
                self._save_progress()
            else:
                data.delete_progress()

            self.entities.kill_all()