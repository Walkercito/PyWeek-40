from settings import * 
from player import Player
from models import Fog


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

        self.color_phase = 0.0
        self.current_color_index = 0
        self.last_color_change = -1
        self.base_colors = [
            Vector3(0.6, 0.8, 1.0),    # classic blue
            Vector3(0.5, 0.7, 0.9),    # dark blue
            Vector3(0.7, 0.8, 1.0),    # light blue
            Vector3(0.4, 0.6, 0.8),    # gray blue
        ]

        self.fog = Fog(self.camera, size=200, segments=50)
        self.fog.set_fog_parameters(
            density=0.7,
            speed=0.2,
            scale=6.0,
            height=8.0,
            color=Vector3(0.6, 0.8, 1.0)
        )

        self.player = Player(self.models["player"], self.shoot)


    def import_assets(self):
        self.models = {
            "player": load_model(join("assets", "models", "player", "plane01.glb"))
        }
        self.audio = {}
    

    def shoot(self, position):
        print("Shoot!")


    def update_camera(self):
        mouse_delta = get_mouse_delta()
        
        self.camera_yaw -= mouse_delta.x * MOUSE_SENSITIVITY
        self.camera_pitch -= mouse_delta.y * MOUSE_SENSITIVITY

        if self.camera_pitch > 1.5: self.camera_pitch = 1.5
        elif self.camera_pitch < -1.5: self.camera_pitch = -1.5
        
        cam_x = self.player.position.x + (self.camera_distance * cos(self.camera_pitch) * sin(self.camera_yaw))
        cam_y = self.player.position.y + (self.camera_distance * sin(self.camera_pitch))
        cam_z = self.player.position.z + (self.camera_distance * cos(self.camera_pitch) * cos(self.camera_yaw))
        
        self.camera.position = Vector3(cam_x, cam_y, cam_z)
        self.camera.target = vector3_add(self.player.position, self.camera_target_offset)


    def cycle_fog_color(self):
        self.current_color_index = (self.current_color_index + 1) % len(self.base_colors)


    def update(self):
        dt = get_frame_time()

        player_forward_x = -sin(self.camera_yaw) * cos(self.camera_pitch)
        player_forward_y = -sin(self.camera_pitch)
        player_forward_z = -cos(self.camera_yaw) * cos(self.camera_pitch)
        player_forward_vector = vector3_normalize(Vector3(player_forward_x, player_forward_y, player_forward_z))

        self.player.update(dt, player_forward_vector)
        self.update_camera()

        self.color_phase += dt * 0.3
        
        current_color = self.base_colors[self.current_color_index]
        next_color_index = (self.current_color_index + 1) % len(self.base_colors)
        next_color = self.base_colors[next_color_index]
        
        blend_factor = (sin(self.color_phase) + 1.0) * 0.5
        dynamic_color = Vector3(
            current_color.x * (1.0 - blend_factor) + next_color.x * blend_factor,
            current_color.y * (1.0 - blend_factor) + next_color.y * blend_factor,
            current_color.z * (1.0 - blend_factor) + next_color.z * blend_factor
        )
        
        pulse_factor = 1.0 + 0.1 * sin(get_time() * 2.0)
        dynamic_density = 0.7 * pulse_factor
        
        self.fog.set_fog_parameters(
            color=dynamic_color,
            density=min(1.0, dynamic_density)
        )
        
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

        end_mode_3d()
        self.draw_ui()
        end_drawing()
        

    def draw_ui(self):
        draw_text(f"FPS: {get_fps()}", 10, 10, 20, WHITE)
        self.player.draw_hud(self.camera_pitch)


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