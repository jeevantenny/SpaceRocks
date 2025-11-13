"Contains the Play state that handles the actual Gameplay."

import pygame as pg
from typing import Self
import random

import config
import debug

from src.misc import increment_score, level_completion_amount
from src.custom_types import SaveData, Timer
from src.file_processing import assets, data

from src.game_objects import GameObject, ObjectGroup, components
from src.game_objects.entities import PlayerShip, Asteroid, Bullet, EnemyShip
from src.game_objects.camera import Camera

from src.ui import font, elements

from . import State
from .menus import PauseMenu, GameOverScreen
from .visuals import BackgroundTint, ShowLevelName
from .info_states import NoMoreLevels






class Play(State):
    """
    handles the actual Gameplay. Contains a game loop that constantly updates all game objects
    and player score.
    """
    __spawn_radius = 150
    __despawn_radius = 500
    __clear_fov = 60
    __score_limit = 99999

    colors = ["#442200", "#884400", "#993300", "#005588", "#99ddee"]



    def __init__(self, level_name: str):
        "The main initializer that starts a new game on a specific level. Mainly the first level."

        super().__init__()

        self.__setup()
        self.__setup_level(level_name)
        self.__setup_game_objects()

        self.spaceship = PlayerShip((0, 0))
        self.entities.add(self.spaceship)


    def reinit_next_level(self, level_name: str) -> None:
        "Reinitializes the current Play object for the next level without creating another Play object."

        try:
            self.__setup_level(level_name)
        except ValueError:
            self.state_stack.push(NoMoreLevels())
            return
        
        self.entities.kill_all()
        self.entities.add(self.spaceship)
        self.spaceship.set_position((0, 0))
        self.spaceship.clear_velocity()
        self.camera.set_position((0, 0))

        self.score = self.spaceship.score
        self.__level_cleared = False
        self.__timer = 10

        ShowLevelName(level_name.replace("_", " ").upper()).add_to_stack(self.state_stack)


    
    @classmethod
    def init_from_save(cls, save_data: SaveData) -> Self:
        """
        Alternate way to create a Play state by using the save data. This allows the player to
        continue right from where they left off before they closed the application.
        """

        self = cls.__new__(cls)
        super().__init__(self)
        self.__setup()
        self.__setup_level(save_data.level_name)
        self.__setup_game_objects()

        object_dict = {}

        for entity_data in save_data.entity_data:
            entity = GameObject.init_from_data(entity_data)
            self.entities.add(entity)
            if isinstance(entity, Asteroid):
                self.asteroids.add(entity)
            elif isinstance(entity, PlayerShip):
                self.spaceship = entity

            object_dict[entity_data["id"]] = entity

        
        for entity in self.entities.sprites():
            entity.post_init_from_data(object_dict)


        self.camera.set_position(self.spaceship.position)
        self.score = save_data.score

        self.__timer = 0

        return self



    def __setup(self) -> None:
        "Called by all initializers to set up needed attributes. Spaceship needs to be made separately."

        self.__info_text = font.small_font.render("")

        self.score = 0
        self.highscore = data.load_highscore()

        self.__prev_highscore = self.highscore
        
        self.highscore_changed = False
        self.__progress_bar = elements.ProgressBar()
        
        self.__game_over_timer = Timer(27, False, self.__game_over)
        self.__level_cleared = False

        self.__timer = 10



    def __setup_level(self, level_name: str) -> None:
        "Assigned attributes related to the current level."

        self.__level_data = data.load_level(level_name)
        self.__base_color = self.__level_data.base_color
        self.__parl_a = assets.load_texture(self.__level_data.parl_a, self.__level_data.background_palette)
        self.__parl_b = assets.load_texture(self.__level_data.parl_b, self.__level_data.background_palette)


    def __setup_game_objects(self) -> None:
        "Assigns all the object groups and the camera."

        self.entities = ObjectGroup()
        self.asteroids: ObjectGroup[Asteroid] = self.entities.make_subgroup()
        self.camera = Camera((0, 0))




    def userinput(self, inputs):
        if debug.debug_mode:
            if inputs.keyboard_mouse.tap_keys[pg.K_r]:
                self.spaceship.position = pg.Vector2(200, 150)
                self.spaceship.set_velocity((0, 0))


            if inputs.keyboard_mouse.tap_keys[pg.K_k]:
                if inputs.keyboard_mouse.hold_keys[pg.KMOD_SHIFT]:
                    self.spaceship.kill()
                else:
                    for asteroid in self.asteroids.sprites():
                        self.spaceship.score += asteroid.points
                        asteroid.kill(False)

            if inputs.keyboard_mouse.tap_keys[pg.K_b]:
                self.spaceship.score += 100

            if inputs.keyboard_mouse.tap_keys[pg.K_c]:
                self.spaceship.combo += 50


            if inputs.keyboard_mouse.tap_keys[pg.K_t]:
                self.reinit_next_level(self.__level_data.next_level)
                self.spaceship.score = self.__level_data.score_range[0]


        if debug.Cheats.enemy_ship and inputs.keyboard_mouse.tap_keys[pg.K_e]:
            self.entities.add(EnemyShip(self.spaceship.position+(0, 20)))


        self.spaceship.userinput(inputs)

        if self.spaceship.health and inputs.check_input("pause"):
            self.__pause_game()


    


    def update(self):
        if self.spaceship.health:
            # The game loop runs as long as the player ship is alive.
            self.__game_loop()
        elif self.__game_over_timer.complete:
            # Adds a pause between when the player dies and the game over screen is shown.
            # The timer automatically calls the game over scree once complete.
            self.__game_over_timer.start()

            # Clears velocity and angular velocity
            self.camera.clear_velocity()
            for entity in self.entities.sprites():
                # Bullets are deleted immediately
                if isinstance(entity, Bullet):
                    entity.force_kill()
                    continue
                
                if isinstance(entity, components.ObjectVelocity):
                    entity.clear_velocity()
                if isinstance(entity, Asteroid):
                    entity.set_angular_vel(0)
        
        else:
            self.entities.update(self.camera.position)
            self.__game_over_timer.update()
        
        self._join_sound_queue(self.entities.clear_sound_queue())
            

        if self.__timer:
            self.__timer -= 1

        self.__info_text = font.font_with_icons.render("Press<pause> to pause")

        






    def draw(self, surface, lerp_amount=0.0):
        surface.fill(self.__base_color)
        self.__draw_scrolling_background(surface, lerp_amount)

        self.camera.capture(surface, self.entities, lerp_amount)



        if self.spaceship.health: # type: ignore
            self.__draw_hud(surface)




    def debug_info(self) -> str | None:
        return f"level: {self.__level_data.level_name}, entity count: {self.entities.count()}, asteroids_density: {self.__asteroid_density()}/{self.__required_asteroid_density():.1f}, cam_x: {self.camera.position.x:.0f}, cam_y: {self.camera.position.y:.0f}"












    def __draw_scrolling_background(self, surface: pg.Surface, lerp_amount=0.0) -> None:
        # Background A
        width, height = self.__parl_b.size
        camera_offset = -self.camera.lerp_position(lerp_amount)*0.1
        camera_offset = pg.Vector2(camera_offset[0]%width, camera_offset[1]%height)
        for x in range(-1, surface.width//width+1):
            for y in range(-1, surface.height//height+1):
                surface.blit(self.__parl_b, (width*x, height*y)+camera_offset)

        # Background B
        width, height = self.__parl_a.size
        camera_offset = -self.camera.lerp_position(lerp_amount)*0.3
        camera_offset = pg.Vector2(camera_offset[0]%width, camera_offset[1]%height)
        for x in range(-1, surface.width//width+1):
            for y in range(-1, surface.height//height+1):
                surface.blit(self.__parl_a, (width*x, height*y)+camera_offset)



    def __draw_hud(self, surface: pg.Surface) -> None:
        if self.__timer:
            entrance_offset = 80*(self.__timer*0.1)**2
        else:
            entrance_offset = 0
        
        y_offset = 6
        if self.__prev_highscore:
            self.__show_scores(surface, "highscore", self.highscore, (10, y_offset-entrance_offset), (self.highscore > self.score or self.score == self.spaceship.score))
            y_offset += 16
        
        self.__show_scores(surface, "score", self.score, (10, y_offset-entrance_offset), self.score == self.spaceship.score)
        y_offset += 22

        if self.__level_data.level_name != "level_1":
            surface.blit(self.__progress_bar.render(level_completion_amount(self.score, self.__level_data.score_range)), (10, y_offset-entrance_offset))
        

        if self.is_top_state():
            surface.blit(self.__info_text, (10, surface.height-20+entrance_offset))





    def __game_loop(self):
        if not self.__level_cleared:
            if not debug.Cheats.no_asteroids and self.__should_spawn_on_tick():
                self.__spawn_asteroid()
            
            # Moves to next level once the player has gained enough points to complete the current one.
            if self.spaceship.score >= self.__level_data.score_range[1]:
                self.__level_cleared = True
                self.__delete_offscreen_asteroids()
        
        else:
            if len(self.asteroids) == 0:
                self.reinit_next_level(self.__level_data.next_level)


        # Removes any asteroids beyond the despawn radius
        for asteroid in self.asteroids.sprites():
            if asteroid.distance_to(self.spaceship) > self.__despawn_radius:
                asteroid.force_kill()


        self.entities.update(self.camera.position)
        self.camera.set_target(self.spaceship.position + self.spaceship.get_velocity()*2)
        self.camera.update()

        # Records wether the highscore changes self.highscore will be incremented along with the score.
        if not self.highscore_changed and self.spaceship.score > self.highscore:
            self.highscore_changed = True
        prev_score = self.score
        self.score = increment_score(self.score, self.spaceship.score)
        self.highscore = max(self.highscore, self.score)

        if self.score > prev_score:
            self._queue_sound("game.point", 0.3)






    def __pause_game(self) -> None:
        "Adds PauseMenu state to state stack as well as some background tint."
        BackgroundTint(self.__level_data.background_tint).add_to_stack(self.state_stack)
        PauseMenu().add_to_stack(self.state_stack)

    
    
    def __game_over(self) -> None:
        "Updates the score and shows the game over screen."
        self.__set_score()
        for obj in self.entities.sprites():
            if isinstance(obj, components.ObjectVelocity):
                obj.set_velocity((0, 0))
            
            if isinstance(obj, components.ObjectTexture):
                obj.set_angular_vel(0)

        BackgroundTint(self.__level_data.background_tint).add_to_stack(self.state_stack)
        GameOverScreen(self.__level_data, (self.score, self.highscore, self.highscore_changed)).add_to_stack(self.state_stack)







    def __spawn_asteroid(self) -> None:
        start_position = pg.Vector2()

        distance_from_center = self.__spawn_radius+self.spaceship.get_speed()*0.3
        start_position = self.camera.position + pg.Vector2(distance_from_center).rotate(random.randint(0, 360))

        if random.random() < self.score*0.00002:
            target_pos = self.spaceship.position
        else:
            target_pos = self.camera.position

        # Make asteroid target spaceship with some deviation
        velocity = target_pos-start_position
        velocity.scale_to_length(self.__get_asteroid_speed())
        velocity.rotate_ip(random.randint(-40, 40))

        asteroid_id = random.choices(*self.__level_data.asteroid_spawn_weights, k=1)[0]

        asteroid = Asteroid(
            start_position,
            velocity,
            asteroid_id
        )

        self.asteroids.add(asteroid)



    def __should_spawn_on_tick(self) -> bool:
        return (random.random() < self.__level_data.asteroid_frequency
                and self.__required_asteroid_density() > self.__asteroid_density()
)


    def __show_scores(self, surface: pg.Surface, name: str, score: int, offset: pg.typing.Point, cache=True):
        score_text = f"{score:05}"

        score_desc_surf = font.small_font.render(name.capitalize())
        surface.blit(score_desc_surf, offset+pg.Vector2(0, 8))
        surface.blit(font.large_font.render(score_text, cache=cache), offset+pg.Vector2(score_desc_surf.width+max(40-score_desc_surf.width, 0), 0))
    

    def __get_relative_score(self) -> int:
        return max(self.score-self.__level_data.score_range[0], 0)


    def __get_increment_percent(self) -> float:
        return (self.__get_relative_score())/(self.__level_data.score_range[1]-self.__level_data.score_range[0])


    def __required_asteroid_density(self) -> float:
        "Required asteroid density based on the player's score. Used to determine wether to spawn more asteroids."
        asteroid_density = self.__level_data.asteroid_density[0]
        asteroid_density += (self.__level_data.asteroid_density[1]-self.__level_data.asteroid_density[0])*self.__get_increment_percent()
        return asteroid_density

    def __get_asteroid_speed(self) -> float:
        "Gets a random speed for the asteroid based on the current level and the player's score."
        asteroid_speed = self.__level_data.asteroid_speed[0]
        asteroid_speed += (self.__level_data.asteroid_speed[1]-self.__level_data.asteroid_speed[0])*self.__get_increment_percent()
        asteroid_speed = max(asteroid_speed + random.random()*4 - 2, 1)
        return asteroid_speed
    

    def __asteroid_density(self) -> int:
        "The sum of the points of all asteroids loaded in."
        return sum(asteroid.size for asteroid in self.asteroids if asteroid.distance_to(self.spaceship) < 300)


    def __delete_offscreen_asteroids(self) -> None:
        for asteroid in self.asteroids.sprites():
            if not asteroid.colliderect(self.camera.get_visible_area(config.PIXEL_WINDOW_SIZE)):
                asteroid.force_kill()
                
    

    def __set_score(self) -> None:
        "Updates the score to match the value stored in the spaceship object. Changes highscore if score is larger."
        self.score = min(self.spaceship.score, self.__score_limit)
        self.highscore = max(self.highscore, self.score)

    
        



    def __save_progress(self) -> None:
        "Saves the current state of the game to a save file."
        entity_data = [entity.get_data()
                       for entity in self.entities.sprites()
                       
                       if entity.save_entity_progress]
        
        save_data = SaveData(self.__level_data.level_name, self.spaceship.score, entity_data)
        data.save_progress(save_data)





    def quit(self) -> None:
        # Don't dave any data if the player has no points
        if not self.spaceship.score:
            return
        
        self.__set_score()
        # Saves the current state of the game if the player has scored points and had not died.
        data.save_highscore(self.highscore)
        if self.spaceship.health:
            self.__save_progress()

        # If not it will save the highscore.
        else:
            data.delete_progress()
        self.entities.kill_all()