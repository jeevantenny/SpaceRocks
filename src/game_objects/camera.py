import pygame as pg
import random

import debug

from src.custom_types import Stopwatch, LerpTracker
from src.math_functions import unit_vector, format_angle, sign
from src.file_processing import assets

from . import GameObject, ObjectGroup
from .components import ObjectVelocity, ObjectTexture





ALL = object()


class Camera:
    "Moves to target position and captures an area of the world every frame."
    __max_speed = 1000
    __snap_distance = 100000
    __max_shake_offset=12
    def __init__(self, start_pos: pg.typing.Point, wander_radius=60):
        self._position = pg.Vector2(start_pos)
        self._velocity = pg.Vector2(0, 0)
        self._target_pos = self.position
        self._track_target = True
        self.__wander_radius = wander_radius
        self.__trail_distance = wander_radius

        self.__shake_stopwatch = Stopwatch().start()
        self.__shake_offset = pg.Vector2()
        self.__shake_intensities: list[float] = []
        self.__shake_end_times: list[int] = []
        self._lerp_tracker = LerpTracker()



    
    @property
    def position(self) -> pg.Vector2:
        return self._position.copy()

    def set_position(self, value: pg.typing.Point) -> None:
        self._position = pg.Vector2(value)

    def get_target(self) -> pg.Vector2:
        return self._target_pos.copy()

    def set_target(self, position: pg.typing.Point) -> None:
        self._target_pos.xy = position

    def track_target(self, track: bool) -> None:
        self._track_target = track

    def set_velocity(self, value: pg.typing.Point) -> None:
        self._velocity.xy = value

    def clear_velocity(self) -> None:
        self._velocity.xy = (0, 0)

    def camera_shake(self, intensity: float, duration=0) -> None:
        self.__shake_intensities.append(pg.math.clamp(intensity, 0, 1))
        self.__shake_end_times.append(self.__shake_stopwatch.time_elapsed + duration)

    def reset_motion(self) -> None:
        self.set_velocity((0, 0))
        self.__shake_intensities.clear()
        self.__shake_offset.xy = (0, 0)


    def update(self) -> None:
        "Updates position of camera for every game tick."
        self.__update_camera_shake()
        if not self._track_target:
            self.clear_velocity()
            return

        displacement = self._target_pos-self.position
        direction = unit_vector(displacement)
        distance = displacement.magnitude()

        if distance < self.__wander_radius:
            self.__trail_distance += 1
        else:
            self.__trail_distance -= 1
        
        self.__trail_distance = pg.math.clamp(self.__trail_distance, 0, self.__wander_radius)

        if distance < 1 or distance > self.__snap_distance:
            self.set_position(self._target_pos)
            self.clear_velocity()
            self.__trail_distance = 0

        elif distance > self.__trail_distance:
            self._velocity = direction*pg.math.clamp((distance-self.__trail_distance)*0.23, 0, self.__max_speed)
        else:
            self.clear_velocity()

        self._position += self._velocity
        self._lerp_tracker.on_update()
    

    def __update_camera_shake(self) -> None:
        if not self.__shake_intensities:
            return

        shake_intensity = min(max(self.__shake_intensities), 1)
        shake_offset = self.__max_shake_offset*shake_intensity**2
        self.__shake_offset.xy = (0, shake_offset)
        self.__shake_offset.rotate_ip(random.randint(1, 359))
        self.__shake_stopwatch.update()
        
        i = 0
        while i < len(self.__shake_intensities):
            intensity = self.__shake_intensities[i]
            if intensity <= 0:
                self.__shake_intensities.pop(i)
                self.__shake_end_times.pop(i)
                continue
            end_time = self.__shake_end_times[i]
            if end_time < self.__shake_stopwatch.time_elapsed:
                self.__shake_intensities[i] -= 0.1
            i += 1


    def blit_position(self, lerp_amount: float) -> pg.Vector2:
        """Position of camera after taking interpolation into account and camera shake."""
        return self.position + self._velocity*lerp_amount + self.__shake_offset

    def get_visible_area(self, area_size: pg.typing.Point) -> pg.Rect:
        rect = pg.Rect((0, 0), area_size)
        rect.center = self.position
        return rect

    def capture(self, output_surface: pg.Surface, entities: ObjectGroup, lerp_amount=0.0) -> None:
            "Draws game objects relative to the camera and blit them to the output surface."
            lerp_pos = self.blit_position(lerp_amount)
            blit_offset = pg.Vector2(output_surface.size)*0.5 - lerp_pos
    
            entities.draw(output_surface, lerp_amount, blit_offset)
            if debug.Cheats.show_bounding_boxes:
                pg.draw.rect(output_surface, "red", (*blit_offset, *output_surface.size), 1)
                blit_offset = pg.Vector2(output_surface.size)*0.5 - self._position
                self._draw_crosshair(output_surface, self._target_pos+blit_offset)


    def _draw_crosshair(self, surface: pg.Surface, position: pg.typing.Point) -> None:
        pg.draw.line(surface, "black", position-(0, 4), position+(0, 4), 3)
        pg.draw.line(surface, "black", position-(4, 0), position+(4, 0), 3)
        pg.draw.line(surface, "white", position-(0, 3), position+(0, 3))
        pg.draw.line(surface, "white", position-(3, 0), position+(3, 0))







