from settings import *


class Model:
    def __init__(self, model, speed, position, direction = Vector3()):
        self.model = model
        self.speed = speed
        self.position = position
        self.direction = direction
        self.size = 1


    def move(self, dt):
        self.position.x += self.speed * self.direction.x * dt
        self.position.y += self.speed * self.direction.y * dt
        self.position.z += self.speed * self.direction.z * dt


    def update(self, dt):
        self.move(dt)

    
    def draw(self):
        draw_model(self.model, self.position, self.size, WHITE)