from settings import * 

from models_dev import Floor
from player import Player

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

        self.floor = Floor(self.dark_texture)
        self.player = Player(self.models["player"], self.shoot)

    
    def shoot(self, position):
        print("Shoot!")


    def import_assets(self):
        self.models = {
            "player": load_model(join("assets", "models", "player", "plane01.glb"))
        }
        self.audio = {}

        self.dark_texture = load_texture(join("assets", "textures", "Dark", "texture_08.png"))


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


    def update(self):
        dt = get_frame_time() 

        player_forward_x = -sin(self.camera_yaw) * cos(self.camera_pitch)
        player_forward_y = -sin(self.camera_pitch)
        player_forward_z = -cos(self.camera_yaw) * cos(self.camera_pitch)
        player_forward_vector = vector3_normalize(Vector3(player_forward_x, player_forward_y, player_forward_z))
        
        self.player.update(dt, player_forward_vector) 
        self.update_camera()


    def draw(self):
        begin_drawing()
        clear_background(BLACK)
        begin_mode_3d(self.camera)

        self.floor.draw()
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