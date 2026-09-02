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

from src.game_objects import asteroids, camera, components, enemies, powerups, particles, spaceship

from src.ui import font, hud, blit_to_center

from .menus import PauseMenu, GameOverScreen
from .info_states import PowerupInfo
from .visuals import ShowText
from .play import Play







class PlayLevel(Play):
    """
    Plays a through a level by passing the level name as the argument. Once the level is complete
    the player will move on to the next level as defined in the level data of the current level.
    """

    def __init__(self, level_name: str):
        "The main initializer that starts a new game on a specific level. Mainly the first level."

        super().__init__()
        self._setup_level(level_name)
        self._setup_hud()
        self._score = self._level_data.score_range[0]


    def __reinit_for_level(self, level_name: str) -> None:
        "Reinitializes the current Play object for the next level without creating another Play object."

        if level_name == "boss_level":
            self.state_stack.quit()
            from .boss_level import PlayBossLevel
            PlayBossLevel().add_to_stack(self.state_stack)
            return
        
        self.__asteroid_timer.stop()
        self.__enemy_timer.stop()
        self.__powerup_timer.stop()
        self._setup_level(level_name)
        
        # Remove all entities except player
        self.entities.remove(self.spaceship)
        self.entities.kill_all()
        self.entities.add(self.spaceship)

        # Reset Player and score
        self.spaceship.set_position((0, 0))
        self.spaceship.set_velocity(self.spaceship.get_rotation_vector()*10)
        self._score = self._level_data.score_range[0]
        self._player_lives = self._player_max_lives
        self.reset_point_combo()
        self.__prev_powerups = len(self.spaceship.get_powerup_group())

        # Reset Camera
        self._camera.set_position((0, 0))
        self._camera.reset_motion()

        # Reset Timers
        self.__lvl_transition_timer.restart()
        self.__hud_timer.restart()
        self._object_spawn_delay.restart()

        self.__level_cleared = False

        ShowText(level_name.replace("_", " ").upper()).add_to_stack(self.state_stack)


    
    @classmethod
    def init_from_save(cls, save_data: SaveData) -> Self:
        self = super().init_from_save(save_data)
        self._setup_level(save_data.level_name)
        self._setup_hud()

        self.__asteroid_timer.set_duration(save_data.game_stats.get("asteroid_timer", 0))
        self.__enemy_timer.set_duration(save_data.game_stats.get("enemy_timer", 0))
        self.__powerup_timer.set_duration(save_data.game_stats.get("powerup_timer", 0))
        self.__prev_powerups = save_data.game_stats.get("prev_powerups", 0)

        self.__display_score = save_data.score
        self.__hud_timer.stop()

        if self._score >= self._level_data.score_range[1]:
            self.__level_cleared = True

        return self


    def _setup(self):
        super()._setup()

        self.highscore = data.load_highscore()
        self.__prev_highscore = self.highscore
        self.highscore_changed = False
        self.__level_cleared = False
        self.__prev_powerups = 0
        
        self.__lvl_transition_timer = Timer(60)
        self.__hyperdrive_spawn_timer = Timer(60, False, self._spawn_hyperdrive_powerup)

    
    def _setup_game_objects(self):
        super()._setup_game_objects()
        self.__asteroid_timer = Timer(0, True, self.__spawn_asteroid)
        self.__enemy_timer = Timer(0, True, self.__spawn_enemy)
        self.__powerup_timer = Timer(0, False)


    def _setup_level(self, level_name):
        super()._setup_level(level_name)
        if self._level_data.asteroid_interval:
            self.__asteroid_timer.set_duration(random.randint(*self._level_data.asteroid_interval))
            self.__asteroid_timer.start()

        if self._level_data.enemy_interval:
            self.__enemy_timer.set_duration(random.randint(*self._level_data.enemy_interval))
            self.__enemy_timer.start()

        if self._level_data.powerup_interval:
            self.__powerup_timer.set_duration(random.randint(*self._level_data.powerup_interval))
            self.__powerup_timer.start()


    def _setup_hud(self) -> None:
        self.__display_score = 0
        self.__hud_timer = Timer(10).start()
        self.__progress_bar = hud.ProgressBar()
        self.__lives_indicator = hud.LivesIndicator(self._player_max_lives)
        self.__powerup_list = hud.PowerupList(self.spaceship.get_powerup_group())
        self.__hud_message = hud.HudMessage()


    
    def userinput(self, inputs):
        super().userinput(inputs)

        if debug.DEBUG_MODE:
            if inputs.keyboard_mouse.tap_keys[pg.K_b]:
                if inputs.keyboard_mouse.hold_keys[pg.KMOD_SHIFT]:
                    self.add_points(1000)
                else:
                    self.add_points(100)

            if inputs.keyboard_mouse.tap_keys[pg.K_t]:
                self.__reinit_for_level(self._level_data.next_level)



    def update(self):
        self.__lvl_transition_timer.update()
        if self.__lvl_transition_timer.complete:
            super().update()
            self.__process_score()
            self.__hud_timer.update()
            self.__hud_message.update()
            self.__hyperdrive_spawn_timer.update()
            



    def draw(self, surface, lerp_amount=0.0):
        self._draw_base(surface)

        if not debug.Cheats.ignore_colorkey:
            self._draw_scrolling_background(surface, self.__lvl_transition_timer.complete and lerp_amount)

        if self.__lvl_transition_timer.complete:
            self._draw_entities(surface, lerp_amount)# if self.spaceship.health else 1)


        if ((isinstance(self.state_stack.top_state, (PauseMenu, ShowText)) or self.is_top_state())
            and self._player_lives):
            self._draw_hud(surface)




    def debug_info(self):
        return (
            f"level: {self._level_data.level_name}, {super().debug_info()}\n"
            f"asteroids: {len(self.asteroids):02};{self.__asteroid_timer.countdown:02.0f}, "
            f"enemies: {len(self.enemies):02};{self.__enemy_timer.countdown:02.0f}, "
            f"powerups: {len(self.powerups):02};{self.__powerup_timer.countdown:02.0f}, "
            f"asteroid_density: {self.__asteroid_density()}/{self.__required_asteroid_density()}"
        )




    def hud_message(self, message, duration=40):
        self.__hud_message.queue_message(message, duration)
    

    def player_damage_obstacle(self, obstacle, point_combo=True):
        super().player_damage_obstacle(obstacle, point_combo)
        if obstacle.has_health() or self.__level_cleared:
            return
        if self._score >= self._level_data.score_range[1]:
            if self.__hyperdrive_spawn_timer.complete:
                self.slowmo_effect(7)
                self.camera_shake(0.7, 12)
                self.__hyperdrive_spawn_timer.start()
                self.entities.add(particles.Shockwave(obstacle.position, 300, 10))
        elif (self._level_data.spawn_powerups
              and (self.__powerup_timer.complete or debug.Cheats.abundant_powerups)
              and obstacle.drop_powerup):
            self.__spawn_powerup(obstacle.position)


    def start_next_level(self):
        self.__reinit_for_level(self._level_data.next_level)






    def _draw_hud(self, surface: pg.Surface) -> None:
        if not self.__hud_timer.complete:
            entrance_offset = 80*(self.__hud_timer.countdown*0.1)**2
        else:
            entrance_offset = 0
        
        y_offset = 6

        # Show highscore if it is not 0
        if self.__prev_highscore:
            self.__show_scores(surface, "Highscore", self.highscore, (10, y_offset-entrance_offset), (self.highscore > self.__display_score or self.__display_score == self._score))
            y_offset += 16
        
        # Show score
        self.__show_scores(surface, "Score", self.__display_score, (10, y_offset-entrance_offset), self.__display_score == self._score)
        y_offset += 22

        # Show progress bar from level_2 onwards
        if self._level_data.level_name != "level_1":
            surface.blit(self.__progress_bar.render(level_completion_amount(self.__display_score, self._level_data.score_range)), (10, y_offset-entrance_offset))

        # Show lives indicator
        lives_render = self.__lives_indicator.render(self._player_lives)
        surface.blit(lives_render, (surface.width-lives_render.width-10, 10-entrance_offset))

        # Show powerups
        if self.spaceship.health:
            output = self.__powerup_list.render()
            if output is not None:
                surface.blit(
                    output,
                    pg.Vector2(surface.size)-self.__powerup_list.size+(entrance_offset*1.5, -6)
                )
        
        # Show hud message if any
        output = self.__hud_message.render()
        if output is not None:
            blit_to_center(output, surface, (0, surface.height*0.5 - 50))
        

        if self.is_top_state():
            surface.blit(font.icon_font.render("Pause<pause>"), (10, surface.height-18+entrance_offset))




    def _game_loop(self):
        if not self.__level_cleared:
            if self._object_spawn_delay.complete:
                self.__do_object_spawning()  
            
            # Stops objects from spawning once the level has been cleared
            if self._score >= self._level_data.score_range[1]:
                self.__level_cleared = True
                self.hud_message("Level Cleared")
                if self.__hyperdrive_spawn_timer.complete:
                    self._spawn_hyperdrive_powerup()

                for asteroid in self.asteroids.sprites():
                    asteroid.kill(False)

        super()._game_loop()



    def __process_score(self) -> None:
        """Increment display score towards the actual score and track wether the highscore has changed"""
        if not self.highscore_changed and self._score > self.highscore:
            self.highscore_changed = True
        prev_score = self.__display_score
        self.__display_score = increment_score(self.__display_score, self._score)
        self.highscore = max(self.highscore, self.__display_score)

        if self.__display_score > prev_score:
            self._queue_sound("game.point", 0.3)



    def _freeze_gameplay(self):
        return super()._freeze_gameplay() or not self.__lvl_transition_timer.complete
    

    def _respawn_player(self):
        super()._respawn_player()
        self.__powerup_list.update_powerup_group(self.spaceship.get_powerup_group())

    
    
    def _game_over(self) -> None:
        "Updates the score and shows the game over screen."
        self.stop_slowmo_effect()
        if debug.Cheats.instant_restart:
            self.state_stack.quit()
            from src.states.init_state import Initializer
            Initializer.main_gameplay(self.state_stack)
            return

        for obj in self.entities.sprites():
            if isinstance(obj, components.ObjectVelocity):
                obj.set_velocity((0, 0))
            
            if isinstance(obj, components.ObjectTexture):
                obj.set_angular_vel(0)

        self.__set_score()
        GameOverScreen(self._level_data.level_name, (self.__display_score, self.highscore, self.highscore_changed)).add_to_stack(self.state_stack)




    def __do_object_spawning(self) -> None:
        if not debug.Cheats.no_obstacles:
            if (self._level_data.spawn_asteroids
                and self.__required_asteroid_density() > self.__asteroid_density()):
                self.__asteroid_timer.update()
            
            if (self._level_data.spawn_enemies
                and self.enemies.count() < self._level_data.enemy_count):
                self.__enemy_timer.update()

        if (self._level_data.spawn_powerups
            and len(self.powerups) + len(self.spaceship.get_powerup_group()) - self.__prev_powerups < len(self._level_data.powerup_spawn_weights[0])):
            self.__powerup_timer.update()
            self.__prev_powerups = min(len(self.spaceship.get_powerup_group()), self.__prev_powerups)


    def __spawn_asteroid(self) -> None:
        spawn_pos = self._get_object_spawn_pos()
        velocity = self._get_object_spawn_velocity(spawn_pos, self.__get_asteroid_speed())
        asteroid_id = weighted_choice(self._level_data.asteroid_spawn_weights)
        asteroid = asteroids.Asteroid(spawn_pos, velocity, asteroid_id)

        for a in self.asteroids.sprites():
            if asteroid.collides_with(a):
                try:
                    return self.__spawn_asteroid()
                except RecursionError:
                    print("Failed to spawn asteroid")
                    return

        self.asteroids.add(asteroid)
        self.__asteroid_timer.set_duration(random.randint(*self._level_data.asteroid_interval))


    def __spawn_enemy(self) -> None:
        spawn_pos = self._get_object_spawn_pos()
        self.enemies.add(enemies.EnemyShip(spawn_pos))
        self.__enemy_timer.set_duration(random.randint(*self._level_data.enemy_interval))


    def __spawn_powerup(self, spawn_pos: pg.typing.Point | None = None) -> None:
        powerups_name = weighted_choice(self._level_data.powerup_spawn_weights)
        if not self.__powerup_exists(powerups_name):
            if spawn_pos is None:
                spawn_pos = self._get_object_spawn_pos()
            velocity = self._get_object_spawn_velocity(spawn_pos, 1, 0)
            powerup = powerups.PowerupCollectable(spawn_pos, velocity, powerups_name)
            self.powerups.add(powerup)
            self.entities.add(camera.ObjectTracker(powerup),
                              particles.Shockwave(spawn_pos, 40, 8, *powerups.PowerUp.powerup_list[powerups_name].colors))
            self.__powerup_timer.set_duration(random.randint(*self._level_data.powerup_interval))
            self.__powerup_timer.restart()
    
    def __powerup_exists(self, powerup_name: str) -> bool:
        """Determine if the player currently has the powerup or the collectable for it is spawned in"""
        if self.spaceship.has_powerup(powerup_name):
            return True
        for powerup in self.powerups:
            if powerup.powerup_name == powerup_name:
                return True
        return False


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
        "The sum of the sizes of all asteroids loaded in."
        return sum(asteroid.size for asteroid in self.asteroids if asteroid.within_distance(self.spaceship, self._spawn_radius+40))
                
    

    def __set_score(self) -> None:
        "Updates the score to match the value stored in the spaceship object. Changes highscore if score is larger."
        self.__display_score = self._score
        self.highscore = max(self.highscore, self.__display_score)


    def _get_save_data(self):
        if self.__hyperdrive_spawn_timer.countdown:
            self._spawn_hyperdrive_powerup()

        save_data = super()._get_save_data()
        save_data.add_game_stats(
            asteroid_timer=self.__asteroid_timer.countdown,
            enemy_timer=self.__enemy_timer.countdown,
            powerup_timer=self.__powerup_timer.countdown,
            prev_powerups=self.__prev_powerups
        )
        return save_data



    def quit(self) -> None:
        # Don't dave any data if the player has no points
        if self._score:
            self.__set_score()
            data.save_highscore(self.highscore)

            if self.is_saving_progress:
                data.save_progress(self._get_save_data())
            else:
                data.delete_progress()

            self.entities.kill_all()