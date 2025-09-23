from settings import *



class Model:
    def __init__(self, model, speed, position, direction = Vector3()):
        self.model = model
        self.speed = speed
        self.position = position
        self.direction = direction
        self.size = 1

    def move(self, dt):
        self.position.x += self.speed * self.direction.x * dt
        self.position.y += self.speed * self.direction.y * dt
        self.position.z += self.speed * self.direction.z * dt

    def update(self, dt):
        self.move(dt)
    
    def draw(self):
        draw_model(self.model, self.position, self.size, WHITE)


class Fog(Model):
    def __init__(self, camera, size=50, segments=50):
        mesh = gen_mesh_plane(size, size, segments, segments)
        model = load_model_from_mesh(mesh)

        vs_path = join("shaders", "fog", "fog.vs")
        fs_path = join("shaders", "fog", "fog.fs")
        
        if not os.path.exists(vs_path) or not os.path.exists(fs_path):
            print(f"Warning: Shader files not found:")
            print(f"  Vertex shader: {vs_path} - {'[*]' if os.path.exists(vs_path) else '[✗]'}")
            print(f"  Fragment shader: {fs_path} - {'[*]' if os.path.exists(fs_path) else '[✗]'}")
            print("Using basic rendering...")
            self.shader_loaded = False
            self.shader = None
        else:
            try:
                self.shader = load_shader(vs_path, fs_path)
                self.shader_loaded = True
                print("[*] Shaders loaded successfully")
                
                # get uniforms locations
                self.time_loc = get_shader_location(self.shader, "time")
                self.view_pos_loc = get_shader_location(self.shader, "viewPos")
                self.fog_density_loc = get_shader_location(self.shader, "fogDensity")
                self.fog_speed_loc = get_shader_location(self.shader, "fogSpeed")
                self.fog_scale_loc = get_shader_location(self.shader, "fogScale")
                self.fog_height_loc = get_shader_location(self.shader, "fogHeight")
                self.fog_color_loc = get_shader_location(self.shader, "fogColor")
                
            except Exception as e:
                print(f"[x] Error loading shaders: {e}")
                self.shader_loaded = False
                self.shader = None
        
        # fog parameters
        self.fog_density = 0.8
        self.fog_speed = 0.5
        self.fog_scale = 4.0
        self.fog_height = 2.0
        self.fog_color = Vector3(0.9, 0.95, 1.0)
        
        self.camera = camera

        super().__init__(model, 0, Vector3(0, 0, 0), Vector3())

        if self.shader_loaded:
            self.model.materials[0].shader = self.shader
            self._update_shader_uniforms()
    

    def _update_shader_uniforms(self):
        if not self.shader_loaded:
            return
            
        density_ptr = ffi.new('float *', self.fog_density)
        speed_ptr = ffi.new('float *', self.fog_speed) 
        scale_ptr = ffi.new('float *', self.fog_scale)
        height_ptr = ffi.new('float *', self.fog_height)
        color_ptr = ffi.new('float[3]', [self.fog_color.x, self.fog_color.y, self.fog_color.z])
        
        set_shader_value(self.shader, self.fog_density_loc, 
                        density_ptr, SHADER_UNIFORM_FLOAT)
        set_shader_value(self.shader, self.fog_speed_loc, 
                        speed_ptr, SHADER_UNIFORM_FLOAT)
        set_shader_value(self.shader, self.fog_scale_loc, 
                        scale_ptr, SHADER_UNIFORM_FLOAT)
        set_shader_value(self.shader, self.fog_height_loc, 
                        height_ptr, SHADER_UNIFORM_FLOAT)
        set_shader_value(self.shader, self.fog_color_loc, 
                        color_ptr, SHADER_UNIFORM_VEC3)
    

    def set_fog_parameters(self, density=None, speed=None, scale=None, height=None, color=None):
        if density is not None:
            self.fog_density = density
        if speed is not None:
            self.fog_speed = speed
        if scale is not None:
            self.fog_scale = scale
        if height is not None:
            self.fog_height = height
        if color is not None:
            self.fog_color = color
        
        self._update_shader_uniforms()
    
    def update(self, dt):
        super().update(dt)
        
        if not self.shader_loaded:
            return

        current_time = get_time()
        time_ptr = ffi.new('float *', current_time)
        set_shader_value(self.shader, self.time_loc, time_ptr, SHADER_UNIFORM_FLOAT)

        view_pos_ptr = ffi.new('float[3]', [self.camera.position.x, self.camera.position.y, self.camera.position.z])
        set_shader_value(self.shader, self.view_pos_loc, view_pos_ptr, SHADER_UNIFORM_VEC3)
    

    def draw(self):
        begin_blend_mode(BLEND_ALPHA)
        
        if self.shader_loaded:
            draw_model(self.model, self.position, self.size, WHITE)
        else:
            draw_model(self.model, self.position, self.size, Color(200, 220, 255, 80))
        end_blend_mode()
    

    def __del__(self):
        if hasattr(self, 'shader') and self.shader is not None:
            unload_shader(self.shader)