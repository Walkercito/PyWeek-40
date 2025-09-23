from settings import * 


class Game:
    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, "Skycraper")
        init_audio_device()
        self.import_assets()

        self.camera = Camera3D()
        self.camera.position = Vector3(-4.0, 8.0, 6.0) 
        self.camera.target = Vector3(0.0, 0.0, -1.0) 
        self.camera.up = Vector3(0.0, 1.0, 0.0) 
        self.camera.fovy = 45.0 
        self.camera.projection = CAMERA_PERSPECTIVE 


    def import_assets(self):
        self.models = {}
        self.audio = {}
    

    def update(self):
        dt = get_frame_time()


    def draw(self):
        clear_background(WHITE)
        begin_drawing()
        begin_mode_3d(self.camera)

        end_mode_3d()
        end_drawing()


    def run(self):
        while not window_should_close():
            self.update()
            self.draw() 
        close_audio_device()
        close_window()



if __name__ == '__main__':
    game = Game()
    game.run()