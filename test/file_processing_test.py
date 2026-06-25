import pygame as pg
import pickle
from json import JSONDecodeError

import unittest
from unittest.mock import patch, MagicMock, mock_open, ANY

from src.file_processing import assets, data
from src.custom_types import LevelData, SaveData

from src import game_errors

import debug
from debug import Cheats




class BaseTest(unittest.TestCase):


    def test_load_json(self):
        with patch("builtins.open", mock_open(read_data='{"arg1": 80, "arg2": 90}')) as mock_file:
            output = data.load_json("json_file_name")

        mock_file: MagicMock
        mock_file.assert_called_once_with("json_file_name.json", "r")
        self.assertEqual(output, {"arg1": 80, "arg2": 90})
        
    
    def test_save_json(self):
        with patch("builtins.open", mock_open(read_data="")) as mock_file:
            data.save_json({"arg1": 80, "arg2": 90}, "json_file_name")
            
        mock_file: MagicMock
        mock_file.assert_called_once_with("json_file_name.json", "w")








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










@unittest.skipIf(Cheats.demo_mode, "Demo mode was enabled when running test")
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

    mock_settings = {
        "music_volume": 0.2,
        "soundfx_volume": 0.2,
        "controller_rumble": False,
        "show_version_number": False,
        "motion_blur": False,
        "scale_blur": False
    }

    @classmethod
    def setUpClass(cls):
        pg.init()
        pg.Window(hidden=True).get_surface()

    @classmethod
    def tearDownClass(cls):
        pg.quit()

    
    def setUp(self):
        # Reset all settings to default
        data.load_settings("")


    def get_test_save_data(self) -> SaveData:
        return SaveData("test", 100, 2.0, 3, (0, 0), {})


    def get_test_save_bytes(self) -> bytes:
        return pickle.dumps(self.get_test_save_data())

        

    def get_invalid_save_data(self) -> bytes:
        invalid_object = dict()
        return pickle.dumps(invalid_object)

        

    def assertCurrentSettings(self, expected: dict):
        self.assertEqual(data.get_setting("soundfx_volume"), expected["soundfx_volume"])
        self.assertEqual(data.get_setting("music_volume"), expected["music_volume"])
        self.assertEqual(data.get_setting("controller_rumble"), expected["controller_rumble"])
        self.assertEqual(data.get_setting("motion_blur"), expected["motion_blur"])
        self.assertEqual(data.get_setting("scale_blur"), expected["scale_blur"])
        self.assertEqual(data.get_setting("show_version_number"), expected["show_version_number"])





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
        with self.assertRaises(FileNotFoundError):
            data.load_level("level_not_found")

    @patch('src.file_processing.data.load_json')
    def test_load_level_missing_property(self, mock_load_json: MagicMock):
        # Missing required property "score_range"
        mock_load_json.return_value = {
            "asteroid_density": [10, 15],
            "asteroid_speed": [1, 6],
            "next_level": "level_2"
        }
        with self.assertRaises(game_errors.LevelDataError) as context:
            data.load_level("test_level")
        
        self.assertEqual(context.exception.level_name, "test_level")
        self.assertEqual(context.exception.missing_property, "score_range")


    @patch('src.file_processing.data.load_json')
    def test_load_high_score(self, mock_load_json: MagicMock):
        mock_load_json.return_value = {"highscore": 12345}
        high_score = data.load_highscore()
        mock_load_json.assert_called_once_with("user_data/highscore")
        self.assertEqual(high_score, 12345)

    @patch('src.file_processing.data.load_json')
    def test_load_high_score_overflow(self, mock_load_json: MagicMock):
        mock_load_json.return_value = {"highscore": 10000000}
        high_score = data.load_highscore()
        mock_load_json.assert_called_once_with("user_data/highscore")
        self.assertEqual(high_score, data.SCORE_LIMIT)

    @patch('src.file_processing.data.load_json')
    def test_load_high_score_underflow(self, mock_load_json: MagicMock):
        mock_load_json.return_value = {"highscore": -100}
        high_score = data.load_highscore()
        mock_load_json.assert_called_once_with("user_data/highscore")
        self.assertEqual(high_score, 0)

    @patch('src.file_processing.data.load_json')
    def test_load_high_invalid_score(self, mock_load_json: MagicMock):
        mock_load_json.return_value = {"highscore": "not_a_number"}
        high_score = data.load_highscore()
        mock_load_json.assert_called_once_with("user_data/highscore")
        self.assertEqual(high_score, 0)





    @patch('src.file_processing.data.save_json')
    def test_save_highscore(self, mock_save_json: MagicMock):
        mock_save_json.return_value = None
        data.save_highscore(12345)
        mock_save_json.assert_called_once_with({"highscore": 12345}, "user_data/highscore")

    @patch('src.file_processing.data.save_json')
    def test_save_highscore_score_overflow(self, mock_save_json: MagicMock):
        mock_save_json.return_value = None
        data.save_highscore(10000000)
        mock_save_json.assert_called_once_with({"highscore": data.SCORE_LIMIT}, "user_data/highscore")

    @patch('src.file_processing.data.save_json')
    def test_save_highscore_score_underflow(self, mock_save_json: MagicMock):
        mock_save_json.return_value = None
        data.save_highscore(-100)
        mock_save_json.assert_called_once_with({"highscore": 0}, "user_data/highscore")





    def test_load_progress(self):
        opener = mock_open(read_data=self.get_test_save_bytes())
        with patch("builtins.open", opener) as mock_file:
            save_data = data.load_progress()

        mock_file: MagicMock
        mock_file.assert_called_once_with(data.SAVE_DATA_PATH, "rb")
        self.assertIsInstance(save_data, SaveData)
    

    def test_load_progress_no_file(self):
        save_data = data.load_progress("no_file")
        self.assertIsNone(save_data)
    
    def test_load_progress_empty_file(self):
        with patch("builtins.open", mock_open(read_data=b"")) as mock_file:
            save_data = data.load_progress("empty_file")
        
        mock_file: MagicMock
        mock_file.assert_called_once_with("empty_file", "rb")
        self.assertIsNone(save_data)
    

    def test_load_progress_corrupted_file(self):
        with patch("builtins.open", mock_open(read_data=b"corrupted")) as mock_file:
            with self.assertRaises(game_errors.SaveFileError):
                data.load_progress("corrupted_file")
        
        mock_file: MagicMock
        mock_file.assert_called_once_with("corrupted_file", "rb")


    def test_load_progress_invalid_type(self):
        opener = mock_open(read_data=self.get_invalid_save_data())
        with patch("builtins.open", opener) as mock_file:
            with self.assertRaises(game_errors.SaveFileError):
                data.load_progress("invalid_type_file")
        
        mock_file: MagicMock
        mock_file.assert_called_once_with("invalid_type_file", "rb")




    def test_save_progress(self):
        save_data = self.get_test_save_data()
        with patch("builtins.open", mock_open()) as mock_file:
            data.save_progress(save_data)
        
        mock_file: MagicMock
        mock_file.assert_called_once_with(data.SAVE_DATA_PATH, "wb")


    def test_save_data_invalid_object(self):
        invalid_data = dict()
        with patch("builtins.open", mock_open()) as mock_file:
            with self.assertRaises(game_errors.SaveFileError):
                data.save_progress(invalid_data)
        
        mock_file: MagicMock
        mock_file.assert_not_called()

    




    def test_delete_progress(self):
        opener = mock_open(read_data=self.get_test_save_bytes())
        with patch("builtins.open", opener) as mock_file:
            data.delete_progress()
        
        mock_file: MagicMock
        mock_file.assert_called_once_with(data.SAVE_DATA_PATH, "wb")






    def test_get_settings_float(self):
        self.assertEqual(data.get_setting("soundfx_volume"), 0.7)
        
    def test_get_settings_bool(self):
        self.assertEqual(data.get_setting("controller_rumble"), True)

    def test_get_settings_invalid_name(self):
        with self.assertRaises(KeyError):
            data.get_setting("non_existent")



    def test_update_settings(self):
        data.update_settings(soundfx_volume=0.9)
        self.assertEqual(data.get_setting("soundfx_volume"), 0.9)

    def test_update_settings_multiple(self):
        data.update_settings(soundfx_volume=0.9, controller_rumble=False, music_volume=0.4)
        self.assertEqual(data.get_setting("soundfx_volume"), 0.9)
        self.assertEqual(data.get_setting("controller_rumble"), False)
        self.assertEqual(data.get_setting("music_volume"), 0.4)
    
    def test_update_settings_invalid_settings_name(self):
        with self.assertRaises(KeyError):
            data.update_settings(non_existent=0.8)

    


    @patch('src.file_processing.data.load_json')
    def test_load_settings(self, mock_load_json: MagicMock):
        mock_load_json.return_value = self.mock_settings
        data.load_settings()

        mock_load_json.assert_called_once_with(data.SETTINGS_DATA_PATH)
        self.assertCurrentSettings(self.mock_settings)



    @patch('src.file_processing.data.load_json')
    def test_load_settings_default(self, mock_load_json: MagicMock):
        mock_load_json.return_value = {}
        data.load_settings()

        mock_load_json.assert_called_once_with(data.SETTINGS_DATA_PATH)
        self.assertCurrentSettings(data.DEFAULT_SETTINGS)



    @patch('src.file_processing.data.load_json')
    def test_load_settings_partially_default(self, mock_load_json: MagicMock):
        mock_load_json.return_value = {
            "soundfx_volume": 0.2,
            "controller_rumble": False,
        }
        data.load_settings()
        expected_settings = data.DEFAULT_SETTINGS.copy()
        expected_settings.update({
            "soundfx_volume": 0.2,
            "controller_rumble": False,
        })

        mock_load_json.assert_called_once_with(data.SETTINGS_DATA_PATH)
        self.assertCurrentSettings(expected_settings)



    @patch('src.file_processing.data.load_json')
    def test_load_settings_file_not_found(self, mock_load_json: MagicMock):
        mock_load_json.side_effect = FileNotFoundError()
        data.load_settings()

        mock_load_json.assert_called_once_with(data.SETTINGS_DATA_PATH)
        self.assertCurrentSettings(data.DEFAULT_SETTINGS)



    @patch('src.file_processing.data.load_json')
    def test_load_settings_invalid_json(self, mock_load_json: MagicMock):
        mock_load_json.side_effect = JSONDecodeError("error message", "doc", 0)
        data.load_settings()

        mock_load_json.assert_called_once_with(data.SETTINGS_DATA_PATH)
        self.assertCurrentSettings(data.DEFAULT_SETTINGS)




    @patch("src.file_processing.data.save_json")
    def test_reset_settings(self, mock_save_json: MagicMock):
        # Change some settings
        changes = {
            "soundfx_volume": 0.9,
            "controller_rumble": False,
            "music_volume": 0.4
        }
        data.update_settings(**changes)
        mock_save_json.return_value = None
        data.save_settings()
        mock_save_json.assert_called_once_with(ANY, "user_data/settings")

        # Call Reset Function
        data.reset_settings()

        self.assertCurrentSettings(data.DEFAULT_SETTINGS)





    @patch("src.file_processing.data.load_json")
    @patch("src.file_processing.data.save_json")
    def test_save_settings(self, mock_save_json: MagicMock, mock_load_json: MagicMock):
        # Change some settings
        changes = {
            "soundfx_volume": 0.9,
            "controller_rumble": False,
            "music_volume": 0.4
        }
        data.update_settings(**changes)
        mock_save_json.return_value = None
        data.save_settings()
        mock_save_json.assert_called_once_with(ANY, "user_data/settings")

        # Clear current changes
        data.reset_settings()

        # Reload saved changes from file (mock load_json to return first argument from save_json call)
        mock_load_json.return_value = mock_save_json.call_args.args[0]
        data.load_settings("")

        # Check that the reloaded settings match the changes initially made
        expected_settings = data.DEFAULT_SETTINGS.copy()
        expected_settings.update(changes)

        self.assertCurrentSettings(expected_settings)

    




    @patch("src.file_processing.data.delete_progress")
    @patch("src.file_processing.data.save_highscore")
    @patch("src.file_processing.data.reset_settings")
    def test_delete_user_data(self,
                              mock_delete_progress: MagicMock,
                              mock_save_highscore: MagicMock,
                              mock_reset_settings: MagicMock
                              ):
        data.delete_user_data()
        mock_delete_progress.assert_called_once()
        mock_save_highscore.assert_called_once_with(0)
        mock_reset_settings.assert_called_once()
        