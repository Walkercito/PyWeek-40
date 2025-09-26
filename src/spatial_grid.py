from settings import *
from collections import defaultdict

class SpatialGrid:
    """
    Manages a 2D spatial grid on the XZ plane for efficient collision detection.
    
    Objects are placed into grid cells based on their world position. When checking for collisions,
    we only need to test against objects within the same grid cell, drastically reducing
    the number of checks required per frame.
    """
    def __init__(self, cell_size):
        self.cell_size = cell_size
        self.grid = defaultdict(list)


    def _get_cell_coords(self, position):
        return (
            int(position.x // self.cell_size),
            int(position.z // self.cell_size)
        )


    def add_object(self, obj):
        aabb = obj.get_world_bounding_box()
        if not aabb:
            return

        min_coords = self._get_cell_coords(aabb.min)
        max_coords = self._get_cell_coords(aabb.max)

        for x in range(min_coords[0], max_coords[0] + 1):
            for z in range(min_coords[1], max_coords[1] + 1):
                self.grid[(x, z)].append(obj)
    

    def get_potential_colliders(self, position):
        cell_coords = self._get_cell_coords(position)
        return self.grid[cell_coords]


    def clear(self):
        self.grid.clear()