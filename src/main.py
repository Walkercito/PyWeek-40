from math import sin

from settings import * 
from player import Player
from models import Fog


class Game:
    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, "Skycraper")
        init_audio_device()
        set_target_fps(FPS)
        
        self.import_assets()

        self.camera = Camera3D()
        self.camera.position = Vector3(0.0, 20.0, 20.0)
        self.camera.target = Vector3(0.0, 0.0, 0.0)
        self.camera.up = Vector3(0.0, 1.0, 0.0) 
        self.camera.fovy = 45.0 
        self.camera.projection = CAMERA_PERSPECTIVE 
        
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


    def cycle_fog_color(self):
        self.current_color_index = (self.current_color_index + 1) % len(self.base_colors)


    def update(self):
        dt = get_frame_time()
        self.player.update(dt)
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


    def cleanup(self):
        for model in self.models.values():
            unload_model(model)
        for sound in self.audio.values():
            unload_sound(sound)


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