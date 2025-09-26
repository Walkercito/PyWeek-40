from settings import *


class Bullet:
    """Base class for projectiles"""
    def __init__(self, position, direction, bullet_type="normal"):
        # types of bullets
        bullet_configs = {
            "normal": {
                "speed": 100.0,
                "damage": 25,
                "lifetime": 3.0,
                "color": YELLOW,
                "size": 1.0
            },
            "heavy": {
                "speed": 80.0,
                "damage": 50,
                "lifetime": 2.5,
                "color": RED,
                "size": 1.5
            },
            "rapid": {
                "speed": 140.0,
                "damage": 15,
                "lifetime": 2.0,
                "color": BLUE,
                "size": 0.8
            }
        }
        
        config = bullet_configs.get(bullet_type, bullet_configs["normal"])
        
        self.position = Vector3(position.x, position.y, position.z)
        self.previous_position = Vector3(position.x, position.y, position.z)
        self.direction = Vector3(direction.x, direction.y, direction.z)
        self.speed = config["speed"]
        
        self.bullet_type = bullet_type
        self.damage = config["damage"]
        self.lifetime = config["lifetime"]
        self.max_lifetime = config["lifetime"]
        self.color = config["color"]
        self.size = config["size"]
        self.active = True
        
        self.collision_box = BoundingBox(
            Vector3(-0.1, -0.1, -0.1),
            Vector3(0.1, 0.1, 0.1)
        )

    def update(self, dt):
        if not self.active:
            return
        
        self.previous_position.x = self.position.x
        self.previous_position.y = self.position.y
        self.previous_position.z = self.position.z
            
        self.position.x += self.speed * self.direction.x * dt
        self.position.y += self.speed * self.direction.y * dt
        self.position.z += self.speed * self.direction.z * dt
        
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.active = False
            return


    def get_transform_matrix(self):
        scale_matrix = matrix_scale(self.size, self.size, self.size)
        translation_matrix = matrix_translate(self.position.x, self.position.y, self.position.z)

        return matrix_multiply(scale_matrix, translation_matrix)


    def get_world_bounding_box(self):
        min_point = Vector3(
            self.position.x + self.collision_box.min.x * self.size,
            self.position.y + self.collision_box.min.y * self.size,
            self.position.z + self.collision_box.min.z * self.size
        )
        max_point = Vector3(
            self.position.x + self.collision_box.max.x * self.size,
            self.position.y + self.collision_box.max.y * self.size,
            self.position.z + self.collision_box.max.z * self.size
        )
        return BoundingBox(min_point, max_point)

    def check_collision_with(self, other_model):
        if not self.active:
            return False
        
        my_box = self.get_world_bounding_box()
        
        if hasattr(other_model, 'has_multiple_collision_boxes') and other_model.has_multiple_collision_boxes:
            other_boxes = other_model.get_world_bounding_boxes()
            for other_box in other_boxes:
                if check_collision_boxes(my_box, other_box):
                    return True
        else:
            other_box = other_model.get_world_bounding_box()
            if other_box is None:
                return False
            return check_collision_boxes(my_box, other_box)
        
        return False


    def draw_trail(self):
        trail_color = fade(self.color, 0.6)
        draw_line_3d(self.previous_position, self.position, trail_color)



    def check_bounds(self, max_distance=1000):
        distance_from_origin = vector3_length(self.position)
        if distance_from_origin > max_distance:
            self.active = False


    def on_hit(self, target):
        if DEBUG:
            print(f"{self.bullet_type.title()} bullet hit {target.__class__.__name__} for {self.damage} damage")
        
        self.active = False
        return self.damage


