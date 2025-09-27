from settings import *
from models import SkyscraperSimple, SkycraperMultipleLayer
from spatial_grid import SpatialGrid


class BuildingData:
    """Lightweight building data for instancing"""

    def __init__(self, position, rotation_angle, building_type):
        self.position = position
        self.rotation_angle = rotation_angle
        self.building_type = building_type  # "simple" or "complex"
        self.transform_matrix = self.calculate_transform_matrix()

    def calculate_transform_matrix(self):
        rotation_matrix = matrix_rotate_y(radians(self.rotation_angle))
        translation_matrix = matrix_translate(self.position.x, self.position.y, self.position.z)

        return matrix_multiply(rotation_matrix, translation_matrix)


class BuildingManager:
    """Manages building rendering with instancing and collision detection"""

    def __init__(self, models):
        self.models = models

        self.building_data = {
            "simple": [],
            "complex": []
        }
        self.collision_objects = []

        self.spatial_grid = SpatialGrid(cell_size=GRID_CELL_SIZE)
        self.setup_instancing()

    def setup_instancing(self):
        vs_path = join("shaders", "buildings", "building_instancing.vs")
        fs_path = join("shaders", "buildings", "building_instancing.fs")

        if not exists(vs_path) or not exists(fs_path):
            print("Warning: Building instancing shaders not found!")
            print(f"  Vertex shader: {vs_path} - {'[*]' if exists(vs_path) else '[✗]'}")
            print(f"  Fragment shader: {fs_path} - {'[*]' if exists(fs_path) else '[✗]'}")
            print("Using individual building rendering...")
            self.instancing_enabled = False
            self.shader = None
            return

        try:
            self.shader = load_shader(vs_path, fs_path)
            self.instancing_enabled = True
            print("[*] Building instancing shaders loaded successfully")

            self.shader.locs[SHADER_LOC_MATRIX_MVP] = get_shader_location(self.shader, "mvp")
            self.shader.locs[SHADER_LOC_VECTOR_VIEW] = get_shader_location(self.shader, "viewPos")
            self.shader.locs[SHADER_LOC_MATRIX_MODEL] = get_shader_location(self.shader, "matModel")
            self.shader.locs[SHADER_LOC_MATRIX_VIEW] = get_shader_location(self.shader, "matView")
            self.shader.locs[SHADER_LOC_MATRIX_PROJECTION] = get_shader_location(self.shader, "matProjection")

            ambient_loc = get_shader_location(self.shader, "ambient")
            ambient_value = ffi.new('float[4]', [0.3, 0.3, 0.3, 1.0])
            set_shader_value(self.shader, ambient_loc, ambient_value, SHADER_UNIFORM_VEC4)

            fog_density_loc = get_shader_location(self.shader, "fogDensity")
            fog_color_loc = get_shader_location(self.shader, "fogColor")

            fog_density_value = ffi.new('float *', 0.8)
            fog_color_value = ffi.new('float[3]', [0.6, 0.8, 1.0])

            set_shader_value(self.shader, fog_density_loc, fog_density_value, SHADER_UNIFORM_FLOAT)
            set_shader_value(self.shader, fog_color_loc, fog_color_value, SHADER_UNIFORM_VEC3)

            try:
                from rlights import create_light, LIGHT_DIRECTIONAL
                create_light(LIGHT_DIRECTIONAL, Vector3(100.0, 200.0, 50.0), Vector3Zero(), WHITE, self.shader)
            except ImportError:
                print("Warning: rlights not available, building lighting will be basic")

            self.setup_materials()

        except Exception as e:
            print(f"[x] Error loading building instancing shaders: {e}")
            self.instancing_enabled = False
            self.shader = None

    def setup_materials(self):
        self.materials = {}

        material_simple = load_material_default()
        if self.instancing_enabled:
            material_simple.shader = self.shader
        material_simple.maps[MATERIAL_MAP_DIFFUSE].color = Color(200, 200, 200, 255)  # light gray
        self.materials["simple"] = material_simple

        material_complex = load_material_default()
        if self.instancing_enabled:
            material_complex.shader = self.shader
        material_complex.maps[MATERIAL_MAP_DIFFUSE].color = Color(180, 180, 180, 255)  # darker gray
        self.materials["complex"] = material_complex

    def add_building(self, position, rotation_angle, building_type_model):
        if building_type_model == "skyscraper01":
            building_type = "complex"
            collision_obj = SkycraperMultipleLayer(
                self.models["skyscraper01"],
                position,
                rotation_angle=rotation_angle
            )
        else:
            building_type = "simple"
            collision_obj = SkyscraperSimple(
                self.models["skyscraper02"],
                position,
                rotation_angle=rotation_angle
            )

        self.collision_objects.append(collision_obj)
        self.spatial_grid.add_object(collision_obj)

        building_data = BuildingData(position, rotation_angle, building_type)
        self.building_data[building_type].append(building_data)

        return collision_obj

    def generate_city(self, count=BUILDING_COUNT):
        print(f"Generating {count} buildings with instancing in a radius of {CITY_RADIUS}m.")

        self.building_data = {"simple": [], "complex": []}
        self.collision_objects.clear()
        self.spatial_grid.clear()

        max_attempts_per_building = 100

        for _ in range(count):
            for attempt in range(max_attempts_per_building):
                x = uniform(-CITY_RADIUS, CITY_RADIUS)
                z = uniform(-CITY_RADIUS, CITY_RADIUS)

                if sqrt(x * x + z * z) < MIN_DISTANCE_FROM_CENTER:
                    continue

                is_overlapping = False
                new_pos = Vector3(x, 0, z)
                for existing_building in self.collision_objects:
                    existing_pos = existing_building.position
                    distance = sqrt((new_pos.x - existing_pos.x) ** 2 + (new_pos.z - existing_pos.z) ** 2)

                    if distance < MIN_BUILDING_DISTANCE:
                        is_overlapping = True
                        break

                if not is_overlapping:
                    rotation = choice([0, 90, 180, 270])

                    if randint(1, 10) <= 4:
                        building_model = "skyscraper01"
                        position = Vector3(x, -10, z)
                    else:
                        building_model = "skyscraper02"
                        position = Vector3(x, -14.8, z)

                    self.add_building(position, rotation, building_model)
                    break
            else:
                print(f"[WARNING]: Could not find a position for a building after {max_attempts_per_building} attempts.")

        simple_count = len(self.building_data["simple"])
        complex_count = len(self.building_data["complex"])
        print(f"Generated {simple_count} simple buildings and {complex_count} complex buildings")
        print(f"Instancing: {'ENABLED' if self.instancing_enabled else 'DISABLED'}")

    def update_shader_uniforms(self, camera):
        if not self.instancing_enabled or not camera:
            return

        camera_pos = ffi.new('float[3]', [camera.position.x, camera.position.y, camera.position.z])
        set_shader_value(self.shader, self.shader.locs[SHADER_LOC_VECTOR_VIEW],
                         camera_pos, SHADER_UNIFORM_VEC3)

    def draw(self, camera=None):
        if self.instancing_enabled and camera:
            self.update_shader_uniforms(camera)
            self.draw_instanced()
        else:
            self.draw_individual()

    def draw_instanced(self):
        if self.building_data["simple"]:
            transforms = [building.transform_matrix for building in self.building_data["simple"]]
            if transforms:
                try:
                    simple_mesh = self.models["skyscraper02"].meshes[0]
                    transforms_ptr = ffi.new('Matrix[]', transforms)
                    draw_mesh_instanced(
                        simple_mesh,
                        self.materials["simple"],
                        transforms_ptr,
                        len(transforms)
                    )
                except Exception:
                    self.draw_individual_type("simple")

        if self.building_data["complex"]:
            transforms = [building.transform_matrix for building in self.building_data["complex"]]
            if transforms:
                try:
                    complex_mesh = self.models["skyscraper01"].meshes[0]
                    transforms_ptr = ffi.new('Matrix[]', transforms)
                    draw_mesh_instanced(
                        complex_mesh,
                        self.materials["complex"],
                        transforms_ptr,
                        len(transforms)
                    )
                except Exception:
                    self.draw_individual_type("complex")

    def draw_individual_type(self, building_type):
        model_key = "skyscraper01" if building_type == "complex" else "skyscraper02"
        model = self.models[model_key]
        material = self.materials[building_type]

        for building_data in self.building_data[building_type]:
            pos = building_data.position
            rot = building_data.rotation_angle
            draw_model_ex(model, pos, Vector3(0, 1, 0), rot, Vector3(1, 1, 1),
                          material.maps[MATERIAL_MAP_DIFFUSE].color)

    def draw_individual(self):
        """Fallback: Draw each building individually like the original system"""
        for obj in self.collision_objects:
            obj.draw()

    def get_collision_objects(self):
        return self.collision_objects

    def get_spatial_grid(self):
        return self.spatial_grid

    def clear_all(self):
        self.building_data = {"simple": [], "complex": []}
        self.collision_objects.clear()
        self.spatial_grid.clear()

    def get_building_count(self):
        return len(self.collision_objects)

    def get_instancing_stats(self):
        simple_count = len(self.building_data["simple"])
        complex_count = len(self.building_data["complex"])
        return {
            "total": simple_count + complex_count,
            "simple": simple_count,
            "complex": complex_count,
            "instancing_enabled": self.instancing_enabled,
            "draw_calls": 2 if self.instancing_enabled else simple_count + complex_count
        }

    def __del__(self):
        if hasattr(self, 'shader') and self.shader is not None:
            unload_shader(self.shader)