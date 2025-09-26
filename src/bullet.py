from settings import *
from models import Model


class Bullet(Model):
    """Base class for projectiles"""
    def __init__(self, position, direction, bullet_type="normal"):
        mesh = gen_mesh_sphere(0.2, 8, 8)
        model = load_model_from_mesh(mesh)

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
        
        super().__init__(
            model=model, 
            speed=config["speed"], 
            position=position, 
            direction=direction
        )
        
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
        
        self.trail_positions = []
        self.max_trail_length = 10


    def update(self, dt):
        if not self.active:
            return
            
        super().update(dt)
        
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.active = False
            return
            
        self.trail_positions.append(Vector3(self.position.x, self.position.y, self.position.z))
        if len(self.trail_positions) > self.max_trail_length:
            self.trail_positions.pop(0)


    def draw(self):
        if not self.active:
            return

        self.draw_trail()
        
        draw_model(self.model, self.position, self.size, self.color)
        draw_sphere(self.position, self.size * 0.3, fade(WHITE, 0.8))


    def draw_trail(self):
        if len(self.trail_positions) < 2:
            return
            
        for i in range(len(self.trail_positions) - 1):
            alpha = (i / len(self.trail_positions)) * 0.5
            trail_color = fade(self.color, alpha)
            trail_size = (i / len(self.trail_positions)) * self.size * 0.5
            
            if trail_size > 0.02: 
                draw_sphere(self.trail_positions[i], trail_size, trail_color)


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
    """Game's Bullet Manager"""
    def __init__(self):
        self.bullets = []
        self.max_bullets = 50  # limit to avoid lag


    def add_bullet(self, position, direction, bullet_type="normal"):
        if len(self.bullets) >= self.max_bullets:
            self.bullets.pop(0)
            
        bullet = Bullet(position, direction, bullet_type)
        self.bullets.append(bullet)
        return bullet


    def update(self, dt, collidable_objects=None):
        for bullet in self.bullets[:]: 
            if not bullet.active:
                self.bullets.remove(bullet)
                continue
                
            bullet.update(dt)
            bullet.check_bounds()

            if collidable_objects:
                self.check_bullet_collisions(bullet, collidable_objects)


    def check_bullet_collisions(self, bullet, collidable_objects):
        if not bullet.active:
            return
            
        for obj in collidable_objects:
            if bullet.check_collision_with(obj):
                damage_dealt = bullet.on_hit(obj)
                
                if hasattr(obj, 'take_damage'):
                    obj.take_damage(damage_dealt)
                
                break


    def draw(self):
        for bullet in self.bullets:
            bullet.draw()


    def clear_all(self):
        self.bullets.clear()


    def get_bullet_count(self):
        return len([b for b in self.bullets if b.active])


    def get_bullets_by_type(self, bullet_type):
        return [b for b in self.bullets if b.bullet_type == bullet_type and b.active]