class RotoZoomCamera(Camera):
    __rotation_speed = 8
    __rotation_acceleration = 1
    def __init__(self, start_pos, wander_radius=60):
        super().__init__(start_pos, wander_radius)
        self.__rotation = 0
        self.__target_rotation = 0
        self.__angular_vel = 0
        self.__zoom = 1.0


    def get_rotation(self) -> int:
        return self.__rotation
    
    def get_lerp_rotation(self, lerp_amount: float) -> float:
        lerp_amount = self._lerp_tracker.get_lerp(lerp_amount)
        return format_angle(self.__rotation-self.__angular_vel*(1-lerp_amount))
    
    def set_rotation(self, value: int) -> None:
        self.__rotation = format_angle(int(value))

    def set_target_rotation(self, rotation: int) -> None:
        self.__target_rotation = format_angle(int(rotation))

    def set_angular_vel(self, value: int) -> None:
        self.__angular_vel = pg.math.clamp(value, -self.__rotation_speed, self.__rotation_speed)
        
    def get_zoom(self) -> float:
        return self.__zoom
    
    def set_zoom(self, zoom: float) -> None:
        if zoom < 0.5:
            raise ValueError("Camera zoom cannot be less than 0.5")
        self.__zoom = round(zoom, 2)
    
    def rotate(self, amount: int) -> None:
        self.set_rotation(self.__rotation+amount)

    def reset_motion(self) -> None:
        super().reset_motion()
        self.set_angular_vel(0)
    
    def update(self):
        super().update()
        difference = int(self.__target_rotation-self.__rotation)
        amount = abs(difference)
        direction = sign(difference)
        if amount > 180:
            amount = 360 - amount
            direction *= -1

        target_vel = direction*pg.math.clamp(int(amount*0.1), 1, self.__angular_vel*direction+1)
        self.set_angular_vel(target_vel)
        self.rotate(self.__angular_vel)



    def capture(self, output_surface, entities, lerp_amount=0):
            scaled_surface = assets.colorkey_surface(pg.Vector2(output_surface.size)*self.__zoom)
            camera_lerp_pos = self.blit_position(lerp_amount)
            camera_lerp_rotation = self.get_lerp_rotation(lerp_amount)
            blit_offset = pg.Vector2(scaled_surface.size)*0.5 - camera_lerp_pos
    
            for entity in entities.get_draw_order():
                if isinstance(entity, ObjectVelocity):
                    entity_pos: pg.Vector2 = entity.get_lerp_pos(lerp_amount)
                else:
                    entity_pos = entity.position
    
                blit_pos = entity_pos - camera_lerp_pos
                blit_pos.rotate_ip(-camera_lerp_rotation)
                blit_pos += camera_lerp_pos - entity_pos + blit_offset
                entity.draw(
                    scaled_surface, lerp_amount, blit_pos,
                    -camera_lerp_rotation if not entity.ignore_camera_rotation else 0)
                
            output_surface.blit(pg.transform.scale(scaled_surface, output_surface.size))
    
            if debug.Cheats.show_bounding_boxes:
                crosshair_pos = (self.get_target()-self.position).rotate(-self.__rotation) + pg.Vector2(output_surface.size)*0.5
                self._draw_crosshair(output_surface, crosshair_pos)
    


class ObjectTracker(ObjectTexture):
    can_despawn=False
    ignore_camera_rotation=True
    progress_save_key="object_tracker"

    __arrow_distance=200
    __circle_distance=100

    def __init__(self, track_object: GameObject):
        super().__init__(position=(0, 0), texture=None)
        self.__track_object = track_object

    def __init_from_data__(self, object_data):
        self.__init__(None)
        self.__track_id = object_data["track_id"]
    
    def post_init_from_data(self, object_dict):
        self.__track_object = object_dict.get(self.__track_id)
    
    def get_data(self):
        data = super().get_data()
        data.update(track_id=id(self.__track_object))
        return data
    
    def update(self):
        super().update()
        if self.__track_object is None or not self.__track_object.alive():
            self.kill()

    
    def draw(self, surface, lerp_amount=0, offset=(0, 0), rotation=0):
        if self.__track_object is None:
            return

        canvas_center = pg.Vector2(surface.size)*0.5
        camera_pos = canvas_center-offset
        if self.__track_object.within_distance(camera_pos, self.__circle_distance):
            return

        if isinstance(self.__track_object, ObjectVelocity):
            track_position = self.__track_object.get_lerp_pos(lerp_amount)
        else:
            track_position = self.__track_object.position
        pg.draw.circle(surface, "yellow", track_position+offset, 30, 1)

        if self.__track_object.within_distance(camera_pos, self.__arrow_distance):
            return

        line_end = canvas_center + (track_position-camera_pos).clamp_magnitude(40)
        pg.draw.line(surface, "yellow", canvas_center, track_position+offset)