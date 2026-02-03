import pygame as pg
import random

from src.custom_types import Timer
from src.file_processing import assets

from .components import ObjectTexture, ObjectHitbox, ObjectCollision
from .spaceship import PlayerShip
from .projectiles import EnemyBullet






class BossShip(ObjectTexture, ObjectHitbox, ObjectCollision):
    ignore_camera_rotation=True
    _max_speed = 500
    def __init__(self, position: pg.typing.Point):
        texture = assets.colorkey_surface((256, 256))
        pg.draw.circle(texture, "#338888", (128, 128), 128)
        super().__init__(
            position=position,
            texture=texture,
            radius=128,
            hitbox_size=(230, 230)
        )
    
        self.__timer = Timer(1)
        self.__shoot_start_timer = Timer(30, True, self.shoot)#.start()

    
    def update(self):
        super().update()
        self.__timer.update()
        self.__shoot_start_timer.update()


    def shoot(self):
        direction = pg.Vector2(0, -1).rotate(random.randint(0, 19))

        for _ in range(15):
            self.primary_group.add(EnemyBullet(self.position, direction, self._velocity))
            direction.rotate_ip(24)


    


    def on_collide(self, collided_with):
        if isinstance(collided_with, PlayerShip) and collided_with.health:
            displacement = collided_with.position-self.position
            collided_with.accelerate(displacement*0.1)
            collided_with.kill()
            self.__timer = Timer(4, exec_after=lambda: collided_with.accelerate(displacement*-0.06)).start()