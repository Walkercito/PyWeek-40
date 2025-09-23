from settings import *
from models import Model

class Floor(Model):
    def __init__(self, texture):
        model = load_model_from_mesh(gen_mesh_cube(32, 1, 32))
        set_material_texture(model.materials[0], MATERIAL_MAP_ALBEDO, texture)
        super().__init__(model = model, position = Vector3(0, -1, 0), speed =0)