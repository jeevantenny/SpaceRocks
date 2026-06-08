import pygame as pg
import unittest
from unittest.mock import patch, MagicMock

from src.file_processing import assets, data
from src.custom_types import LevelData

from src.game_errors import LevelDataError

import debug
from debug import Cheats



class AssetsTest(unittest.TestCase):
    """
    Test the assets module in file_processing.
    """

    texture_path = "game_objects/medium_rock"
    pallette_swap = "asteroid/green_rocks"
    
    test_sound = "entity.asteroid.small_explode"
    test_music = "test_music"
    test_music_attr = "music/test_folder/house_lo", "music/test_folder/apt"


    @classmethod
    def setUpClass(cls):
        pg.init()
        pg.Window(hidden=True).get_surface()

    @classmethod
    def tearDownClass(cls):
        pg.quit()


    def assertTextureFormat(self, texture: pg.Surface):
        self.assertIsInstance(texture, pg.Surface, "texture must be of type pygame.Surface")
        self.assertEqual(texture.get_colorkey()[0:3], assets.COLORKEY,
                         f"texture must have the correct colorkey {assets.COLORKEY}")




    # Test load_texture
    def test_load_texture(self):
        texture = assets.load_texture(self.texture_path)
        self.assertTextureFormat(texture)

    def test_load_texture_with_palette_swap(self):
        texture = assets.load_texture(self.texture_path, palette_swap_name=self.pallette_swap)
        self.assertTextureFormat(texture)

    def test_load_texture_caching(self):
        texture1 = assets.load_texture(self.texture_path)
        texture2 = assets.load_texture(self.texture_path)
        self.assertIs(texture1, texture2)

    


    # Test colorkey_surface
    def test_colorkey_surface(self):
        size = (200, 200)
        surface = assets.colorkey_surface(size)
        self.assertTextureFormat(surface)
        self.assertEqual(surface.size, size)
        # Check that surface is filled with the colorkey color
        pixel_color = surface.get_at((50, 50))[0:3]
        self.assertEqual(pixel_color, assets.COLORKEY, "colorkey surface must be filled with colorkey")



    # Test load_texture_map
    def test_load_texture_map(self):
        texture_map = assets.load_texture_map("spaceship")
        self.assertIsInstance(texture_map, dict)
        self.assertGreater(len(texture_map), 0)
        # Check that all entries are surfaces
        for texture in texture_map.values():
            self.assertTextureFormat(texture)

    def test_load_texture_map_caching(self):
        texture_map1 = assets.load_texture_map("spaceship")
        texture_map2 = assets.load_texture_map("spaceship")
        self.assertIs(texture_map1, texture_map2)




    # Test load_anim_data
    def test_load_anim_data(self):
        anim_data = assets.load_anim_data("spaceship")
        self.assertIsInstance(anim_data, dict)
        self.assertGreater(len(anim_data), 0)

    def test_load_anim_data_caching(self):
        anim_data1 = assets.load_anim_data("spaceship")
        anim_data2 = assets.load_anim_data("spaceship")
        self.assertIs(anim_data1, anim_data2)




    # Test load_anim_controller_data
    def test_load_anim_controller_data(self):
        controller_data = assets.load_anim_controller_data("spaceship")
        self.assertIsInstance(controller_data, dict)
        self.assertGreater(len(controller_data), 0)

    def test_load_anim_controller_data_caching(self):
        controller_data1 = assets.load_anim_controller_data("spaceship")
        controller_data2 = assets.load_anim_controller_data("spaceship")
        self.assertIs(controller_data1, controller_data2)




    # Test load_sound
    def test_load_sound(self):
        sound = assets.load_sound(self.test_sound)
        self.assertEqual(sound.name, self.test_sound)
        self.assertGreater(sound.get_variations(), 0)

    def test_load_sound_caching(self):
        sound1 = assets.load_sound(self.test_sound)
        sound2 = assets.load_sound(self.test_sound)
        self.assertIs(sound1, sound2)

    def test_load_sound_invalid_name(self):
        with self.assertRaises(ValueError):
            assets.load_sound("nonexistent_sound_xyz")




    # Test load_music_data
    def test_load_music_data(self):
        music = assets.load_music_data(self.test_music)
        self.assertEqual(music.get_name(), self.test_music)
        self.assertIsInstance(music.get_main_loop(), str)
        if music.get_prelude() is not None:
            self.assertIsInstance(music.get_prelude(), str)

    def test_load_music_data_caching(self):
        music1 = assets.load_music_data(self.test_music)
        music2 = assets.load_music_data(self.test_music)
        self.assertIs(music1, music2)




    # Test palette_swap function
    @patch('src.file_processing.assets.load_json')
    def test_palette_swap_with_dict(self, mock_load_json: MagicMock):
        # Create a simple test surface
        test_surface = pg.Surface((10, 10))
        test_surface.fill((255, 0, 0))  # Red
        
        swap_colors = {"#FF0000": "#00FF00"}  # Red to Green
        result = assets.palette_swap(test_surface, swap_colors)
        
        self.assertEqual(result.get_size(), test_surface.get_size())

    @patch('src.file_processing.assets.load_json')
    def test_palette_swap_with_file(self, mock_load_json: MagicMock):
        # Mock the load_json to return a swap dictionary
        mock_load_json.return_value = {"#FF0000": "#00FF00"}
        
        test_surface = pg.Surface((10, 10))
        test_surface.fill((255, 0, 0))
        
        result = assets.palette_swap(test_surface, self.pallette_swap)
        
        mock_load_json.assert_called_once_with("assets/palette_swaps/asteroid/green_rocks")











