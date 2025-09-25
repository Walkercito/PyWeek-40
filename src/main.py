from settings import * 

from player import Player
from models import Fog
from models import Skycraper


class Game:
    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, "Skycraper")
        init_audio_device()
        set_target_fps(FPS)
        disable_cursor()
        
        self.import_assets()

        self.camera = Camera3D()
        self.camera.up = Vector3(0.0, 1.0, 0.0) 
        self.camera.fovy = 45.0 
        self.camera.projection = CAMERA_PERSPECTIVE

        self.camera_yaw = 0.0 
        self.camera_pitch = 0.2
        self.camera_distance = 15.0 
        self.camera_target_offset = Vector3(0, 3.0, 0) 
        self.camera_smooth_factor = 5.0

        self.show_altitude_warning = False
        self.altitude_warning_active = False
        self.is_fading_out_sound = False
        self.warning_sound_volume = 1.0
        self.FADE_OUT_SPEED = 2.0

        self.is_in_emergency_ascent = False
        self.EMERGENCY_ASCENT_TARGET_Y = 15.0
        self.EMERGENCY_ASCENT_SPEED = 2.0
        self.warning_sound_timer = Timer(2.5) 
        self.camera_shake_timer = Timer(0.3)
        self.camera_shake_intensity = 0.8

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

        self.player = Player(self.models["player"], self.shoot)
        self.camera.position = Vector3(self.player.position.x, self.player.position.y + 10, self.player.position.z + self.camera_distance)
        self.camera.target = vector3_add(self.player.position, self.camera_target_offset)

        self.skycraper = Skycraper(self.models["skycraper01"], Vector3(0, -10, 10))


    def import_assets(self):
        self.models = {
            "player": load_model(join("assets", "models", "player", "plane01.glb")),
            "skycraper01": load_model(join("assets", "models", "buildings", "1.glb")),
            "skycraper02": load_model(join("assets", "models", "buildings", "2.glb"))
        }
        self.audio = {
            "warning": load_sound(join("assets", "audio", "beep-warning.mp3"))
        }
    

    def shoot(self, position):
        print("Shoot!")


    def cycle_fog_color(self):
        self.current_color_index = (self.current_color_index + 1) % len(self.base_colors)


    def update(self):
        dt = get_frame_time()
        mouse_delta = get_mouse_delta()

        self.warning_sound_timer.update()
        self.camera_shake_timer.update()

        if self.is_in_emergency_ascent:
            target_pos = Vector3(self.player.position.x, self.EMERGENCY_ASCENT_TARGET_Y, self.player.position.z)
            self.player.position = vector3_lerp(self.player.position, target_pos, self.EMERGENCY_ASCENT_SPEED * dt)
            
            if self.player.position.y >= self.EMERGENCY_ASCENT_TARGET_Y - 0.1:
                self.is_in_emergency_ascent = False
                self.altitude_warning_active = False
        else:
            self.camera_yaw -= mouse_delta.x * MOUSE_SENSITIVITY
            self.camera_pitch -= mouse_delta.y * MOUSE_SENSITIVITY
            self.camera_pitch = min(max(self.camera_pitch, -1.5), 1.5)

            player_forward_x = -sin(self.camera_yaw) * cos(self.camera_pitch)
            player_forward_y = -sin(self.camera_pitch)
            player_forward_z = -cos(self.camera_yaw) * cos(self.camera_pitch)
            player_forward_vector = vector3_normalize(Vector3(player_forward_x, player_forward_y, player_forward_z))

            self.player.update(dt, player_forward_vector, mouse_delta.x)

            self.altitude_warning_active = self.player.position.y <= 10.0

            if self.player.position.y <= 3.0:
                self.is_in_emergency_ascent = True
                self.camera_shake_timer.activate()
                self.player.velocity = Vector3(0, 0, 0)

        self.show_altitude_warning = self.altitude_warning_active or self.is_in_emergency_ascent
        
        if self.altitude_warning_active:
            self.is_fading_out_sound = False 
            set_sound_volume(self.audio["warning"], 1.0)
            self.warning_sound_volume = 1.0

            if not self.warning_sound_timer:
                play_sound(self.audio["warning"])
                self.warning_sound_timer.activate()
        else:
            if is_sound_playing(self.audio["warning"]) and not self.is_fading_out_sound:
                self.is_fading_out_sound = True

        # sound fade out
        if self.is_fading_out_sound:
            self.warning_sound_volume -= self.FADE_OUT_SPEED * dt
            if self.warning_sound_volume <= 0:
                self.warning_sound_volume = 0
                stop_sound(self.audio["warning"])
                self.is_fading_out_sound = False
            
            set_sound_volume(self.audio["warning"], self.warning_sound_volume)

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


    def draw(self):
        begin_drawing()
        clear_background(BLACK)
        begin_mode_3d(self.camera)

        self.fog.draw()
        self.player.draw()
        self.skycraper.draw()

        end_mode_3d()
        self.draw_ui()
        end_drawing()


    def draw_ui(self):
        draw_text(f"FPS: {get_fps()}", 10, 10, 20, WHITE)
        self.player.draw_hud(self.camera_pitch)

        if self.show_altitude_warning:
            alpha = int(abs(sin(get_time() * 10)) * 255)
            warning_color = Color(255, 50, 50, alpha)
            
            text = "WARNING: PULL UP!"
            text_width = measure_text(text, FONT_SIZE)
            text_pos_x = (SCREEN_WIDTH - text_width) // 2
            text_pos_y = (SCREEN_HEIGHT - FONT_SIZE) // 2

            draw_text(text, text_pos_x, text_pos_y, FONT_SIZE, warning_color)


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