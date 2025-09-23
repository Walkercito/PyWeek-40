from settings import *
from models import Model


class Player(Model):
    def __init__(self, model, shoot_func):
        super().__init__(model = model, speed = 20, position = Vector3())
        self.shoot_func = shoot_func

    
    def input(self):
        self.direction.x = int(is_key_down(KEY_D)) - int(is_key_down(KEY_A))
        self.direction.z = int(is_key_down(KEY_W)) - int(is_key_down(KEY_S))
        self.direction.y = int(is_key_down(KEY_SPACE)) - int(is_key_down(KEY_LEFT_SHIFT))
        if is_key_pressed(KEY_ENTER):
            self.shoot_func(self.position)


    def update(self, dt):
        self.input()
        super().update(dt) 