from settings import *
from models import Model
from custom_timer import Timer


class Player(Model):
    """Player class with its own UI"""
    def __init__(self, model, shoot_func):
        super().__init__(model = model, speed = 25, position = Vector3(0, 15, 0))
        self.shoot_func = shoot_func
        self.model.transform = matrix_identity()
        
        self.collision_box = BoundingBox(
            Vector3(-1.0, -0.5, -3.4),    # min (X/2, Z/2, Y/2) 
            Vector3(1.0, 0.5, 3.4)        # max (X/2, Z/2, Y/2)
        )
        
        self.max_speed = 25.0
        self.velocity = Vector3(0, 0, 0)
        self.acceleration = 10.0
        self.drag = 0.8           # air resistance
        self.target_direction = Vector3(0, 0, 0)

        self.roll_angle = 0.0
        self.ROLL_SPEED = 4.0      # how quickly the plane rolls/unrolls
        self.MAX_ROLL_ANGLE = radians(45)
        self.TURN_TO_ROLL_RATIO = 30.0

        self.is_invulnerable = False
        self.invulnerability_timer = Timer(2.0) 
        self.flash_timer = Timer(0.1, repeat=True)
        self.is_visible = True
        self.spawn_position = Vector3(0, 15, 0)
        self.FOG_COLLISION_Y = 5.0 

        self.is_boosting = False
        self.max_boost_time = 6.0
        self.current_boost_time = self.max_boost_time
        self.boost_speed_multiplier = 1.8
        self.boost_recharge_rate = 1.0 
        self.boost_depletion_rate = 1.0 
        
        self.boost_drained_timer = Timer(2.0)
        self.show_boost_drained_message = False


    def start_invulnerability(self, reason="collision"):
        if self.is_invulnerable:
            return 
            
        if DEBUG:
            print(f"Invulnerability activated! Reason: {reason}")
        
        self.is_invulnerable = True
        self.is_visible = True
        self.invulnerability_timer.activate()
        self.flash_timer.activate()
        
        self.position = Vector3(self.spawn_position.x, self.spawn_position.y, self.spawn_position.z)
        self.velocity = Vector3(0, 0, 0)


    def end_invulnerability(self):
        self.is_invulnerable = False
        self.is_visible = True
        self.invulnerability_timer.deactivate()
        self.flash_timer.deactivate()
        if DEBUG:
            print("Invulnerability ended - Player vulnerable again!")


    def update_invulnerability(self):
        if not self.is_invulnerable:
            return

        self.invulnerability_timer.update()
        self.flash_timer.update()
        
        if not self.flash_timer:
            self.is_visible = not self.is_visible
            self.flash_timer.activate()
        
        if not self.invulnerability_timer:
            self.end_invulnerability()


    def check_fog_collision(self):
        if self.is_invulnerable:
            return False
            
        if self.position.y <= self.FOG_COLLISION_Y:
            self.start_invulnerability("fog collision")
            return True
        return False


    def get_rotated_bbox_corners(self):
        # corners of the 8 bboxs
        local_corners = [
            Vector3(self.collision_box.min.x, self.collision_box.min.y, self.collision_box.min.z),
            Vector3(self.collision_box.max.x, self.collision_box.min.y, self.collision_box.min.z),
            Vector3(self.collision_box.min.x, self.collision_box.max.y, self.collision_box.min.z),
            Vector3(self.collision_box.max.x, self.collision_box.max.y, self.collision_box.min.z),
            Vector3(self.collision_box.min.x, self.collision_box.min.y, self.collision_box.max.z),
            Vector3(self.collision_box.max.x, self.collision_box.min.y, self.collision_box.max.z),
            Vector3(self.collision_box.min.x, self.collision_box.max.y, self.collision_box.max.z),
            Vector3(self.collision_box.max.x, self.collision_box.max.y, self.collision_box.max.z)
        ]
        
        world_corners = []
        for corner in local_corners:
            transformed_corner = vector3_transform(corner, self.model.transform)
            world_corners.append(transformed_corner)
        
        return world_corners

    def get_world_bounding_box(self):
        if not self.has_collision or self.is_invulnerable:
            return None
        
        corners = self.get_rotated_bbox_corners()
        
        if not corners:
            return None
        
        min_x = min(corner.x for corner in corners)
        max_x = max(corner.x for corner in corners)
        min_y = min(corner.y for corner in corners)
        max_y = max(corner.y for corner in corners)
        min_z = min(corner.z for corner in corners)
        max_z = max(corner.z for corner in corners)
        
        return BoundingBox(
            Vector3(min_x, min_y, min_z),
            Vector3(max_x, max_y, max_z)
        )


    def check_collision_with(self, other_model):
        """Collision check - does not collide if invulnerable"""
        if not self.has_collision or not other_model.has_collision or self.is_invulnerable:
            return False
        
        my_box = self.get_world_bounding_box()
        if my_box is None:
            return False
        
        if hasattr(other_model, 'has_multiple_collision_boxes') and other_model.has_multiple_collision_boxes:
            other_boxes = other_model.get_world_bounding_boxes()
            for other_box in other_boxes:
                if check_collision_boxes(my_box, other_box):
                    return True
        else:
            other_box = other_model.get_world_bounding_box()
            if other_box is None:
                return False
            
            return check_collision_boxes(my_box, other_box)
        
        return False


    def draw_debug_oriented_box(self):
        if not DEBUG or not hasattr(self, '_show_oriented_debug') or not self._show_oriented_debug:
            return
            
        corners = self.get_rotated_bbox_corners()
        if len(corners) < 8:
            return

        box_color = PURPLE if self.is_invulnerable else LIME
        
        # front (z min)
        draw_line_3d(corners[0], corners[1], box_color)
        draw_line_3d(corners[1], corners[3], box_color)
        draw_line_3d(corners[3], corners[2], box_color)
        draw_line_3d(corners[2], corners[0], box_color)
        
        # back (z max)
        draw_line_3d(corners[4], corners[5], box_color)
        draw_line_3d(corners[5], corners[7], box_color)
        draw_line_3d(corners[7], corners[6], box_color)
        draw_line_3d(corners[6], corners[4], box_color)
        
        # connect front with back
        draw_line_3d(corners[0], corners[4], box_color)
        draw_line_3d(corners[1], corners[5], box_color)
        draw_line_3d(corners[2], corners[6], box_color)
        draw_line_3d(corners[3], corners[7], box_color)


    def input(self, forward_vector):
        move_amount = int(is_key_down(KEY_W)) - int(is_key_down(KEY_S))
        self.target_direction = vector3_scale(forward_vector, move_amount)

        if is_key_pressed(KEY_ENTER):
            self.shoot_func(self.position)

        if is_key_down(KEY_LEFT_SHIFT):                       # just stop the player from abusing the boost
            if not self.is_boosting:
                boost_ratio = self.current_boost_time / self.max_boost_time
                if boost_ratio > 0.2:
                    self.is_boosting = True
        else:
            self.is_boosting = False


    def move(self, dt):
        current_max_speed = self.max_speed * self.boost_speed_multiplier if self.is_boosting else self.max_speed
        
        desired_velocity = vector3_scale(self.target_direction, current_max_speed)
        steering_force = vector3_subtract(desired_velocity, self.velocity)
        steering_force = vector3_scale(steering_force, self.acceleration * dt)
        self.velocity = vector3_add(self.velocity, steering_force)
        drag_force = vector3_scale(self.velocity, self.drag * dt)
        self.velocity = vector3_subtract(self.velocity, drag_force)
        self.position = vector3_add(self.position, vector3_scale(self.velocity, dt))


    def update_boost(self, dt):
        if self.is_boosting:
            self.current_boost_time -= self.boost_depletion_rate * dt
            if self.current_boost_time <= 0:
                self.current_boost_time = 0
                self.is_boosting = False
                if not self.show_boost_drained_message:
                    self.start_boost_drained_message()
        else:
            if self.current_boost_time < self.max_boost_time:
                self.current_boost_time += self.boost_recharge_rate * dt
                if self.current_boost_time > self.max_boost_time:
                    self.current_boost_time = self.max_boost_time


    def apply_upward_boost(self, boost_force: float):
        self.velocity.y += boost_force


    def start_boost_drained_message(self):
        self.show_boost_drained_message = True
        self.boost_drained_timer.activate()


    def end_boost_drained_message(self):
        self.show_boost_drained_message = False
        self.boost_drained_timer.deactivate()


    def update_boost_drained_message(self):
        if not self.show_boost_drained_message:
            return
            
        self.boost_drained_timer.update()
        
        if not self.boost_drained_timer:
            self.end_boost_drained_message()


    def update(self, dt, forward_vector, mouse_dx):
        self.update_invulnerability()
        self.update_boost_drained_message()
        self.check_fog_collision()
        
        self.input(forward_vector)
        self.update_boost(dt)
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
        if self.is_visible:
            draw_model(self.model, Vector3(0, 0, 0), 1.0, WHITE)
        
        self.draw_debug_oriented_box()


    def draw_hud(self, camera_pitch, camera_yaw, is_warning_active=False):
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2

        HUD_GREEN = Color(50, 255, 150, 255)
        HUD_BLUE = Color(100, 200, 255, 255)
        HUD_RED = Color(255, 50, 50, 255)
        
        base_hud_color = HUD_RED if is_warning_active else HUD_GREEN
        final_hud_color = PURPLE if self.is_invulnerable else base_hud_color
        speedo_color = PURPLE if self.is_invulnerable else HUD_GREEN

        pitch_scale = 150
        vertical_offset = camera_pitch * pitch_scale
        roll_rad = -self.roll_angle
        
        draw_circle(center_x, center_y, 3, final_hud_color)
        draw_line_ex(Vector2(center_x - 10, center_y), Vector2(center_x - 25, center_y), 2, final_hud_color)
        draw_line_ex(Vector2(center_x + 10, center_y), Vector2(center_x + 25, center_y), 2, final_hud_color)

        for i in [-30, 0, 30]:
            line_y_offset = vertical_offset - (radians(i) * pitch_scale)
            if abs(center_y + line_y_offset - center_y) > SCREEN_HEIGHT / 3: continue
            line_half_width = 80 if i == 0 else 40
            line_color = HUD_BLUE if i == 0 else final_hud_color
            line_thickness = 3 if i == 0 else 1.5
            start_pos = vector2_add(vector2_rotate(Vector2(-line_half_width, 0), roll_rad), Vector2(center_x, center_y + line_y_offset))
            end_pos = vector2_add(vector2_rotate(Vector2(line_half_width, 0), roll_rad), Vector2(center_x, center_y + line_y_offset))
            draw_line_ex(start_pos, end_pos, line_thickness, line_color)

        # speedometer
        speed_bar_pos = Rectangle(40, center_y - 100, 20, 200)
        current_speed_val = vector3_length(self.velocity) * 10
        absolute_max_speed_display = self.max_speed * self.boost_speed_multiplier * 10
        speed_ratio = min(current_speed_val / absolute_max_speed_display, 1.0)

        draw_rectangle_rec(speed_bar_pos, fade(BLACK, 0.5))
        fill_height = speed_bar_pos.height * speed_ratio
        draw_rectangle(int(speed_bar_pos.x), int(speed_bar_pos.y + speed_bar_pos.height - fill_height), int(speed_bar_pos.width), int(fill_height), speedo_color)
        draw_rectangle_lines_ex(speed_bar_pos, 2, speedo_color)

        normal_speed_ratio = (self.max_speed * 10) / absolute_max_speed_display
        marker_y = speed_bar_pos.y + speed_bar_pos.height * (1.0 - normal_speed_ratio)
        draw_line(int(speed_bar_pos.x), int(marker_y), int(speed_bar_pos.x + speed_bar_pos.width), int(marker_y), WHITE)
        
        spd_text = "SPEED"
        font_size = 20
        char_spacing = 5 
        total_text_height = len(spd_text) * font_size + (len(spd_text) - 1) * char_spacing
        y_start_spd = speed_bar_pos.y + (speed_bar_pos.height - total_text_height) / 2
        x_pos_spd = speed_bar_pos.x - 25

        for i, char in enumerate(spd_text):
            char_width = measure_text(char, font_size)
            draw_text(char, int(x_pos_spd - char_width / 2), int(y_start_spd + i * (font_size + char_spacing)), font_size, speedo_color)
        
        
        speed_value_text = f"{int(current_speed_val)}"
        speed_text_width = measure_text(speed_value_text, 20)
        draw_text(
            speed_value_text, 
            int(speed_bar_pos.x + speed_bar_pos.width / 2 - speed_text_width / 2), 
            int(speed_bar_pos.y + speed_bar_pos.height + 10), 
            20, 
            speedo_color
        )
        
        # boost bar
        boost_bar_pos = Rectangle(80, center_y - 100, 20, 200)
        boost_ratio = self.current_boost_time / self.max_boost_time

        if boost_ratio > 0.5: boost_color = speedo_color
        elif boost_ratio > 0.2: boost_color = YELLOW
        else: boost_color = RED
        if self.is_invulnerable: boost_color = PURPLE

        draw_rectangle_rec(boost_bar_pos, fade(BLACK, 0.5))
        fill_height_boost = boost_bar_pos.height * boost_ratio
        draw_rectangle(int(boost_bar_pos.x), int(boost_bar_pos.y + boost_bar_pos.height - fill_height_boost), int(boost_bar_pos.width), int(fill_height_boost), boost_color)
        draw_rectangle_lines_ex(boost_bar_pos, 2, speedo_color)

        bst_text = "BOOST"
        y_start_bst = boost_bar_pos.y + (boost_bar_pos.height - total_text_height) / 2
        x_pos_bst = boost_bar_pos.x + boost_bar_pos.width + 15

        for i, char in enumerate(bst_text):
            char_width = measure_text(char, font_size)
            draw_text(char, int(x_pos_bst - char_width / 2), int(y_start_bst + i * (font_size + char_spacing)), font_size, speedo_color)

        
        # radar in the bottom right
        radar_center = Vector2(SCREEN_WIDTH - 130, SCREEN_HEIGHT - 140)
        radar_radius = 100.0
        player_heading_deg = -degrees(camera_yaw)
        draw_circle_v(radar_center, radar_radius, fade(BLACK, 0.5))
        fov_angle = 60
        draw_circle_sector(radar_center, radar_radius - 5, player_heading_deg - fov_angle / 2, player_heading_deg + fov_angle / 2, 30, fade(final_hud_color, 0.2))

        cardinals = {'N': 0, 'E': 90, 'S': 180, 'W': 270}
        for text, angle in cardinals.items():
            rad = radians(angle - player_heading_deg)
            text_pos = Vector2(radar_center.x + sin(rad) * (radar_radius - 15), radar_center.y - cos(rad) * (radar_radius - 15))
            line_start = Vector2(radar_center.x + sin(rad) * (radar_radius), radar_center.y - cos(rad) * (radar_radius))
            line_end = Vector2(radar_center.x + sin(rad) * (radar_radius-5), radar_center.y - cos(rad) * (radar_radius-5))
            draw_text(text, int(text_pos.x - measure_text(text, 10)/2), int(text_pos.y - 10), 10, final_hud_color)
            draw_line_v(line_start, line_end, final_hud_color)

        draw_circle_lines(int(radar_center.x), int(radar_center.y), radar_radius, final_hud_color)
        draw_circle_lines(int(radar_center.x), int(radar_center.y), radar_radius / 2, fade(final_hud_color, 0.3))
        draw_circle_v(radar_center, 5, final_hud_color)
        
        rad_text = "In a 320m radius"
        text_width_rad = measure_text(rad_text, 14)
        draw_text(rad_text, int(radar_center.x - text_width_rad/2), int(radar_center.y + radar_radius + 10), 14, final_hud_color)

        
        # TODO: iterate through enemies here.

        if self.is_invulnerable:
            remaining_time = self.invulnerability_timer.duration - (get_time() - self.invulnerability_timer.start_time)
            inv_text = f"INVULNERABLE: {remaining_time:.1f}s"
            text_width = measure_text(inv_text, 20)
            draw_text(inv_text, center_x - text_width // 2, center_y + 80, 20, PURPLE)
        
        if self.show_boost_drained_message:
            alpha = int(abs(sin(get_time() * 10)) * 255)
            warning_color = Color(255, 255, 0, alpha) # yellow

            boost_text = "BOOST DRAINED!"
            text_width = measure_text(boost_text, 30)
            draw_text(boost_text, center_x - text_width // 2, center_y + 120, 30, warning_color)