from settings import *
from models import Model


class Player(Model):
    """Player class with its own UI"""
    def __init__(self, model, shoot_func):
        super().__init__(model = model, speed = 25, position = Vector3(0, 15, 0))
        self.shoot_func = shoot_func
        self.model.transform = matrix_identity()
        
        self.max_speed = 25.0
        self.velocity = Vector3(0, 0, 0)
        self.acceleration = 10.0
        self.drag = 0.8           # air resistance
        self.target_direction = Vector3(0, 0, 0)

        self.roll_angle = 0.0
        self.ROLL_SPEED = 4.0      # how quickly the plane rolls/unrolls
        self.MAX_ROLL_ANGLE = radians(45)
        self.TURN_TO_ROLL_RATIO = 30.0


    def input(self, forward_vector):
        move_amount = int(is_key_down(KEY_W)) - int(is_key_down(KEY_S))
        self.target_direction = vector3_scale(forward_vector, move_amount)

        if is_key_pressed(KEY_ENTER):
            self.shoot_func(self.position)


    def move(self, dt):
        desired_velocity = vector3_scale(self.target_direction, self.max_speed)
        steering_force = vector3_subtract(desired_velocity, self.velocity)
        steering_force = vector3_scale(steering_force, self.acceleration * dt)
        self.velocity = vector3_add(self.velocity, steering_force)
        drag_force = vector3_scale(self.velocity, self.drag * dt)
        self.velocity = vector3_subtract(self.velocity, drag_force)
        self.position = vector3_add(self.position, vector3_scale(self.velocity, dt))


    def apply_upward_boost(self, boost_force: float):
        """Applies an instantaneous upward force to the player's velocity."""
        self.velocity.y += boost_force


    def update(self, dt, forward_vector, mouse_dx):
        self.input(forward_vector)
        self.move(dt)

        target_roll = 0.0
        is_moving = vector3_length_sqr(self.velocity) > 1.0 
        is_turning = abs(mouse_dx) > 0.01

        if is_moving and is_turning:
            target_roll = mouse_dx * self.TURN_TO_ROLL_RATIO
            target_roll = min(max(target_roll, -self.MAX_ROLL_ANGLE), self.MAX_ROLL_ANGLE)
        
        self.roll_angle += (target_roll - self.roll_angle) * self.ROLL_SPEED * dt

        forward = vector3_normalize(self.velocity) if vector3_length_sqr(self.velocity) > 0.01 else forward_vector
        world_up = Vector3(0, 1, 0)

        if abs(vector3_dot_product(forward, world_up)) > 0.9999:
            self.model.transform.m12 = self.position.x
            self.model.transform.m13 = self.position.y
            self.model.transform.m14 = self.position.z
        else:
            right = vector3_normalize(vector3_cross_product(forward, world_up))
            up = vector3_normalize(vector3_cross_product(right, forward))

            rolled_up = vector3_rotate_by_axis_angle(up, forward, self.roll_angle)
            rolled_right = vector3_rotate_by_axis_angle(right, forward, self.roll_angle)

            # this matrix contains rotation and position in the world
            self.model.transform = Matrix(
                rolled_right.x,    rolled_up.x,   -forward.x,   self.position.x,
                rolled_right.y,    rolled_up.y,   -forward.y,   self.position.y,
                rolled_right.z,    rolled_up.z,   -forward.z,   self.position.z,
                0.0,               0.0,           0.0,          1.0
            )


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

        # if looking down, draw a triangle pointing down
        if camera_pitch > pitch_threshold:
            p1 = Vector2(center_x, center_y + indicator_offset)
            p2 = Vector2(center_x - indicator_size, center_y + indicator_offset - indicator_size)
            p3 = Vector2(center_x + indicator_size, center_y + indicator_offset - indicator_size)
            draw_triangle_lines(p1, p2, p3, WHITE)
        
        # the movement indicators. only if the player is actually moving
        if vector3_length_sqr(self.velocity) > 0.1:
            move_dir_2d = vector2_normalize(Vector2(self.velocity.x, self.velocity.z))
            
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