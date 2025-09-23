from settings import * 

from models_dev import Floor
from player import Player

class Game:
    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, "Skycraper")
        init_audio_device()
        set_target_fps(FPS)
        
        self.import_assets()

        self.camera = Camera3D()
        self.camera.position = Vector3(0.0, 10.0, 10.0)
        self.camera.target = Vector3(0.0, 0.0, 0.0)
        self.camera.up = Vector3(0.0, 1.0, 0.0) 
        self.camera.fovy = 45.0 
        self.camera.projection = CAMERA_PERSPECTIVE

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


    def update(self):
        dt = get_frame_time() 
        self.player.update(dt) 


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