class BulletManager:
    """Game's Bullet Manager with instancing"""
    def __init__(self):
        self.bullets = []
        self.max_bullets = 500

        self.bullet_mesh = gen_mesh_sphere(0.2, 8, 8)
        
        vs_path = join("shaders", "bullets", "bullet_instancing.vs")
        fs_path = join("shaders", "bullets", "bullet_instancing.fs")
        
        if not exists(vs_path) or not exists(fs_path):
            print(f"Warning: Bullet instancing shaders not found!")
            print(f"  Vertex shader: {vs_path} - {'[*]' if exists(vs_path) else '[✗]'}")
            print(f"  Fragment shader: {fs_path} - {'[*]' if exists(fs_path) else '[✗]'}")
            print("Using basic rendering...")
            self.instancing_enabled = False
            self.shader = None
        else:
            try:
                self.shader = load_shader(vs_path, fs_path)
                self.instancing_enabled = True
                print("[*] Bullet instancing shaders loaded successfully")

                self.shader.locs[SHADER_LOC_MATRIX_MVP] = get_shader_location(self.shader, "mvp")
                self.shader.locs[SHADER_LOC_VECTOR_VIEW] = get_shader_location(self.shader, "viewPos")

                ambient_loc = get_shader_location(self.shader, "ambient")
                ambient_value = ffi.new('float[4]', [0.2, 0.2, 0.2, 1.0])
                set_shader_value(self.shader, ambient_loc, ambient_value, SHADER_UNIFORM_VEC4)

                from rlights import create_light, LIGHT_DIRECTIONAL
                create_light(LIGHT_DIRECTIONAL, Vector3(50.0, 50.0, 0.0), Vector3Zero(), WHITE, self.shader)
                
            except Exception as e:
                print(f"[x] Error loading bullet instancing shaders: {e}")
                self.instancing_enabled = False
                self.shader = None

        self.materials = {}
        bullet_types = ["normal", "heavy", "rapid"]
        bullet_colors = [YELLOW, RED, BLUE]
        
        for bullet_type, color in zip(bullet_types, bullet_colors):
            if self.instancing_enabled:
                material = load_material_default()
                material.shader = self.shader
                material.maps[MATERIAL_MAP_DIFFUSE].color = color
                self.materials[bullet_type] = material
            else:
                material = load_material_default()
                material.maps[MATERIAL_MAP_DIFFUSE].color = color
                self.materials[bullet_type] = material


    def add_bullet(self, position, direction, bullet_type="normal"):
        if len(self.bullets) >= self.max_bullets:
            for i, bullet in enumerate(self.bullets):
                if not bullet.active:
                    self.bullets.pop(i)
                    break
            else:
                self.bullets.pop(0)
            
        bullet = Bullet(position, direction, bullet_type)
        self.bullets.append(bullet)
        return bullet


    def update(self, dt, spatial_grid=None):
        for bullet in self.bullets[:]: 
            if not bullet.active:
                self.bullets.remove(bullet)
                continue
                
            bullet.update(dt)
            bullet.check_bounds()

            if spatial_grid:
                self.check_bullet_collisions(bullet, spatial_grid)


    def check_bullet_collisions(self, bullet, spatial_grid):
        if not bullet.active:
            return

        # only gets potential coliders insted of all 
        potential_colliders = spatial_grid.get_potential_colliders(bullet.position)
            
        for obj in potential_colliders:
            if bullet.check_collision_with(obj):
                damage_dealt = bullet.on_hit(obj)
                
                if hasattr(obj, 'take_damage'):
                    obj.take_damage(damage_dealt)

                break


    def draw(self, camera=None):
        if not self.bullets:
            return

        for bullet in self.bullets:
            if bullet.active:
                bullet.draw_trail()
        
        if self.instancing_enabled and camera:
            self.draw_instanced(camera)
        else:
            self.draw_individual()


    def draw_instanced(self, camera):
        if camera:
            camera_pos = ffi.new('float[3]', [camera.position.x, camera.position.y, camera.position.z])
            set_shader_value(self.shader, self.shader.locs[SHADER_LOC_VECTOR_VIEW], 
                           camera_pos, SHADER_UNIFORM_VEC3)
 
        bullets_by_type = {}
        for bullet in self.bullets:
            if not bullet.active:
                continue
            
            if bullet.bullet_type not in bullets_by_type:
                bullets_by_type[bullet.bullet_type] = []
            bullets_by_type[bullet.bullet_type].append(bullet)

        for bullet_type, type_bullets in bullets_by_type.items():
            if not type_bullets:
                continue

            transforms = []
            for bullet in type_bullets:
                transforms.append(bullet.get_transform_matrix())

            if len(transforms) > 0:
                try:
                    transforms_ptr = ffi.new('Matrix[]', transforms)
                    draw_mesh_instanced(
                        self.bullet_mesh, 
                        self.materials[bullet_type], 
                        transforms_ptr, 
                        len(transforms)
                    )
                except Exception as e:
                    if DEBUG:
                        print(f"Instancing failed, falling back to individual drawing: {e}")
                    self.draw_individual_type(type_bullets, bullet_type)


    def draw_individual_type(self, bullets, bullet_type):
        model = load_model_from_mesh(self.bullet_mesh)
        for bullet in bullets:
            if bullet.active:
                draw_model_ex(
                    model, 
                    bullet.position, 
                    Vector3(0, 1, 0), 
                    0, 
                    Vector3(bullet.size, bullet.size, bullet.size), 
                    bullet.color
                )
        unload_model(model)


    def draw_individual(self):
        for bullet in self.bullets:
            if bullet.active:
                draw_sphere(bullet.position, bullet.size * 0.2, bullet.color)
                draw_sphere(bullet.position, bullet.size * 0.3 * 0.3, fade(WHITE, 0.8))


    def clear_all(self):
        self.bullets.clear()


    def get_bullet_count(self):
        return len([b for b in self.bullets if b.active])


    def get_bullets_by_type(self, bullet_type):
        return [b for b in self.bullets if b.bullet_type == bullet_type and b.active]
    

    def __del__(self):
        if hasattr(self, 'shader') and self.shader is not None:
            unload_shader(self.shader)
        if hasattr(self, 'bullet_mesh'):
            unload_mesh(self.bullet_mesh)