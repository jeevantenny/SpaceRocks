import pygame as pg
import unittest
from unittest.mock import patch, MagicMock

from src.file_processing import assets, data



class AssetsTest(unittest.TestCase):
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
        self.assertIsInstance(texture, pg.Surface)
        self.assertEqual(texture.get_colorkey()[0:3], assets.COLORKEY)




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
        self.assertEqual(surface.size, size)
        self.assertEqual(surface.get_colorkey()[0:3], assets.COLORKEY)
        # Check that surface is filled with the colorkey color
        pixel_color = surface.get_at((50, 50))[0:3]
        self.assertEqual(pixel_color, assets.COLORKEY)



    # Test load_texture_map
    def test_load_texture_map(self):
        texture_map = assets.load_texture_map("spaceship")
        self.assertIsInstance(texture_map, dict)
        self.assertGreater(len(texture_map), 0)
        # Check that all entries are surfaces
        for name, surface in texture_map.items():
            self.assertIsInstance(surface, pg.Surface)

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
