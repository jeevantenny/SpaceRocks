import pygame as pg
from typing import Self
import random

import config
import debug

from math_functions import unit_vector
from misc import increment_score
from custom_types import LevelData, SaveData, Timer

from file_processing import assets, data

from game_objects import GameObject, ObjectGroup, components
from game_objects.entities import PlayerShip, Asteroid, Bullet, EnemyShip
from game_objects.camera import Camera

from ui import add_text_padding, font

from . import State, StateStack
from .menus import PauseMenu, GameOverScreen






class Play(State):
    """
    Contains the game-loop which handles the main gameplay.
    """
    __spawn_radius = 200
    __despawn_radius = 1200
    __clear_fov = 60
    __score_limit = 99999



    def __init__(self, level_name: str):
        super().__init__()

        self.__setup(level_name)

        self.spaceship = PlayerShip(self.__center)
        self.entities.add(self.spaceship)

        self._initialized = True


    def reinit_next_level(self, level_name: str) -> None:
        self._initialized = False

        self.entities.remove(self.spaceship)
        self.__setup(level_name)
        self.entities.add(self.spaceship)
        self.score = self.spaceship.score

        self._initialized = True


    
    @classmethod
    def init_from_save(cls, save_data: SaveData) -> Self:
        self = cls.__new__(cls)
        super().__init__(self)
        self.__setup(save_data.level_name)

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

        self._initialized = True

        return self



    def __setup(self, level_name: str) -> None:
        "Initializes Play object with attributes required by all initializers. Spaceship needs to be made separately."
        self.visible_area = pg.Rect(0, 0, *config.PIXEL_WINDOW_SIZE)
        self.world_border = self.visible_area.inflate(100, 100)

        level_data = data.load_level(level_name)

        self.__level_name = level_name
        self.__base_color = level_data["base_color"]
        self.__parl_a = assets.load_texture(level_data["parl_a"])
        self.__parl_b = assets.load_texture(level_data["parl_b"])
        self.__info_text = font.SmallFont.render("")

        self.entities = ObjectGroup()
        self.asteroids = ObjectGroup[Asteroid]()

        self.score = 0
        self.highscore = data.load_highscore()
        self.highscore_changed = False
        
        self.__center = pg.Vector2(config.PIXEL_WINDOW_SIZE)*0.5
        self.camera = Camera(self.__center)

        self.__game_over_timer = Timer(27, False, self.__game_over)

        self.__timer = 10







    def userinput(self, inputs):
        if debug.debug_mode:
            if inputs.keyboard_mouse.action_keys[pg.K_r]:
                self.spaceship.position = pg.Vector2(200, 150)
                self.spaceship.set_velocity((0, 0))


            if inputs.keyboard_mouse.action_keys[pg.K_k]:
                for asteroid in self.asteroids.sprites():
                    self.spaceship.score += asteroid.points
                    asteroid.kill(False)

            if inputs.keyboard_mouse.action_keys[pg.K_p]:
                self.spaceship.score += 1000

            if inputs.keyboard_mouse.action_keys[pg.K_c]:
                self.spaceship.combo += 50


        if debug.Cheats.enemy_ship and inputs.keyboard_mouse.action_keys[pg.K_e]:
            self.entities.add(EnemyShip(self.spaceship.position+(0, 20)))


        self.spaceship.userinput(inputs)

        if self.spaceship.health and inputs.check_input("pause"):
            PauseMenu().add_to_stack(self.state_stack)


    


    def update(self):
        if self.spaceship.health:
            self.__game_loop()
        elif self.__game_over_timer.complete:
            self.__game_over_timer.start()
            self.camera.clear_velocity()
            for entity in self.entities.sprites():
                if isinstance(entity, Bullet):
                    entity.force_kill()
                    continue

                if isinstance(entity, components.ObjectVelocity) and not isinstance(entity, Bullet):
                    entity.clear_velocity()
                if isinstance(entity, Asteroid):
                    entity.set_angular_vel(0)
        
        else:
            self.entities.update(self.camera.position)

        
        self._join_sound_queue(self.entities.clear_sound_queue())
        self.__game_over_timer.update()






    def draw(self, surface, lerp_amount=0.0):
        surface.fill(self.__base_color)
        self.__draw_scrolling_background(surface, lerp_amount)

        self.camera.capture(surface, self.entities, lerp_amount)



        if isinstance(self.state_stack.top_state, (Play, PauseMenu)): # type: ignore
            if self.__timer:
                text_offset = -80*(self.__timer*0.1)**2
            else:
                text_offset = 0
            self.__show_scores(surface, "highscore", self.highscore, (10, 4+text_offset))
            self.__show_scores(surface, "score", self.score, (10, 20+text_offset))

        if self.spaceship.health and self.is_top_state():
            surface.blit(self.__info_text, (10, surface.height-20))





    def debug_info(self) -> str | None:
        return f"entity count: {self.entities.count()}, camera_pos: {self.camera.position}"







    def __draw_scrolling_background(self, surface: pg.Surface, lerp_amount=0.0) -> None:
        # Background A
        width, height = self.__parl_a.size
        camera_offset = -self.camera.lerp_position(lerp_amount)*0.1
        camera_offset = pg.Vector2(camera_offset[0]%width, camera_offset[1]%height)
        for x in range(-1, surface.width//width+1):
            for y in range(-1, surface.height//height+1):
                surface.blit(self.__parl_a, (width*x, height*y)+camera_offset)

        # Background B
        width, height = self.__parl_b.size
        camera_offset = -self.camera.lerp_position(lerp_amount)*0.3
        camera_offset = pg.Vector2(camera_offset[0]%width, camera_offset[1]%height)
        for x in range(-1, surface.width//width+1):
            for y in range(-1, surface.height//height+1):
                surface.blit(self.__parl_b, (width*x, height*y)+camera_offset)





    def __game_loop(self):
        if self.__should_spawn_on_tick():
            self.__spawn_asteroid()

        for asteroid in self.asteroids.sprites():
            if asteroid.distance_to(self.spaceship) > self.__despawn_radius:
                asteroid.force_kill()


        self.entities.update(self.camera.position)

        # enemy_ships = self.entities.get_type(EnemyShip)
        # if enemy_ships:
        #     self.camera.set_target(enemy_ships[0].position)
        # else:
        self.camera.set_target(self.spaceship.position + self.spaceship.get_velocity()*2)
        self.camera.update()


        if not self.highscore_changed and self.spaceship.score > self.highscore:
            self.highscore_changed = True
        prev_score = self.score
        self.score = increment_score(self.score, self.spaceship.score)
        self.highscore = max(self.highscore, self.score)

        if self.score > prev_score:
            self._queue_sound("game.point", 0.3)

        if self.__timer:
            self.__timer -= 1

        self.__info_text = font.FontWithIcons.render("Press<pause> to pause")







    def __spawn_asteroid(self) -> None:
        start_position = pg.Vector2()

        center_offset = pg.Vector2(self.__spawn_radius+self.spaceship.get_velocity().magnitude()*0.3, 0)
        rotation_offset = self.spaceship.get_velocity().angle_to((0, -1))
        center_offset.rotate_ip(random.randint(0, 360-self.__clear_fov)+rotation_offset+self.__clear_fov*0.5)
        start_position = self.camera.position + center_offset

        if random.random() < self.score*0.00002:
            target_pos = self.spaceship.position
        else:
            target_pos = self.camera.position

        velocity = unit_vector(target_pos-start_position)*self.__get_asteroid_speed()
        velocity.rotate_ip(random.randint(-10, 10))

        asteroid = Asteroid(
            start_position,
            velocity,
            random.randint(1, 2) # type: ignore
        )

        self.entities.add(asteroid)
        self.asteroids.add(asteroid)



    def __should_spawn_on_tick(self) -> bool:
        # random.random() < 0.2+self.score*0.02 and 
        return self.__required_asteroid_value() > self.__asteroid_value()



    def __show_scores(self, surface: pg.Surface, name: str, score: int, offset: pg.typing.Point):
        score_text = add_text_padding(str(score), 5, pad_char='0')

        score_desc_surf = font.SmallFont.render(name.capitalize())
        surface.blit(score_desc_surf, offset+pg.Vector2(0, 8))
        surface.blit(font.LargeFont.render(score_text), offset+pg.Vector2(score_desc_surf.width+max(40-score_desc_surf.width, 0), 0))



    def __required_asteroid_value(self) -> int:
        return min(10 + int(self.score/200), 120)
    

    def __get_asteroid_speed(self) -> float:
        return random.random()*self.score*0.005+1
    

    def __asteroid_value(self) -> int:
        return sum(asteroid.size for asteroid in self.asteroids if asteroid.distance_to(self.spaceship) < 300)
    

    def __set_score(self) -> None:
        self.score = min(self.spaceship.score, self.__score_limit)
        self.highscore = max(self.highscore, self.score)

    

    
    
    def __game_over(self) -> None:
        self.__set_score()
        for obj in self.entities.sprites():
            if isinstance(obj, components.ObjectVelocity):
                obj.set_velocity((0, 0))
            
            if isinstance(obj, components.ObjectTexture):
                obj.set_angular_vel(0)

        GameOverScreen((self.score, self.highscore, self.highscore_changed)).add_to_stack(self.state_stack)
        



    def __save_progress(self) -> None:
        entity_data = [entity.get_data()
                       for entity in self.entities.sprites()
                       
                       if entity.save_entity_progress]
        
        save_data = SaveData(self.__level_name, self.spaceship.score, entity_data)
        data.save_progress(save_data)





    def quit(self) -> None:
        self.__set_score()
        if self.spaceship.health and self.spaceship.score:
            self.__save_progress()
        else:
            data.save_highscore(self.highscore)
            data.delete_progress()
        self.entities.kill_all()