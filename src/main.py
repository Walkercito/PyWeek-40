from settings import * 

from player import Player
from models import Fog, Skycraper, SkycraperMultipleLayer
from bullet import BulletManager


class Game:
    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, "Skyscraper")
        init_audio_device()
        set_target_fps(FPS)
        disable_cursor()
        
        self.import_assets()

        self.camera = Camera3D()
        self.camera.up = Vector3(0.0, 1.0, 0.0) 
        self.camera.projection = CAMERA_PERSPECTIVE

        self.base_fov = 45.0
        self.boost_fov = 60.0
        self.camera.fovy = self.base_fov

        self.camera_yaw = 0.0 
        self.camera_pitch = 0.2
        self.camera_distance = 15.0 
        self.camera_target_offset = Vector3(0, 1.0, 0)
        self.camera_smooth_factor = 5.0

        self.warning_sound_timer = Timer(1.0)
        self.camera_shake_timer = Timer(0.3)
        self.camera_shake_intensity = 0.8

        self.show_altitude_warning = False
        self.ALTITUDE_WARNING_Y = 12.0

        self.color_phase = 0.0
        self.current_color_index = 0
        self.last_color_change = -1
        self.base_colors = [
            Vector3(0.6, 0.8, 1.0), Vector3(0.5, 0.7, 0.9),
            Vector3(0.7, 0.8, 1.0), Vector3(0.4, 0.6, 0.8),
        ]

        self.fog = Fog(self.camera, size=200, segments=50)
        self.fog.set_fog_parameters(
            density=0.7, speed=0.2, scale=6.0,
            height=8.0, color=Vector3(0.6, 0.8, 1.0)
        )

        self.bullet_manager = BulletManager()
        self.current_bullet_type = "normal"
        self.shoot_cooldown = Timer(0.02) 
        self.is_shooting = False

        self.player = Player(self.models["player"])
        self.camera.position = Vector3(self.player.position.x, self.player.position.y + 10, self.player.position.z + self.camera_distance)
        self.camera.target = vector3_add(self.player.position, self.camera_target_offset)

        self.collidable_objects = []
        
        self.skyscraper_complex = SkycraperMultipleLayer(self.models["skyscraper01"], Vector3(0, -10, 50))
        self.collidable_objects.append(self.skyscraper_complex)

        self.show_debug_boxes = False
        self.show_oriented_debug = False


    def import_assets(self):
        self.models = {
            "player": load_model(join("assets", "models", "player", "plane01.glb")),
            "skyscraper01": load_model(join("assets", "models", "buildings", "1.glb")),
            "skyscraper02": load_model(join("assets", "models", "buildings", "2.glb"))
        }
        self.audio = {
            "warning": load_sound(join("assets", "audio", "beep-warning.mp3")),
        }
    

    def shoot(self, position, forward_vector):
        if self.shoot_cooldown: 
            return
            
        shoot_direction = vector3_normalize(forward_vector)
        offset = vector3_scale(shoot_direction, 2.5)
        shoot_position = vector3_add(position, offset)

        bullet = self.bullet_manager.add_bullet(shoot_position, shoot_direction, self.current_bullet_type)
        
        self.shoot_cooldown.activate()
        # TODO: add a sound

        if DEBUG:
            print(f"Fired {self.current_bullet_type} bullet! Active bullets: {self.bullet_manager.get_bullet_count()}")


    def cycle_fog_color(self):
        self.current_color_index = (self.current_color_index + 1) % len(self.base_colors)


    def handle_shooting(self, player_forward_vector):
        self.is_shooting = is_mouse_button_down(MOUSE_BUTTON_LEFT)

        if self.is_shooting and not self.shoot_cooldown:
            self.shoot(self.player.position, player_forward_vector)


    def handle_weapon_switching(self):
        if is_key_pressed(KEY_ONE):
            self.current_bullet_type = "normal"
        elif is_key_pressed(KEY_TWO):
            self.current_bullet_type = "heavy"
        elif is_key_pressed(KEY_THREE):
            self.current_bullet_type = "rapid"


    def check_collisions(self):
        for obj in self.collidable_objects:
            if self.player.check_collision_with(obj):
                self.handle_collision(obj)
                return True
        return False


    def handle_collision(self, collided_object):
        if self.player.is_invulnerable:
            return
        
        if hasattr(collided_object, 'has_multiple_collision_boxes') and collided_object.has_multiple_collision_boxes:
            collision_part = self.identify_collision_part(collided_object)
            collision_reason = f"building collision - {collision_part}"
        else:
            collision_reason = "building collision"
        
        self.player.start_invulnerability(collision_reason)
        self.camera_shake_timer.activate()


    def identify_collision_part(self, building):
        if not hasattr(building, 'get_world_bounding_boxes'):
            return "building"
        
        player_box = self.player.get_world_bounding_box()
        if not player_box:
            return "building"
        
        boxes = building.get_world_bounding_boxes()
        parts = ["BASE (Y: -5 to 67.6)", "SECOND FLOOR (Y: 67.6 to 94.0)", "ANTENNA (Y: 94.0 to 128.9)"]
        
        for i, box in enumerate(boxes):
            if check_collision_boxes(player_box, box):
                return parts[i] if i < len(parts) else f"part {i+1}"
        
        return "building"


    def draw_debug_boxes(self):
        if not DEBUG or not self.show_debug_boxes:
            return
            
        player_box = self.player.get_world_bounding_box()
        if player_box:
            player_color = Color(128, 0, 128, 100) if self.player.is_invulnerable else Color(0, 255, 0, 100)
            draw_bounding_box(player_box, player_color)
        
        part_colors = [RED, BLUE, YELLOW, PURPLE, ORANGE]
        
        for obj in self.collidable_objects:
            if hasattr(obj, 'has_multiple_collision_boxes') and obj.has_multiple_collision_boxes:
                boxes = obj.get_world_bounding_boxes()
                for i, box in enumerate(boxes):
                    color = part_colors[i % len(part_colors)]
                    draw_bounding_box(box, color)
            else:
                obj_box = obj.get_world_bounding_box()
                if obj_box:
                    draw_bounding_box(obj_box, RED)


    def generate_precise_city(self, count=10):
        if not DEBUG:
            return
            
        for i in range(count):
            x = uniform(-100, 100)
            z = uniform(-100, 100)
            
            if abs(x) < 15 and abs(z) < 15:
                continue
            
            if randint(1, 10) <= 4:
                building = SkycraperMultipleLayer(self.models["skyscraper01"], Vector3(x, -10, z))
                print(f"Generating SkycraperMultipleLayer at ({x:.1f}, {z:.1f}) - Max height: 128.9m")
            else:
                building_model = choice([self.models["skyscraper01"], self.models["skyscraper02"]])
                building = Skycraper(building_model, Vector3(x, -10, z))
                
                if randint(1, 100) <= 10:
                    building.has_collision = False
            
            self.collidable_objects.append(building)


    def update(self):
        dt = get_frame_time()
        mouse_delta = get_mouse_delta()

        self.warning_sound_timer.update()
        self.camera_shake_timer.update()
        self.shoot_cooldown.update() 

        self.camera_yaw -= mouse_delta.x * MOUSE_SENSITIVITY
        self.camera_pitch -= mouse_delta.y * MOUSE_SENSITIVITY
        self.camera_pitch = min(max(self.camera_pitch, -1.5), 1.5)

        player_forward_x = -sin(self.camera_yaw) * cos(self.camera_pitch)
        player_forward_y = -sin(self.camera_pitch)
        player_forward_z = -cos(self.camera_yaw) * cos(self.camera_pitch)
        player_forward_vector = vector3_normalize(Vector3(player_forward_x, player_forward_y, player_forward_z))

        self.handle_shooting(player_forward_vector)

        self.player.update(dt, player_forward_vector, mouse_delta.x)

        self.bullet_manager.update(dt, self.collidable_objects)

        self.check_collisions()
        
        altitude_warning_active = self.player.position.y <= self.ALTITUDE_WARNING_Y and not self.player.is_invulnerable
        self.show_altitude_warning = altitude_warning_active

        is_any_warning_active = self.player.is_invulnerable or altitude_warning_active

        if is_any_warning_active:
            if not self.warning_sound_timer:
                play_sound(self.audio["warning"])
                self.warning_sound_timer.activate()
        else:
            if is_sound_playing(self.audio["warning"]):
                stop_sound(self.audio["warning"])

        target_fov = self.boost_fov if self.player.is_boosting else self.base_fov
        self.camera.fovy = lerp(self.camera.fovy, target_fov, self.camera_smooth_factor * dt)

        target_cam_x = self.player.position.x + (self.camera_distance * cos(self.camera_pitch) * sin(self.camera_yaw))
        target_cam_y = self.player.position.y + (self.camera_distance * sin(self.camera_pitch))
        target_cam_z = self.player.position.z + (self.camera_distance * cos(self.camera_pitch) * cos(self.camera_yaw))
        target_camera_pos = Vector3(target_cam_x, target_cam_y, target_cam_z)
        target_camera_lookat = vector3_add(self.player.position, self.camera_target_offset)
        
        self.camera.position = vector3_lerp(self.camera.position, target_camera_pos, self.camera_smooth_factor * dt)
        self.camera.target = vector3_lerp(self.camera.target, target_camera_lookat, self.camera_smooth_factor * dt)
        
        if self.camera_shake_timer:
            offset_x = uniform(-1, 1) * self.camera_shake_intensity
            offset_y = uniform(-1, 1) * self.camera_shake_intensity
            self.camera.position.x += offset_x
            self.camera.position.y += offset_y

        self.color_phase += dt * 0.3
        current_color = self.base_colors[self.current_color_index]
        next_color_index = (self.current_color_index + 1) % len(self.base_colors)
        next_color = self.base_colors[next_color_index]
        blend_factor = (sin(self.color_phase) + 1.0) * 0.5
        dynamic_color = vector3_lerp(current_color, next_color, blend_factor)
        pulse_factor = 1.0 + 0.1 * sin(get_time() * 2.0)
        dynamic_density = 0.7 * pulse_factor
        
        self.fog.set_fog_parameters(color=dynamic_color, density=min(1.0, dynamic_density))
        
        current_time_int = int(self.color_phase)
        if current_time_int % 6 == 0 and current_time_int != self.last_color_change and current_time_int > 0:
            self.cycle_fog_color()
            self.last_color_change = current_time_int
        
        self.fog.update(dt)

        if DEBUG:
            if is_key_pressed(KEY_B):
                self.show_debug_boxes = not self.show_debug_boxes
            if is_key_pressed(KEY_V):
                self.show_oriented_debug = not self.show_oriented_debug
                self.player._show_oriented_debug = self.show_oriented_debug
            if is_key_pressed(KEY_G):
                self.generate_precise_city(10)
            if is_key_pressed(KEY_I):
                if not self.player.is_invulnerable:
                    self.player.start_invulnerability("manual test")
            if is_key_pressed(KEY_C):
                self.bullet_manager.clear_all()


    def draw(self):
        begin_drawing()
        clear_background(BLACK)
        begin_mode_3d(self.camera)

        self.fog.draw()
        self.player.draw()

        for obj in self.collidable_objects:
            obj.draw()

        self.bullet_manager.draw()

        if DEBUG:
            self.draw_debug_boxes()

        end_mode_3d()
        self.draw_ui()
        end_drawing()


    def draw_ui(self):
        draw_text(f"FPS: {get_fps()}", 10, 10, 20, Color(50, 255, 150, 255))
        self.player.draw_hud(self.camera_pitch, self.camera_yaw, self.show_altitude_warning)

        weapon_info = f"Weapon: {self.current_bullet_type.upper()}"
        draw_text(weapon_info, SCREEN_WIDTH - 300, 10, 20, Color(255, 255, 0, 255))
        
        bullet_count = f"Bullets: {self.bullet_manager.get_bullet_count()}"
        draw_text(bullet_count, SCREEN_WIDTH - 300, 35, 16, Color(200, 200, 200, 255))

        if self.is_shooting:
            shooting_text = "FIRING..."
            draw_text(shooting_text, SCREEN_WIDTH - 300, 60, 14, Color(255, 255, 100, 255))
        elif self.shoot_cooldown:
            cooldown_text = "RELOADING..."
            draw_text(cooldown_text, SCREEN_WIDTH - 300, 60, 14, Color(255, 100, 100, 255))
        else:
            ready_text = "READY"
            draw_text(ready_text, SCREEN_WIDTH - 300, 60, 14, Color(100, 255, 100, 255))

        if self.show_altitude_warning:
            alpha = int(abs(sin(get_time() * 10)) * 255)
            warning_color = Color(255, 50, 50, alpha)
            
            text = "WARNING: PULL UP!"
            text_width = measure_text(text, FONT_SIZE)
            text_pos_x = (SCREEN_WIDTH - text_width) // 2
            text_pos_y = SCREEN_HEIGHT - FONT_SIZE - FONT_PADDING

            draw_text(text, text_pos_x, text_pos_y, FONT_SIZE, warning_color)

        if DEBUG:
            if self.show_debug_boxes:
                draw_text("DEBUG: AABB Boxes ON", 10, 40, 20, YELLOW)
                draw_text("GREEN=Vulnerable, PURPLE=Invulnerable", 10, 65, 14, WHITE)
                draw_text("RED=Base(-5 to 67.6), BLUE=2nd(67.6 to 94.0), YELLOW=Antenna(94.0 to 128.9)", 10, 85, 12, WHITE)
            if self.show_oriented_debug:
                draw_text("DEBUG: Oriented Box ON", 10, 110, 20, LIME)
                draw_text("GREEN=Vulnerable, PURPLE=Invulnerable - Rotating", 10, 135, 14, WHITE)
            draw_text("DEBUG CONTROLS:", 10, SCREEN_HEIGHT - 200, 16, YELLOW)
            draw_text("[LEFT CLICK] to shoot (hold for continuous)", 10, SCREEN_HEIGHT - 180, 14, WHITE)
            draw_text("[G] to generate precise city", 10, SCREEN_HEIGHT - 160, 14, WHITE)
            draw_text("[B] to toggle AABB boxes", 10, SCREEN_HEIGHT - 140, 14, WHITE)
            draw_text("[V] to toggle oriented plane box", 10, SCREEN_HEIGHT - 120, 14, WHITE)
            draw_text("[I] to test invulnerability", 10, SCREEN_HEIGHT - 100, 14, WHITE)
            draw_text("[C] to clear all bullets", 10, SCREEN_HEIGHT - 80, 14, WHITE)
            precise_buildings = sum(1 for obj in self.collidable_objects if hasattr(obj, 'has_multiple_collision_boxes') and obj.has_multiple_collision_boxes)
            draw_text(f"Buildings: {len(self.collidable_objects)} (Multi-layer: {precise_buildings})", 10, SCREEN_HEIGHT - 40, 14, WHITE)

            if self.player.is_invulnerable:
                draw_text("STATUS: INVULNERABLE - RESET TO SPAWN + FULL CONTROL", 10, SCREEN_HEIGHT - 20, 18, PURPLE)
            else:
                draw_text("STATUS: VULNERABLE", 10, SCREEN_HEIGHT - 20, 18, GREEN)


    def cleanup(self):
        for model in self.models.values():
            unload_model(model)
        for sound in self.audio.values():
            unload_sound(sound)
        enable_cursor()


    def run(self):
        while not window_should_close():
            self.update()
            self.draw() 
            
        self.cleanup()
        close_audio_device()
        close_window()



if __name__ == '__main__':
    game = Game()
    game.run()