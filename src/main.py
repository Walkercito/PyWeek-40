from settings import * 

from models import Fog, WallCube
from player import Player
from skybox import Skybox
from bullet import BulletManager
from building_manager import BuildingManager
from enemy import EnemyManager
from vfx_manager import VFXManager


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

        self.base_fov = BASE_FOV
        self.boost_fov = BOOST_FOV
        self.camera.fovy = self.base_fov

        self.camera_yaw = 0.0 
        self.camera_pitch = 0.2
        self.camera_distance = 15.0 
        self.camera_target_offset = Vector3(0, 1.0, 0)
        self.camera_smooth_factor = 5.0

        self.warning_sound_timer = Timer(1.0)
        self.camera_shake_timer = Timer(0.3)
        self.camera_shake_intensity = CAMERA_SHAKE_INTENSITY

        self.show_altitude_warning = False
        self.ALTITUDE_WARNING_Y = ALTITUDE_WARNING_Y
        
        self.show_boundary_warning = False
        self.world_boundary = CITY_RADIUS + 50.0

        self.color_phase = 0.0
        self.current_color_index = 0
        self.last_color_change = -1
        self.base_colors = [
            Vector3(0.6, 0.8, 1.0), Vector3(0.5, 0.7, 0.9),
            Vector3(0.7, 0.8, 1.0), Vector3(0.4, 0.6, 0.8),
        ]

        wall_size = 1000
        self.fog = Fog(self.camera, size=wall_size, segments=50)
        self.fog.set_fog_parameters(
            density=0.7, speed=0.2, scale=6.0,
            height=8.0, color=Vector3(0.6, 0.8, 1.0)
        )

        self.wall_cube = WallCube(size=wall_size, height=200)

        self.bullet_manager = BulletManager()
        self.current_bullet_type = "normal"
        self.shoot_cooldown = Timer(0.02) 
        self.is_shooting = False

        self.weapon_heat = 0.0
        self.max_weapon_heat = 8.0    
        self.heat_increase_rate = 1.0 
        self.heat_decrease_rate = 2.0 
        self.is_overheated = False
        
        self.overheat_message_timer = Timer(2.0)
        self.show_overheat_message = False

        self.player = Player(self.models["player"])
        self.camera.position = Vector3(self.player.position.x, self.player.position.y + 10, self.player.position.z + self.camera_distance)
        self.camera.target = vector3_add(self.player.position, self.camera_target_offset)

        self.building_manager = BuildingManager(self.models)
        self.building_manager.generate_city()

        self.vfx_manager = VFXManager()
        self.enemy_manager = EnemyManager(self.models, self.vfx_manager)
 
        print("[*] Spawning initial test enemies...")
        self.enemy_manager.spawn_enemy(Vector3(200, 60, 200), "fighter")
        self.enemy_manager.spawn_enemy(Vector3(-150, 80, -180), "interceptor")
        self.enemy_manager.spawn_enemy(Vector3(0, 90, -250), "bomber")
        print(f"[*] Initial enemies spawned. Active count: {self.enemy_manager.get_enemy_count()}")

        self.show_debug_boxes = False
        self.show_oriented_debug = False
        self.show_wall_wireframe = False

        self.skybox = Skybox()


    def import_assets(self):
        print("[*] Loading game assets...")
        self.models = {
            "player": load_model(join("assets", "models", "player", "plane01.glb")),
            "skyscraper01": load_model(join("assets", "models", "buildings", "1.glb")),
            "skyscraper02": load_model(join("assets", "models", "buildings", "2.glb")),
        }

        enemy_models = {
            "enemy01": join("assets", "models", "enemies", "enemy01.glb"),
            "enemy02": join("assets", "models", "enemies", "enemy02.glb"),
        }
        
        for model_name, model_path in enemy_models.items():
            try:
                if exists(model_path):
                    self.models[model_name] = load_model(model_path)
                    print(f"[*] Loaded enemy model: {model_name}")
                else:
                    print(f"[!] Enemy model file not found: {model_path}")
                    self.models[model_name] = None
            except Exception as e:
                print(f"[ERROR] Failed to load {model_name}: {e}")
                self.models[model_name] = None
        
        self.audio = {
            "warning": load_sound(join("assets", "audio", "beep-warning.mp3")),
        }
        print("[*] Asset loading complete!")
    

    def shoot(self, position, forward_vector):
        if self.shoot_cooldown: 
            return
            
        shoot_direction = vector3_normalize(forward_vector)
        offset = vector3_scale(shoot_direction, 2.5)
        shoot_position = vector3_add(position, offset)

        bullet = self.bullet_manager.add_bullet(shoot_position, shoot_direction, self.current_bullet_type)
        
        self.shoot_cooldown.activate()

        if DEBUG:
            print(f"Fired {self.current_bullet_type} bullet! Active bullets: {self.bullet_manager.get_bullet_count()}")


    def start_overheat_message(self):
        self.show_overheat_message = True
        self.overheat_message_timer.activate()


    def end_overheat_message(self):
        self.show_overheat_message = False
        self.overheat_message_timer.deactivate()


    def update_overheat_message(self):
        if not self.show_overheat_message:
            return
        
        self.overheat_message_timer.update()
        
        if not self.overheat_message_timer:
            self.end_overheat_message()


    def cycle_fog_color(self):
        self.current_color_index = (self.current_color_index + 1) % len(self.base_colors)


    def handle_shooting(self, player_forward_vector):
        self.is_shooting = is_mouse_button_down(MOUSE_BUTTON_LEFT)

        if self.is_shooting and not self.shoot_cooldown and not self.is_overheated:
            self.shoot(self.player.position, player_forward_vector)


    def handle_weapon_switching(self):
        if is_key_pressed(KEY_ONE):
            self.current_bullet_type = "normal"
        elif is_key_pressed(KEY_TWO):
            self.current_bullet_type = "heavy"
        elif is_key_pressed(KEY_THREE):
            self.current_bullet_type = "rapid"


    def check_collisions(self):
        if self.player.is_dying:
            return False

        collidable_objects = self.building_manager.get_collision_objects()
        for obj in collidable_objects:
            if self.player.check_collision_with(obj):
                self.handle_collision(obj)
                return True

        for enemy in self.enemy_manager.get_enemies():
            if self.player.check_collision_with(enemy):
                self.handle_enemy_collision(enemy)
                return True
        
        return False


    def check_player_bullet_collisions(self):
        if self.player.is_invulnerable or self.player.is_dying:
            return

        for bullet in self.bullet_manager.bullets:
            if bullet.active and bullet.check_collision_with(self.player):
                damage_dealt = bullet.on_hit(self.player)
                self.player.take_damage(damage_dealt, on_death=self.player_death_callback)
                self.camera_shake_timer.activate()
                self.vfx_manager.create_explosion(bullet.position, "explosion_air01", scale=3.0)

                break

    def handle_collision(self, collided_object):
        if self.player.is_invulnerable:
            return
        
        self.vfx_manager.create_explosion(self.player.position, "explosion_air01")
        self.camera_shake_timer.activate()
        
        is_fatal = (self.player.health - 25) <= 0
        self.player.take_damage(25, on_death=self.player_death_callback)

        if not is_fatal:
            if hasattr(collided_object, 'has_multiple_collision_boxes') and collided_object.has_multiple_collision_boxes:
                collision_part = self.identify_collision_part(collided_object)
                collision_reason = f"building collision - {collision_part}"
            else:
                collision_reason = "building collision"
            
            self.player.start_invulnerability(collision_reason)


    def handle_enemy_collision(self, enemy):
        if self.player.is_invulnerable:
            return

        player_damage = 40
        enemy_damage = 60
        
        self.vfx_manager.create_explosion(self.player.position, "explosion_air02")
        self.camera_shake_timer.activate()

        is_fatal = (self.player.health - player_damage) <= 0
        self.player.take_damage(player_damage, on_death=self.player_death_callback)
        enemy.take_damage(enemy_damage)

        if not is_fatal:
            self.player.start_invulnerability("enemy collision")

    def player_death_callback(self):
        self.vfx_manager.create_explosion(
            self.player.position, 
            "explosion_air01", 
            on_finish=self.player.respawn
        )

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
        
        collidable_objects = self.building_manager.get_collision_objects()
        for obj in collidable_objects:
            if hasattr(obj, 'has_multiple_collision_boxes') and obj.has_multiple_collision_boxes:
                boxes = obj.get_world_bounding_boxes()
                for i, box in enumerate(boxes):
                    color = part_colors[i % len(part_colors)]
                    draw_bounding_box(box, color)
            else:
                obj_box = obj.get_world_bounding_box()
                if obj_box:
                    draw_bounding_box(obj_box, RED)


    def check_player_bounds(self, dt):
        distance_from_center = sqrt(self.player.position.x**2 + self.player.position.z**2)
        
        if distance_from_center > self.world_boundary:
            self.show_boundary_warning = True
            
            distance_out = distance_from_center - self.world_boundary
            damage_per_second = BOUNDARY_DAMAGE_START + (distance_out * BOUNDARY_DAMAGE_SCALING)
            damage_to_apply = damage_per_second * dt
            
            self.player.take_damage(damage_to_apply, on_death=self.player_death_callback)
        else:
            self.show_boundary_warning = False


    def update(self):
        dt = get_frame_time()
        mouse_delta = get_mouse_delta()

        self.warning_sound_timer.update()
        self.camera_shake_timer.update()
        self.shoot_cooldown.update() 
        self.update_overheat_message() 

        if not self.player.is_dying:
            self.camera_yaw -= mouse_delta.x * MOUSE_SENSITIVITY
            self.camera_pitch -= mouse_delta.y * MOUSE_SENSITIVITY
            self.camera_pitch = min(max(self.camera_pitch, -1.5), 1.5)

            player_forward_x = -sin(self.camera_yaw) * cos(self.camera_pitch)
            player_forward_y = -sin(self.camera_pitch)
            player_forward_z = -cos(self.camera_yaw) * cos(self.camera_pitch)
            player_forward_vector = vector3_normalize(Vector3(player_forward_x, player_forward_y, player_forward_z))

            self.handle_shooting(player_forward_vector)
            self.handle_weapon_switching()

            if self.is_shooting and not self.is_overheated:
                self.weapon_heat += self.heat_increase_rate * dt 
                if self.weapon_heat >= self.max_weapon_heat:
                    self.weapon_heat = self.max_weapon_heat
                    self.is_overheated = True
                    if not self.show_overheat_message:
                        self.start_overheat_message() 
            else:
                self.weapon_heat -= self.heat_decrease_rate * dt
                if self.weapon_heat < 0:
                    self.weapon_heat = 0
                
                if self.is_overheated and self.weapon_heat <= 0:
                    self.is_overheated = False

            self.player.update(dt, player_forward_vector, mouse_delta.x)
        else:
            player_forward_vector = Vector3(0,0,0)


        spatial_grid = self.building_manager.get_spatial_grid()
        self.bullet_manager.update(dt, spatial_grid)

        self.vfx_manager.update(dt)
        self.enemy_manager.update(dt, self.player.position, spatial_grid, self.bullet_manager)

        self.check_player_bullet_collisions()
        self.check_collisions()
        self.check_player_bounds(dt)
        
        altitude_warning_active = self.player.position.y <= self.ALTITUDE_WARNING_Y and not self.player.is_invulnerable
        self.show_altitude_warning = altitude_warning_active
        
        is_any_warning_active = self.player.is_invulnerable or altitude_warning_active or self.show_boundary_warning

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
            if is_key_pressed(KEY_N):
                self.show_wall_wireframe = not self.show_wall_wireframe
            if is_key_pressed(KEY_G):
                self.building_manager.clear_all()
                self.building_manager.generate_city()
            if is_key_pressed(KEY_I):
                if not self.player.is_invulnerable:
                    self.player.start_invulnerability("manual test")
            if is_key_pressed(KEY_C):
                self.bullet_manager.clear_all()

            if is_key_pressed(KEY_E):
                spawn_pos = Vector3(
                    self.player.position.x + uniform(-100, 100),
                    self.player.position.y + uniform(20, 40),
                    self.player.position.z + uniform(-100, 100)
                )
                spawned = self.enemy_manager.spawn_enemy(spawn_pos)
                if spawned:
                    print(f"[*] Manual enemy spawn successful")
                else:
                    print(f"[!] Manual enemy spawn failed")
            
            if is_key_pressed(KEY_R):
                enemy_count = self.enemy_manager.get_enemy_count()
                self.enemy_manager.clear_all()
                print(f"[*] Cleared {enemy_count} enemies")


    def draw(self):
        begin_drawing()
        clear_background(BLACK)
        begin_mode_3d(self.camera)

        self.skybox.draw()
        self.wall_cube.draw()

        self.fog.draw()
        self.player.draw()
        self.building_manager.draw(camera=self.camera)
        self.bullet_manager.draw(camera=self.camera)
        self.vfx_manager.draw(self.camera)
        
        self.enemy_manager.draw()

        if DEBUG:
            self.draw_debug_boxes()
            if self.show_wall_wireframe:
                self.wall_cube.draw_wireframe()

        end_mode_3d()
        self.draw_ui()
        end_drawing()


    def draw_ui(self):
        draw_text(f"FPS: {get_fps()}", 10, 10, 20, Color(50, 255, 150, 255))
        
        enemy_count = self.enemy_manager.get_enemy_count()
        draw_text(f"ENEMIES: {enemy_count}", SCREEN_WIDTH - 150, 10, 20, Color(255, 100, 100, 255))

        radar_mode = "ENHANCED" if self.player.radar_enhanced_mode else "STANDARD"
        draw_text(f"RADAR: {radar_mode}", SCREEN_WIDTH - 150, 35, 16, Color(0, 255, 100, 255))
        
        weapon_heat_ratio = self.weapon_heat / self.max_weapon_heat if self.max_weapon_heat > 0 else 0
        self.player.draw_hud(
            self.camera_pitch,
            self.camera_yaw,
            self.show_altitude_warning or self.show_boundary_warning,
            weapon_heat_ratio=weapon_heat_ratio,
            is_overheated=self.is_overheated,
            enemies=self.enemy_manager.get_enemies()
        )

        if self.show_altitude_warning:
            alpha = int(abs(sin(get_time() * 10)) * 255)
            warning_color = Color(255, 50, 50, alpha)
            
            text = "WARNING: PULL UP!"
            text_width = measure_text(text, FONT_SIZE)
            text_pos_x = (SCREEN_WIDTH - text_width) // 2
            text_pos_y = SCREEN_HEIGHT - FONT_SIZE - FONT_PADDING

            draw_text(text, text_pos_x, text_pos_y, FONT_SIZE, warning_color)

        if self.show_boundary_warning:
            alpha = int(abs(sin(get_time() * 5)) * 255)
            warning_color = Color(255, 165, 0, alpha)
            
            text = "RETURN TO BATTLEFIELD!"
            text_width = measure_text(text, 40)
            text_pos_x = (SCREEN_WIDTH - text_width) // 2
            text_pos_y = SCREEN_HEIGHT - FONT_SIZE - FONT_PADDING - 60

            draw_text(text, text_pos_x, text_pos_y, 40, warning_color)

        if self.show_overheat_message:
            alpha = int(abs(sin(get_time() * 10)) * 255)
            warning_color = Color(255, 255, 0, alpha)
            text = "OVERHEATED!!!"
            text_width = measure_text(text, 30)
            draw_text(text, (SCREEN_WIDTH - text_width) // 2, SCREEN_HEIGHT // 2 + 120, 30, warning_color)

        if DEBUG:
            if self.show_debug_boxes:
                draw_text("DEBUG: AABB Boxes ON", 10, 40, 20, YELLOW)
                draw_text("GREEN=Vulnerable, PURPLE=Invulnerable", 10, 65, 14, WHITE)
                draw_text("RED=Base(-5 to 67.6), BLUE=2nd(67.6 to 94.0), YELLOW=Antenna(94.0 to 128.9)", 10, 85, 12, WHITE)
            if self.show_oriented_debug:
                draw_text("DEBUG: Oriented Box ON", 10, 110, 20, LIME)
                draw_text("GREEN=Vulnerable, PURPLE=Invulnerable - Rotating", 10, 135, 14, WHITE)
            if self.show_wall_wireframe:
                draw_text("DEBUG: Wall Wireframe ON", 10, 160, 20, CYAN)
            
            draw_text("DEBUG CONTROLS:", 10, SCREEN_HEIGHT - 300, 16, YELLOW)
            draw_text("[LEFT CLICK] to shoot (hold for continuous)", 10, SCREEN_HEIGHT - 280, 14, WHITE)
            draw_text("[TAB] to toggle enhanced radar mode", 10, SCREEN_HEIGHT - 260, 14, WHITE)
            draw_text("[G] to generate a new random city", 10, SCREEN_HEIGHT - 240, 14, WHITE)
            draw_text("[B] to toggle AABB boxes", 10, SCREEN_HEIGHT - 220, 14, WHITE)
            draw_text("[V] to toggle oriented plane box", 10, SCREEN_HEIGHT - 200, 14, WHITE)
            draw_text("[N] to toggle wall wireframe", 10, SCREEN_HEIGHT - 180, 14, WHITE)
            draw_text("[E] to spawn enemy manually", 10, SCREEN_HEIGHT - 160, 14, WHITE)
            draw_text("[R] to clear all enemies", 10, SCREEN_HEIGHT - 140, 14, WHITE)
            draw_text("[I] to test invulnerability", 10, SCREEN_HEIGHT - 120, 14, WHITE)
            draw_text("[C] to clear all bullets", 10, SCREEN_HEIGHT - 100, 14, WHITE)

            building_stats = self.building_manager.get_instancing_stats()
            draw_text(f"Buildings: {building_stats['total']} (Simple: {building_stats['simple']}, Complex: {building_stats['complex']})", 10, SCREEN_HEIGHT - 80, 14, WHITE)
            draw_text(f"Building Instancing: {'ON' if building_stats['instancing_enabled'] else 'OFF'} - Draw calls: {building_stats['draw_calls']}", 10, SCREEN_HEIGHT - 60, 14, YELLOW)

            bullet_status = "ON" if self.bullet_manager.instancing_enabled else "OFF"
            draw_text(f"Bullet Instancing: {bullet_status} - Active bullets: {self.bullet_manager.get_bullet_count()}", 10, SCREEN_HEIGHT - 40, 14, WHITE)

            draw_text(f"Active Enemies: {enemy_count}", 10, SCREEN_HEIGHT - 20, 14, Color(255, 100, 100, 255))

            y_offset = 400
            for i, enemy in enumerate(self.enemy_manager.get_enemies()[:3]):
                distance = vector3_distance(self.player.position, enemy.position)
                info_text = f"Enemy {i+1}: {enemy.enemy_type} | {enemy.debug_info} | Dist: {distance:.1f}m"
                draw_text(info_text, 10, y_offset + (i * 15), 12, ORANGE)

            if self.player.is_invulnerable:
                draw_text("STATUS: INVULNERABLE", 10, 350, 18, PURPLE)
            else:
                draw_text("STATUS: VULNERABLE", 10, 350, 18, GREEN)


    def cleanup(self):
        for model in self.models.values():
            unload_model(model)
        for sound in self.audio.values():
            unload_sound(sound)
        enable_cursor()
        self.skybox.deinit()


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