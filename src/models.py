from settings import *


class Model:
    def __init__(self, model, speed, position, direction = Vector3()):
        self.model = model
        self.speed = speed
        self.position = position
        self.direction = direction
        self.size = 1
        
        # collision system
        self.collision_box = BoundingBox(
            Vector3(-1, -1, -1),  # min
            Vector3(1, 1, 1)      # max
        )
        self.has_collision = True  # for simple models
        self.has_multiple_collision_boxes = False  # for complex models

    def get_world_bounding_box(self):
        if not self.has_collision:
            return None
            
        min_point = Vector3(
            self.position.x + (self.collision_box.min.x * self.size),
            self.position.y + (self.collision_box.min.y * self.size),
            self.position.z + (self.collision_box.min.z * self.size)
        )
        max_point = Vector3(
            self.position.x + (self.collision_box.max.x * self.size),
            self.position.y + (self.collision_box.max.y * self.size),
            self.position.z + (self.collision_box.max.z * self.size)
        )
        
        return BoundingBox(min_point, max_point)

    def check_collision_with(self, other_model):
        if not self.has_collision or not other_model.has_collision:
            return False
        
        if hasattr(other_model, 'has_multiple_collision_boxes') and other_model.has_multiple_collision_boxes:
            other_boxes = other_model.get_world_bounding_boxes()
            my_box = self.get_world_bounding_box()
            
            if my_box is None:
                return False
                
            for other_box in other_boxes:
                if check_collision_boxes(my_box, other_box):
                    return True
        else:
            my_box = self.get_world_bounding_box()
            other_box = other_model.get_world_bounding_box()
            
            if my_box is None or other_box is None:
                return False
                
            return check_collision_boxes(my_box, other_box)
        
        return False

    def move(self, dt):
        self.position.x += self.speed * self.direction.x * dt
        self.position.y += self.speed * self.direction.y * dt
        self.position.z += self.speed * self.direction.z * dt

    def update(self, dt):
        self.move(dt)
    
    def draw(self):
        draw_model(self.model, self.position, self.size, WHITE)


class Skycraper(Model):
    def __init__(self, model, position):
        super().__init__(model, 0, position, Vector3())
        self.collision_box = BoundingBox(
            Vector3(-2, -5, -2),   # min
            Vector3(2, 15, 2)      # max
        )


class SkycraperMultipleLayer(Model):
    """SkycraperMultipleLayer with exact dimensions from the model
    
    Original measurements from Blender:
    - base: X 30.2m, Y 30.2m, Z 67.6m
    - second floor: X 21.14m, Y 21.14m, Z 26.4m  
    - antenna: X 2.8359m, Y 2.81107m, Z 34.9m
    """
    def __init__(self, model, position):
        super().__init__(model, 0, position, Vector3())
        
        # blender: X=width, Y=depth, Z=height
        # raylib: X=width, Y=height, Z=depth
        
        self.collision_boxes = [
            # base: 30.2m x 30.2m x 67.6m 
            BoundingBox(
                Vector3(-15.1, -5, -15.1),
                Vector3(15.1, 67.6, 15.1)  
            ),
            
            # second floor: 21.14m x 21.14m x 26.4m 
            # starts where first floor ends (Y=67.6)
            BoundingBox(
                Vector3(-10.57, 67.6, -10.57), 
                Vector3(10.57, 94.0, 10.57)
            ),
            
            # antenna: 2.84m x 2.81m x 34.9m
            # starts where second floor ends (Y=94.0)
            BoundingBox(
                Vector3(-1.42, 94.0, -1.41), 
                Vector3(1.42, 128.9, 1.41) 
            )
        ]
        
        self.has_multiple_collision_boxes = True
    

    def get_world_bounding_boxes(self):
        if not self.has_collision:
            return []
            
        world_boxes = []
        for box in self.collision_boxes:
            min_point = Vector3(
                self.position.x + (box.min.x * self.size),
                self.position.y + (box.min.y * self.size),
                self.position.z + (box.min.z * self.size)
            )
            max_point = Vector3(
                self.position.x + (box.max.x * self.size),
                self.position.y + (box.max.y * self.size),
                self.position.z + (box.max.z * self.size)
            )
            world_boxes.append(BoundingBox(min_point, max_point))
        
        return world_boxes
    

    def check_collision_with(self, other_model):
        if not self.has_collision or not other_model.has_collision:
            return False

        # complex model
        if hasattr(other_model, 'get_world_bounding_boxes'):
            other_boxes = other_model.get_world_bounding_boxes()
            my_boxes = self.get_world_bounding_boxes()
            
            for my_box in my_boxes:
                for other_box in other_boxes:
                    if check_collision_boxes(my_box, other_box):
                        return True
        else:
            # simple model
            other_box = other_model.get_world_bounding_box()
            if other_box is None:
                return False
                
            my_boxes = self.get_world_bounding_boxes()
            for my_box in my_boxes:
                if check_collision_boxes(my_box, other_box):
                    return True
        
        return False


class Fog(Model):
    def __init__(self, camera, size=50, segments=50):
        mesh = gen_mesh_plane(size, size, segments, segments)
        model = load_model_from_mesh(mesh)

        vs_path = join("shaders", "fog", "fog.vs")
        fs_path = join("shaders", "fog", "fog.fs")
        
        if not exists(vs_path) or not exists(fs_path):
            print(f"Warning: Shader files not found:")
            print(f"  Vertex shader: {vs_path} - {'[*]' if exists(vs_path) else '[✗]'}")
            print(f"  Fragment shader: {fs_path} - {'[*]' if exists(fs_path) else '[✗]'}")
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

        self.has_collision = False

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