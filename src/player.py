from settings import *
from models import Model

class Player(Model):
    """Player class with its own UI"""
    def __init__(self, model, shoot_func):
        super().__init__(model = model, speed = 20, position = Vector3(0, 10, 0))
        self.shoot_func = shoot_func
        self.model.transform = matrix_identity()

    
    def input(self, forward_vector):
        move_amount = int(is_key_down(KEY_W)) - int(is_key_down(KEY_S))
        self.direction = vector3_scale(forward_vector, move_amount)

        if is_key_pressed(KEY_ENTER):
            self.shoot_func(self.position)


    def update(self, dt, forward_vector):
        self.input(forward_vector)
        super().update(dt)

        if vector3_length_sqr(self.direction) > 0.001:
            forward = vector3_normalize(self.direction)
            world_up = Vector3(0, 1, 0)

            if abs(vector3_dot_product(forward, world_up)) > 0.9999:
                self.model.transform.m12 = self.position.x
                self.model.transform.m13 = self.position.y
                self.model.transform.m14 = self.position.z
            else:
                right = vector3_normalize(vector3_cross_product(forward, world_up))
                up = vector3_normalize(vector3_cross_product(right, forward))

                # this matrix contains rotation and position in the world
                self.model.transform = Matrix(
                    right.x,    up.x,   -forward.x,   self.position.x,
                    right.y,    up.y,   -forward.y,   self.position.y,
                    right.z,    up.z,   -forward.z,   self.position.z,
                    0.0,        0.0,    0.0,          1.0
                )
        else:
            self.model.transform.m12 = self.position.x
            self.model.transform.m13 = self.position.y
            self.model.transform.m14 = self.position.z

        
    def draw(self):
        draw_model(self.model, Vector3(0, 0, 0), 1.0, WHITE)


    def draw_hud(self, camera_pitch):
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2
        radius = 12
        
        draw_circle_lines(center_x, center_y, radius, WHITE)
        draw_circle(center_x, center_y, 2, WHITE)

        pitch_threshold = 0.15 
        move_threshold = 0.35
        indicator_offset = 25
        indicator_size = 6

        # quite complex for a fkg indicator 
        # for the pitch indicators. If looking up
        if camera_pitch < -pitch_threshold:
            p1 = Vector2(center_x, center_y - indicator_offset)
            p2 = Vector2(center_x - indicator_size, center_y - indicator_offset + indicator_size)
            p3 = Vector2(center_x + indicator_size, center_y - indicator_offset + indicator_size)
            draw_triangle_lines(p1, p2, p3, WHITE)

        # if looking down
        if camera_pitch > pitch_threshold:
            p1 = Vector2(center_x, center_y + indicator_offset)
            p2 = Vector2(center_x - indicator_size, center_y + indicator_offset - indicator_size)
            p3 = Vector2(center_x + indicator_size, center_y + indicator_offset - indicator_size)
            draw_triangle_lines(p1, p2, p3, WHITE)
        
        # the movement indicators. only if the player is actually moving
        if vector3_length_sqr(self.direction) > 0.01:
            move_dir_2d = vector2_normalize(Vector2(self.direction.x, self.direction.z))
            
            # (North)
            if move_dir_2d.y < -move_threshold:
                p1 = Vector2(center_x, center_y - indicator_offset)
                p2 = Vector2(center_x - indicator_size, center_y - indicator_offset + indicator_size)
                p3 = Vector2(center_x + indicator_size, center_y - indicator_offset + indicator_size)
                draw_triangle_lines(p1, p2, p3, WHITE)

            # (West)
            if move_dir_2d.x < -move_threshold:
                p1 = Vector2(center_x - indicator_offset, center_y)
                p2 = Vector2(center_x - indicator_offset + indicator_size, center_y - indicator_size)
                p3 = Vector2(center_x - indicator_offset + indicator_size, center_y + indicator_size)
                draw_triangle_lines(p1, p3, p2, WHITE)
            
            # (East)
            if move_dir_2d.x > move_threshold:
                p1 = Vector2(center_x + indicator_offset, center_y)
                p2 = Vector2(center_x + indicator_offset - indicator_size, center_y - indicator_size)
                p3 = Vector2(center_x + indicator_offset - indicator_size, center_y + indicator_size)
                draw_triangle_lines(p1, p2, p3, WHITE)