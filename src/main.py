from settings import *

from skybox import Skybox
from player import Player
from enemy import EnemyManager
from models import Fog, WallCube
from ui_manager import UIManager
from bullet import BulletManager
from vfx_manager import VFXManager
from audio_manager import AudioManager
from building_manager import BuildingManager
from highscore_manager import HighScoreManager


class Game:
    def __init__(self):
        self.resolutions = [(1280, 720), (1600, 900), (1900, 980)]
        self.settings = {
            'resolution_index': 2,
            'fullscreen': False,
            'master_volume': 0.5,
            'muted': False
        }
        init_window(self.resolutions[self.settings['resolution_index']][0],
                    self.resolutions[self.settings['resolution_index']][1], "Skyscraper")
        init_audio_device()
        set_target_fps(FPS)

        self.font = None
        self.import_assets()

        self.game_state = GameState.MAIN_MENU
        self.should_close = False

        self.ui_manager = UIManager(self.font)
        self.highscore_manager = HighScoreManager()

        self.score = 0
        self.player_lives = PLAYER_LIVES
        self.enemies_defeated = 0

        self.setup_ui_elements()
        self.load_external_data()

        self.camera = Camera3D()
        self.camera.up = Vector3(0.0, 1.0, 0.0)
        self.camera.projection = CAMERA_PERSPECTIVE

        self.menu_camera = Camera3D()
        self.menu_camera.position = Vector3(0.0, 2.0, 0.0)
        self.menu_camera.target = Vector3(10.0, 2.0, 0.0)
        self.menu_camera.up = Vector3(0.0, 1.0, 0.0)
        self.menu_camera.fovy = 45.0
        self.menu_camera.projection = CAMERA_PERSPECTIVE
        self.menu_camera_angle = 0.0

        self.base_fov = BASE_FOV
        self.boost_fov = BOOST_FOV
        self.camera.fovy = self.base_fov

        self.camera_yaw = 0.0
        self.camera_pitch = 0.2
        self.camera_distance = 15.0
        self.camera_target_offset = Vector3(0, 1.0, 0)
        self.camera_smooth_factor = 5.0

        self.camera_shake_timer = Timer(0.3)
        self.camera_shake_intensity = CAMERA_SHAKE_INTENSITY
        self.show_altitude_warning = False
        self.show_boundary_warning = False
        self.world_boundary = CITY_RADIUS + 50.0

        self.color_phase = 0.0
        self.current_color_index = 0
        self.last_color_change = -1
        self.base_colors = [Vector3(0.6, 0.8, 1.0), Vector3(0.5, 0.7, 0.9), Vector3(0.7, 0.8, 1.0),
                            Vector3(0.4, 0.6, 0.8)]

        wall_size = 1000
        self.fog = Fog(self.camera, size=wall_size, segments=50)
        self.fog.set_fog_parameters(density=0.7, speed=0.2, scale=6.0, height=8.0, color=Vector3(0.6, 0.8, 1.0))
        self.wall_cube = WallCube(size=wall_size, height=200)

        self.player = Player(self.models["player"])

        self.bullet_manager = BulletManager()
        self.building_manager = BuildingManager(self.models)
        self.vfx_manager = VFXManager()
        self.enemy_manager = EnemyManager(self.models, self.vfx_manager)
        self.audio_manager = AudioManager(self.camera, self.player, self.settings)

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

        self.skybox = Skybox()
        self.building_manager.generate_city()

    def load_external_data(self):
        try:
            with open(join("assets", "ui", "splashes.txt"), 'r') as f:
                self.splashes = [line.strip() for line in f.readlines() if line.strip()]
            self.current_splash = choice(self.splashes) if self.splashes else "Hello!"
        except FileNotFoundError:
            self.splashes = ["Splashes file not found!"]
            self.current_splash = self.splashes[0]

        try:
            with open(join("assets", "ui", "credits.json"), 'r') as f:
                self.credits = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.credits = [{"name": "Error", "reason": "Could not load credits.json", "link": ""}]

        self.link_rects = []
        self.link_hover_states = []

    def setup_ui_elements(self):
        sw, sh = get_screen_width(), get_screen_height()
        btn_width, btn_height = 350, 60
        center_x = (sw - btn_width) / 2

        self.button_rects = {
            "start": Rectangle(center_x, sh / 2, btn_width, btn_height),
            "settings": Rectangle(center_x, sh / 2 + 80, btn_width, btn_height),
            "quit": Rectangle(center_x, sh / 2 + 160, btn_width, btn_height),
            "graphics": Rectangle(center_x, sh / 2 - 80, btn_width, btn_height),
            "controls": Rectangle(center_x, sh / 2, btn_width, btn_height),
            "credits": Rectangle(center_x, sh / 2 + 80, btn_width, btn_height),
            "back": Rectangle(center_x, sh - 120, btn_width, btn_height),
            "resume": Rectangle(center_x, sh / 2 - 80, btn_width, btn_height),
            "main_menu": Rectangle(center_x, sh / 2, btn_width, btn_height),
            "pause_quit": Rectangle(center_x, sh / 2 + 80, btn_width, btn_height),
            "restart": Rectangle(center_x, sh / 2 + 120, btn_width, btn_height),
            "go_main_menu": Rectangle(center_x, sh / 2 + 200, btn_width, btn_height),
            "resolution": Rectangle(sw * 0.6, sh * 0.3, 200, 50),
            "fullscreen": Rectangle(sw * 0.6, sh * 0.4, 200, 50),
            "mute": Rectangle(sw * 0.6, sh * 0.5, 200, 50),
            "vol_down": Rectangle(sw * 0.6, sh * 0.6, 60, 50),
            "vol_up": Rectangle(sw * 0.6 + 140, sh * 0.6, 60, 50),
        }

        self.hover_states = {key: False for key in self.button_rects}

    def reset_game(self):
        print("[*] Resetting game state for a new game...")
        self.score = 0
        self.player_lives = PLAYER_LIVES
        self.enemies_defeated = 0

        self.player.reset()
        self.bullet_manager.clear_all()
        self.enemy_manager.clear_all()
        self.vfx_manager.animations.clear()

        self.weapon_heat = 0.0
        self.is_overheated = False

        self.building_manager.generate_city()
        self.audio_manager.current_game_music = None

        self.enemy_manager.spawn_enemy(Vector3(200, 60, 200), "fighter")
        self.enemy_manager.spawn_enemy(Vector3(-150, 80, -180), "interceptor")
        self.enemy_manager.spawn_enemy(Vector3(0, 90, -250), "bomber")
        print(f"[*] Initial enemies spawned. Active count: {self.enemy_manager.get_enemy_count()}")

    def import_assets(self):
        print("[*] Loading game assets...")
        self.font = load_font(join("assets", "BoldPixels.ttf"))
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
                else:
                    self.models[model_name] = None
            except Exception as e:
                print(f"[ERROR] Failed to load {model_name}: {e}")
                self.models[model_name] = None
        
        print("[*] Non-audio asset loading complete!")

    def shoot(self, position, forward_vector):
        if self.shoot_cooldown:
            return

        shoot_direction = vector3_normalize(forward_vector)
        offset = vector3_scale(shoot_direction, 2.5)
        shoot_position = vector3_add(position, offset)

        self.bullet_manager.add_bullet(shoot_position, shoot_direction, self.current_bullet_type)
        self.shoot_cooldown.activate()

        self.audio_manager.play_sound_3d(
            'shooting',
            self.player.position,
            self.player.velocity,
            base_volume=0.8,
            pitch_variation=0.05
        )

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
        self.audio_manager.play_sound_3d('player_explosion', self.player.position, self.player.velocity, base_volume=0.9)

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
        self.audio_manager.play_sound_3d('player_explosion', self.player.position, self.player.velocity, base_volume=1.0)

        is_fatal = (self.player.health - player_damage) <= 0
        self.player.take_damage(player_damage, on_death=self.player_death_callback)
        enemy.take_damage(enemy_damage)

        if not is_fatal:
            self.player.start_invulnerability("enemy collision")

    def player_death_callback(self):
        self.player_lives -= 1
        self.audio_manager.play_sound_3d('player_explosion', self.player.position, self.player.velocity, base_volume=1.2)
        if self.player_lives > 0:
            self.vfx_manager.create_explosion(
                self.player.position,
                "explosion_air01",
                on_finish=self.player.respawn
            )
        else:
            self.vfx_manager.create_explosion(self.player.position, "explosion_air01")
            self.highscore_manager.save_high_score(self.score)
            self.game_state = GameState.GAME_OVER
            enable_cursor()

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
                return parts[i] if i < len(parts) else f"part {i + 1}"

        return "building"

    def check_player_bounds(self, dt):
        distance_from_center = sqrt(self.player.position.x ** 2 + self.player.position.z ** 2)

        if distance_from_center > self.world_boundary:
            self.show_boundary_warning = True

            distance_out = distance_from_center - self.world_boundary
            damage_per_second = BOUNDARY_DAMAGE_START + (distance_out * BOUNDARY_DAMAGE_SCALING)
            damage_to_apply = damage_per_second * dt

            self.player.take_damage(damage_to_apply, on_death=self.player_death_callback)
        else:
            self.show_boundary_warning = False

    def update_playing(self):
        if is_key_pressed(KEY_ESCAPE) or is_key_pressed(KEY_P):
            self.game_state = GameState.PAUSED
            enable_cursor()
            return

        dt = get_frame_time()
        mouse_delta = get_mouse_delta()

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

        spatial_grid = self.building_manager.get_spatial_grid()
        self.bullet_manager.update(dt, spatial_grid)
        self.vfx_manager.update(dt)

        score_gain, enemies_killed, defeated_info = self.enemy_manager.update(dt, self.player.position, spatial_grid, self.bullet_manager, self.audio_manager)
        self.score += score_gain
        self.enemies_defeated += enemies_killed

        for info in defeated_info:
            self.audio_manager.play_sound_3d('enemy_explosions', info['position'], info['velocity'])

        self.check_player_bullet_collisions()
        self.check_collisions()
        self.check_player_bounds(dt)

        altitude_warning_active = self.player.position.y <= ALTITUDE_WARNING_Y and not self.player.is_invulnerable and not self.player.is_dying
        self.show_altitude_warning = altitude_warning_active

        # Pasar las advertencias al AudioManager para gestionar el sonido
        self.audio_manager.manage_warning_sound(self.game_state, self.show_altitude_warning, self.show_boundary_warning)

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

    def draw_playing_scene(self):
        begin_mode_3d(self.camera)
        self.skybox.draw()
        self.wall_cube.draw()
        self.fog.draw()
        self.player.draw()
        self.building_manager.draw(camera=self.camera)
        self.bullet_manager.draw(camera=self.camera)
        self.vfx_manager.draw(self.camera)
        self.enemy_manager.draw()
        end_mode_3d()
        self.draw_game_hud()

    def draw_game_hud(self):
        sw, sh = get_screen_width(), get_screen_height()
        draw_text_ex(self.font, f"FPS: {get_fps()}", Vector2(10, 10), 20, 1, Color(50, 255, 150, 255))

        enemy_count = self.enemy_manager.get_enemy_count()
        draw_text_ex(self.font, f"ENEMIES: {enemy_count}", Vector2(sw - 150, 10), 20, 1, Color(255, 100, 100, 255))

        radar_mode = "ENHANCED" if self.player.radar_enhanced_mode else "STANDARD"
        draw_text_ex(self.font, f"RADAR: {radar_mode}", Vector2(sw - 150, 35), 16, 1, Color(0, 255, 100, 255))

        weapon_heat_ratio = self.weapon_heat / self.max_weapon_heat if self.max_weapon_heat > 0 else 0
        self.player.draw_hud(
            self.camera_pitch,
            self.camera_yaw,
            self.show_altitude_warning or self.show_boundary_warning,
            font=self.font,
            weapon_heat_ratio=weapon_heat_ratio,
            is_overheated=self.is_overheated,
            enemies=self.enemy_manager.get_enemies(),
            lives=self.player_lives,
            score=self.score
        )

        if self.show_altitude_warning:
            alpha = int(abs(sin(get_time() * 10)) * 255)
            warning_color = Color(255, 50, 50, alpha)
            text = "WARNING: PULL UP!"
            text_width = measure_text_ex(self.font, text, FONT_SIZE, 1).x
            text_pos_x = (sw - text_width) // 2
            text_pos_y = sh - FONT_SIZE - FONT_PADDING
            draw_text_ex(self.font, text, Vector2(text_pos_x, text_pos_y), FONT_SIZE, 1, warning_color)

        if self.show_boundary_warning:
            alpha = int(abs(sin(get_time() * 5)) * 255)
            warning_color = Color(255, 165, 0, alpha)
            text = "RETURN TO BATTLEFIELD!"
            text_width = measure_text_ex(self.font, text, 40, 1).x
            text_pos_x = (sw - text_width) // 2
            text_pos_y = sh - FONT_SIZE - FONT_PADDING - 60
            draw_text_ex(self.font, text, Vector2(text_pos_x, text_pos_y), 40, 1, warning_color)

        if self.show_overheat_message:
            alpha = int(abs(sin(get_time() * 10)) * 255)
            warning_color = Color(255, 255, 0, alpha)
            text = "OVERHEATED!!!"
            text_width = measure_text_ex(self.font, text, 30, 1).x
            draw_text_ex(self.font, text, Vector2((sw - text_width) // 2, sh // 2 + 120), 30, 1, warning_color)

    def cleanup(self):
        for model in self.models.values():
            if model:
                unload_model(model)
        self.audio_manager.cleanup()
        self.skybox.deinit()
        unload_font(self.font)

    def run(self):
        while not self.should_close:
            self.update()
            self.draw()

        self.cleanup()
        close_audio_device()
        close_window()

    def update(self):
        if window_should_close():
            self.should_close = True
            return

        self.audio_manager.manage_music_streams(self.game_state)
        self.audio_manager.manage_warning_sound(self.game_state, self.show_altitude_warning, self.show_boundary_warning)

        state_handlers = {
            GameState.MAIN_MENU: self.update_main_menu,
            GameState.SETTINGS: self.update_settings,
            GameState.GRAPHICS_SETTINGS: self.update_graphics_settings,
            GameState.CONTROLS_INFO: self.update_controls_info,
            GameState.CREDITS_SCREEN: self.update_credits_screen,
            GameState.PLAYING: self.update_playing,
            GameState.PAUSED: self.update_pause_menu,
            GameState.GAME_OVER: self.update_game_over,
        }
        handler = state_handlers.get(self.game_state)
        if handler:
            handler()

    def draw(self):
        begin_drawing()
        clear_background(BLACK)

        draw_handlers = {
            GameState.MAIN_MENU: self.draw_main_menu_screen,
            GameState.SETTINGS: self.draw_settings_screen,
            GameState.GRAPHICS_SETTINGS: self.draw_graphics_screen,
            GameState.CONTROLS_INFO: self.draw_controls_screen,
            GameState.CREDITS_SCREEN: self.draw_credits_screen,
            GameState.PLAYING: self.draw_playing_scene,
            GameState.PAUSED: self.draw_pause_screen,
            GameState.GAME_OVER: self.draw_game_over_screen,
        }
        handler = draw_handlers.get(self.game_state)
        if handler:
            handler()

        end_drawing()

    def draw_main_menu_screen(self):
        self.ui_manager.draw_main_menu(self.skybox, self.menu_camera, self.highscore_manager.high_score,
                                     self.current_splash,
                                     {"start": self.button_rects["start"], "settings": self.button_rects["settings"],
                                      "quit": self.button_rects["quit"]},
                                     self.hover_states)

    def draw_settings_screen(self):
        self.ui_manager.draw_settings_menu(self.skybox, self.menu_camera,
                                         {"graphics": self.button_rects["graphics"],
                                          "controls": self.button_rects["controls"],
                                          "credits": self.button_rects["credits"], "back": self.button_rects["back"]},
                                         self.hover_states)

    def draw_graphics_screen(self):
        self.ui_manager.draw_graphics_menu(self.skybox, self.menu_camera, self.settings, self.resolutions,
                                         self.button_rects, self.hover_states)

    def draw_controls_screen(self):
        self.ui_manager.draw_controls_screen(self.skybox, self.menu_camera, {"back": self.button_rects["back"]},
                                           self.hover_states)

    def draw_credits_screen(self):
        self.ui_manager.draw_credits_screen(self.skybox, self.menu_camera, self.credits,
                                          {"back": self.button_rects["back"]}, self.hover_states,
                                          self.link_hover_states)

    def draw_pause_screen(self):
        self.draw_playing_scene()
        self.ui_manager.draw_pause_menu({"resume": self.button_rects["resume"], "main_menu": self.button_rects["main_menu"],
                                       "quit": self.button_rects["pause_quit"]}, self.hover_states)

    def draw_game_over_screen(self):
        self.draw_playing_scene()
        self.ui_manager.draw_game_over(self.score, self.highscore_manager.high_score, self.enemies_defeated,
                                     {"restart": self.button_rects["restart"],
                                      "main_menu": self.button_rects["go_main_menu"]}, self.hover_states)

    def update_main_menu(self):
        self.menu_camera_angle += get_frame_time() * 0.1
        self.menu_camera.position = Vector3(cos(self.menu_camera_angle) * 10, 2.0, sin(self.menu_camera_angle) * 10)
        self.menu_camera.target = Vector3(0, 2, 0)

        mouse_pos = get_mouse_position()
        for key in ["start", "settings", "quit"]:
            self.hover_states[key] = check_collision_point_rec(mouse_pos, self.button_rects[key])

        if is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
            if self.hover_states["start"]:
                self.reset_game()
                self.game_state = GameState.PLAYING
                disable_cursor()
            elif self.hover_states["settings"]:
                self.game_state = GameState.SETTINGS
            elif self.hover_states["quit"]:
                self.should_close = True

    def update_settings(self):
        mouse_pos = get_mouse_position()
        for key in ["graphics", "controls", "credits", "back"]:
            self.hover_states[key] = check_collision_point_rec(mouse_pos, self.button_rects[key])

        if is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
            if self.hover_states["graphics"]:
                self.game_state = GameState.GRAPHICS_SETTINGS
            elif self.hover_states["controls"]:
                self.game_state = GameState.CONTROLS_INFO
            elif self.hover_states["credits"]:
                self.game_state = GameState.CREDITS_SCREEN
                self.link_rects = [Rectangle(180, 250 + 65 + i * 120, measure_text(c['link'], 25), 25) for i, c in
                                   enumerate(self.credits) if c['link']]
            elif self.hover_states["back"]:
                self.game_state = GameState.MAIN_MENU

    def update_graphics_settings(self):
        mouse_pos = get_mouse_position()
        for key in ["resolution", "fullscreen", "mute", "vol_down", "vol_up", "back"]:
            self.hover_states[key] = check_collision_point_rec(mouse_pos, self.button_rects[key])

        if is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
            if self.hover_states["resolution"]:
                self.settings['resolution_index'] = (self.settings['resolution_index'] + 1) % len(self.resolutions)
                self.apply_graphics_settings()
            elif self.hover_states["fullscreen"]:
                self.settings['fullscreen'] = not self.settings['fullscreen']
                self.apply_graphics_settings()
            elif self.hover_states["mute"]:
                self.settings['muted'] = not self.settings['muted']
                self.apply_audio_settings()
            elif self.hover_states["vol_down"]:
                self.settings['master_volume'] = max(0.0, self.settings['master_volume'] - 0.1)
                self.apply_audio_settings()
            elif self.hover_states["vol_up"]:
                self.settings['master_volume'] = min(1.0, self.settings['master_volume'] + 0.1)
                self.apply_audio_settings()
            elif self.hover_states["back"]:
                self.game_state = GameState.SETTINGS

    def apply_graphics_settings(self):
        res = self.resolutions[self.settings['resolution_index']]
        if self.settings['fullscreen'] and not is_window_fullscreen():
            set_window_size(get_monitor_width(0), get_monitor_height(0))
            toggle_fullscreen()
        elif not self.settings['fullscreen']:
            if is_window_fullscreen():
                toggle_fullscreen()
            set_window_size(res[0], res[1])
        self.setup_ui_elements()

    def apply_audio_settings(self):
        self.audio_manager.apply_settings()

    def update_controls_info(self):
        mouse_pos = get_mouse_position()
        self.hover_states["back"] = check_collision_point_rec(mouse_pos, self.button_rects["back"])
        if is_mouse_button_pressed(MOUSE_BUTTON_LEFT) and self.hover_states["back"]:
            self.game_state = GameState.SETTINGS

    def update_credits_screen(self):
        mouse_pos = get_mouse_position()
        self.hover_states["back"] = check_collision_point_rec(mouse_pos, self.button_rects["back"])
        self.link_hover_states = [check_collision_point_rec(mouse_pos, rect) for rect in self.link_rects]

        if is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
            if self.hover_states["back"]:
                self.game_state = GameState.SETTINGS
            else:
                for i, rect in enumerate(self.link_rects):
                    if check_collision_point_rec(mouse_pos, rect):
                        credit_index = [idx for idx, c in enumerate(self.credits) if c['link']][i]
                        open_url(self.credits[credit_index]['link'])
                        break

    def update_pause_menu(self):
        if is_key_pressed(KEY_ESCAPE) or is_key_pressed(KEY_P):
            self.game_state = GameState.PLAYING
            disable_cursor()
            return

        mouse_pos = get_mouse_position()
        self.hover_states["resume"] = check_collision_point_rec(mouse_pos, self.button_rects["resume"])
        self.hover_states["main_menu"] = check_collision_point_rec(mouse_pos, self.button_rects["main_menu"])
        self.hover_states["pause_quit"] = check_collision_point_rec(mouse_pos, self.button_rects["pause_quit"])

        if is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
            if self.hover_states["resume"]:
                self.game_state = GameState.PLAYING
                disable_cursor()
            elif self.hover_states["main_menu"]:
                self.game_state = GameState.MAIN_MENU
            elif self.hover_states["pause_quit"]:
                self.should_close = True

    def update_game_over(self):
        mouse_pos = get_mouse_position()
        self.hover_states["restart"] = check_collision_point_rec(mouse_pos, self.button_rects["restart"])
        self.hover_states["go_main_menu"] = check_collision_point_rec(mouse_pos, self.button_rects["go_main_menu"])

        if is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
            if self.hover_states["restart"]:
                self.reset_game()
                self.game_state = GameState.PLAYING
                disable_cursor()
            elif self.hover_states["go_main_menu"]:
                self.game_state = GameState.MAIN_MENU


if __name__ == '__main__':
    game = Game()
    game.run()