class DataTest(unittest.TestCase):
    test_level1 = {
        "asteroid_density": [10, 15],
        "asteroid_speed": [1, 6],

        "score_range": [0, 10000],
        "next_level": "level_2"
    }

    test_level2 = {
        "base_color": "#123456",
        "parl_a": "background_1",
        "parl_b": "background_2",
        "background_palette": "palette_1",
        "background_tint": "#4E6382",

        "asteroid_density": [20, 30],
        "asteroid_speed": [1, 6],
        "asteroid_frequency": 0.5,
        "spawn_asteroids": {"small_rock": 70, "medium_rock": 30},

        "enemy_frequency": 0.2,
        "enemy_count": 5,
        "spawn_enemies": {"basic_enemy": 100, "big_chungus": 80},

        "powerup_frequency": 0.67,
        "spawn_powerups": {"health": 100, "speed_boost": 50},

        "score_range": [10000, 20000],
        "next_level": "level_3"
    }

    @classmethod
    def setUpClass(cls):
        pg.init()
        pg.Window(hidden=True).get_surface()

    @classmethod
    def tearDownClass(cls):
        pg.quit()

    @patch("src.file_processing.data.load_json")
    def test_load_level_with_default_values(self, mock_load_json: MagicMock):
        mock_load_json.return_value = self.test_level1
        level = data.load_level("test_level")
        
        mock_load_json.assert_called_once_with("data/levels/test_level")
        self.assertIsInstance(level, LevelData)

        self.assertEqual(level.level_name, "test_level")
        self.assertEqual(level.base_color, "#000000")
        self.assertEqual(level.parl_a, None)
        self.assertEqual(level.parl_b, None)
        self.assertEqual(level.background_palette, None)
        self.assertEqual(level.background_tint, "#4E6382")

        self.assertEqual(level.asteroid_density, (10, 15))
        self.assertEqual(level.asteroid_speed, (1, 6))
        self.assertEqual(level.asteroid_frequency, 0.0)
        self.assertEqual(level.asteroid_spawn_weights, ([], []))

        self.assertEqual(level.enemy_frequency, 0.0)
        self.assertEqual(level.enemy_count, 0)
        self.assertEqual(level.enemy_spawn_weights, ([], []))

        self.assertEqual(level.powerup_frequency, 0.0)
        self.assertEqual(level.powerup_spawn_weights, ([], []))

        self.assertEqual(level.score_range, (0, 10000))
        self.assertEqual(level.next_level, "level_2")

    @patch("src.file_processing.data.load_json")
    def test_load_level(self, mock_load_json: MagicMock):
        mock_load_json.return_value = self.test_level2
        level = data.load_level("test_level")
        
        mock_load_json.assert_called_once_with("data/levels/test_level")
        self.assertIsInstance(level, LevelData)

        self.assertEqual(level.level_name, "test_level")
        self.assertEqual(level.base_color, "#123456")
        self.assertEqual(level.parl_a, "background_1")
        self.assertEqual(level.parl_b, "background_2")
        self.assertEqual(level.background_palette, "palette_1")
        self.assertEqual(level.background_tint, "#4E6382")

        self.assertEqual(level.asteroid_density, (20, 30))
        self.assertEqual(level.asteroid_speed, (1, 6))
        self.assertEqual(level.asteroid_frequency, 0.5)
        self.assertEqual(level.asteroid_spawn_weights, (["small_rock", "medium_rock"], [70, 30]))

        self.assertEqual(level.enemy_frequency, 0.2)
        self.assertEqual(level.enemy_count, 5)
        self.assertEqual(level.enemy_spawn_weights, (["basic_enemy", "big_chungus"], [100, 80]))

        self.assertEqual(level.powerup_frequency, 0.67)
        self.assertEqual(level.powerup_spawn_weights, (["health", "speed_boost"], [100, 50]))

        self.assertEqual(level.score_range, (10000, 20000))
        self.assertEqual(level.next_level, "level_3")

    @patch('src.file_processing.data.load_json')
    def test_load_level_invalid_name(self, mock_load_json: MagicMock):
        mock_load_json.side_effect = FileNotFoundError()
        with self.assertRaises(ValueError):
            data.load_level("level_not_found")

    @patch('src.file_processing.data.load_json')
    def test_load_level_missing_property(self, mock_load_json: MagicMock):
        # Missing required property "score_range"
        mock_load_json.return_value = {
            "asteroid_density": [10, 15],
            "asteroid_speed": [1, 6],
            "next_level": "level_2"
        }
        with self.assertRaises(LevelDataError) as context:
            data.load_level("test_level")
        
        self.assertEqual(context.exception.level_name, "test_level")
        self.assertEqual(context.exception.missing_property, "score_range")


    @unittest.skipIf(Cheats.demo_mode, "Demo mode was enabled when running test")
    @patch('src.file_processing.data.load_json')
    def test_load_high_score(self, mock_load_json: MagicMock):
        mock_load_json.return_value = {"highscore": 12345}
        high_score = data.load_highscore()
        mock_load_json.assert_called_once_with("user_data/highscore")
        self.assertEqual(high_score, 12345)

    @unittest.skipIf(Cheats.demo_mode, "Demo mode was enabled when running test")
    @patch('src.file_processing.data.load_json')
    def test_load_high_score_overflow(self, mock_load_json: MagicMock):
        mock_load_json.return_value = {"highscore": 10000000}
        high_score = data.load_highscore()
        mock_load_json.assert_called_once_with("user_data/highscore")
        self.assertEqual(high_score, data.SCORE_LIMIT)

    @unittest.skipIf(Cheats.demo_mode, "Demo mode was enabled when running test")
    @patch('src.file_processing.data.load_json')
    def test_load_high_score_underflow(self, mock_load_json: MagicMock):
        mock_load_json.return_value = {"highscore": -100}
        high_score = data.load_highscore()
        mock_load_json.assert_called_once_with("user_data/highscore")
        self.assertEqual(high_score, 0)

    @unittest.skipIf(Cheats.demo_mode, "Demo mode was enabled when running test")
    @patch('src.file_processing.data.load_json')
    def test_load_high_invalid_score(self, mock_load_json: MagicMock):
        mock_load_json.return_value = {"highscore": "not_a_number"}
        high_score = data.load_highscore()
        mock_load_json.assert_called_once_with("user_data/highscore")
        self.assertEqual(high_score, 0)
