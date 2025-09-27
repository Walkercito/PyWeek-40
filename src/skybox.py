from settings import *


class Skybox:
    def __init__(self, initial_exposure=0.7):
        cube = gen_mesh_cube(1.0, 1.0, 1.0)
        self.skybox = load_model_from_mesh(cube)

        self.exposure = initial_exposure
        vertex_shader_path = join("shaders", "skybox", "skybox.vs")
        fragment_shader_path = join("shaders", "skybox", "skybox.fs")

        try:
            self.skybox.materials[0].shader = load_shader(vertex_shader_path, fragment_shader_path)
            print("[*] Skybox shaders loaded successfully")
        except:
            print("Warning: Could not load skybox shaders, using default")
            self.skybox.materials[0].shader = get_shader_default()
            return

        self.environment_map_loc = get_shader_location(self.skybox.materials[0].shader, "environmentMap")
        self.do_gamma_loc = get_shader_location(self.skybox.materials[0].shader, "doGamma")
        self.vflipped_loc = get_shader_location(self.skybox.materials[0].shader, "vflipped")
        self.exposure_loc = get_shader_location(self.skybox.materials[0].shader, "exposure")

        cubemap_value = ffi.new('int *', MATERIAL_MAP_CUBEMAP)
        gamma_value = ffi.new('int *', 0)
        vflipped_value = ffi.new('int *', 0)

        set_shader_value(self.skybox.materials[0].shader, self.environment_map_loc,
                         cubemap_value, SHADER_UNIFORM_INT)
        set_shader_value(self.skybox.materials[0].shader, self.do_gamma_loc,
                         gamma_value, SHADER_UNIFORM_INT)
        set_shader_value(self.skybox.materials[0].shader, self.vflipped_loc,
                         vflipped_value, SHADER_UNIFORM_INT)
        self.set_exposure(self.exposure)

        self.textures = {}
        game_png_path = join("assets", "skybox.png")
        menu_png_path = join("assets", "stylized_skybox.png")

        try:
            img_game = load_image(game_png_path)
            if not (img_game.width > 0 and img_game.height > 0): raise ValueError("Game skybox image empty")
            print("[*] Loaded game PNG skybox successfully")
            self.textures['game'] = load_texture_cubemap(img_game, CUBEMAP_LAYOUT_AUTO_DETECT)
            unload_image(img_game)
        except Exception as e:
            print(f"[*] Warning: Game skybox not found or failed ({e}), using generated gradient.")
            img_generated = gen_image_gradient_radial(512, 512, 0.0, SKYBLUE, DARKBLUE)
            self.textures['game'] = load_texture_cubemap(img_generated, CUBEMAP_LAYOUT_AUTO_DETECT)
            unload_image(img_generated)

        try:
            img_menu = load_image(menu_png_path)
            if not (img_menu.width > 0 and img_menu.height > 0): raise ValueError("Menu skybox image empty")
            print("[*] Loaded menu (stylized) PNG skybox successfully")
            self.textures['menu'] = load_texture_cubemap(img_menu, CUBEMAP_LAYOUT_AUTO_DETECT)
            unload_image(img_menu)
        except Exception as e:
            print(f"[*] Warning: Stylized skybox not found or failed ({e}), using generated gradient.")
            img_generated = gen_image_gradient_radial(512, 512, 0.0, Color(20, 40, 80, 255), Color(100, 120, 180, 255))
            self.textures['menu'] = load_texture_cubemap(img_generated, CUBEMAP_LAYOUT_AUTO_DETECT)
            unload_image(img_generated)

        self.set_active_texture('menu')


    def set_active_texture(self, key):
        """
        Establece la textura del skybox activa.
        Acepta 'game' o 'menu' como claves.
        """
        if key in self.textures:
            self.skybox.materials[0].maps[MATERIAL_MAP_CUBEMAP].texture = self.textures[key]
            print(f"[*] Skybox texture switched to '{key}'.")
        else:
            print(f"[WARNING] Skybox texture key '{key}' not found.")


    def set_exposure(self, exposure):
        self.exposure = max(0.0, exposure)
        exposure_value = ffi.new('float *', self.exposure)
        set_shader_value(self.skybox.materials[0].shader, self.exposure_loc,
                         exposure_value, SHADER_UNIFORM_FLOAT)


    def adjust_exposure(self, delta):
        self.set_exposure(self.exposure + delta)


    def get_exposure(self):
        return self.exposure


    def draw(self):
        rl_disable_backface_culling()
        rl_disable_depth_mask()
        draw_model(self.skybox, Vector3(0, 0, 0), 1.0, WHITE)
        rl_enable_depth_mask()
        rl_enable_backface_culling()


    def deinit(self):
        for texture in self.textures.values():
            unload_texture(texture)
        unload_shader(self.skybox.materials[0].shader)
        unload_model(self.skybox)