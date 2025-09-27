from settings import *

from models import Model
import random


class AIState(Enum):
    PATROL = "patrol"
    CHASE = "chase"
    ATTACK = "attack"
    EVADE = "evade"
    RETREAT = "retreat"
    EMERGENCY = "emergency"


class ManeuverType(Enum):
    STRAIGHT = "straight"
    CIRCLE_LEFT = "circle_left"
    CIRCLE_RIGHT = "circle_right"
    CLIMB = "climb"
    DIVE = "dive"
    BARREL_ROLL = "barrel_roll"
    SPLIT_S = "split_s"


class Enemy(Model):
    """AI enemy aircraft#"""

    def __init__(self, model, position, enemy_type="fighter"):
        super().__init__(model, speed=20, position=position)
        self.transform = matrix_identity()

        self.enemy_configs = {
            "fighter": {
                "max_speed": 25.0, "acceleration": 9.0, "max_health": 120,
                "aggressiveness": 0.9, "skill_level": 0.7,
                "bullet_type": "normal", "shoot_cooldown": 0.8,
                "burst_count": 3, "burst_delay": 0.2, "score_value": 100
            },
            "interceptor": {
                "max_speed": 32.0, "acceleration": 14.0, "max_health": 80,
                "aggressiveness": 1.0, "skill_level": 0.8,
                "bullet_type": "rapid", "shoot_cooldown": 1.2,
                "burst_count": 6, "burst_delay": 0.1, "score_value": 150
            },
            "bomber": {
                "max_speed": 18.0, "acceleration": 6.0, "max_health": 250,
                "aggressiveness": 0.6, "skill_level": 0.5,
                "bullet_type": "heavy", "shoot_cooldown": 1.5,
                "burst_count": 1, "burst_delay": 0.0, "score_value": 200
            }
        }

        config = self.enemy_configs.get(enemy_type, self.enemy_configs["fighter"])

        self.enemy_type = enemy_type
        self.max_speed = config["max_speed"]
        self.acceleration = config["acceleration"]
        self.max_health = config["max_health"]
        self.health = self.max_health
        self.aggressiveness = config["aggressiveness"]
        self.skill_level = config["skill_level"]
        self.bullet_type = config["bullet_type"]
        self.shoot_cooldown = Timer(config["shoot_cooldown"])
        self.score_value = config["score_value"]

        self.burst_count = config["burst_count"]
        self.burst_delay = config["burst_delay"]
        self.is_in_burst = False
        self.shots_in_burst_left = 0
        self.burst_timer = Timer(self.burst_delay)

        self.velocity = Vector3(0, 0, 0)
        self.target_direction = Vector3(0, 0, 1)
        self.drag = 0.7

        self.ai_state = AIState.PATROL
        self.state_timer = Timer(2.0)
        self.decision_timer = Timer(0.5)

        self.is_boosting = False
        self.max_boost_time = 4.0
        self.current_boost_time = self.max_boost_time
        self.boost_speed_multiplier = 1.6
        self.boost_recharge_rate = 0.8
        self.boost_depletion_rate = 1.2

        self.current_maneuver = ManeuverType.STRAIGHT
        self.maneuver_timer = Timer(4.0)
        self.maneuver_intensity = 1.0
        self.roll_angle = 0.0
        self.target_roll = 0.0
        self.roll_speed = 2.0

        self.avoidance_vector = Vector3(0, 0, 0)
        self.target_position = Vector3(0, 0, 0)
        self.patrol_center = Vector3(position.x, position.y, position.z)
        self.patrol_radius = 200.0
        self.safe_altitude_min = 20.0
        self.safe_altitude_max = 120.0

        self.player_threat_level = 0.0
        self.last_player_position = Vector3(0, 0, 0)
        self.detection_range = 500.0
        self.attack_range = 250.0
        self.retreat_threshold = 0.3

        self.stress_level = 0.0
        self.max_stress = 100.0

        self.collision_box = BoundingBox(
            Vector3(-4.0, -2.0, -6.0),
            Vector3(4.0, 2.0, 6.0)
        )
        self.avoidance_range = 100.0
        self.emergency_avoidance_range = 50.0


    def take_damage(self, amount):
        self.health -= amount
        if self.health < 0:
            self.health = 0

        stress_increase = amount * 2.0
        self.stress_level = min(self.stress_level + stress_increase, self.max_stress)

        if self.health < self.max_health * self.retreat_threshold:
            self.ai_state = AIState.RETREAT
            self.state_timer.activate()


    def update_ai_state(self, player_position, dt):
        self.decision_timer.update()
        self.state_timer.update()

        if not self.decision_timer:
            distance_to_player = vector3_distance(self.position, player_position)
            health_ratio = self.health / self.max_health

            self.assess_threats(player_position, distance_to_player)

            if health_ratio < self.retreat_threshold or self.stress_level > 80:
                self.ai_state = AIState.RETREAT
            elif distance_to_player < self.attack_range and self.player_threat_level > 0.3:
                self.ai_state = AIState.ATTACK
            elif distance_to_player < self.detection_range and self.player_threat_level > 0.1:
                self.ai_state = AIState.CHASE
            elif self.ai_state == AIState.ATTACK and distance_to_player > self.attack_range * 1.5:
                self.ai_state = AIState.CHASE
            elif not self.state_timer:
                if random.random() < 0.3:
                    self.ai_state = random.choice([AIState.PATROL, AIState.EVADE])
                    self.state_timer.activate()

            self.decision_timer.activate()


    def assess_threats(self, player_position, distance_to_player):
        if distance_to_player < self.detection_range:
            distance_threat = 1.0 - (distance_to_player / self.detection_range)
            self.player_threat_level = distance_threat * self.aggressiveness
        else:
            self.player_threat_level *= 0.9

        if self.position.y < self.safe_altitude_min + 10:
            self.stress_level += 20 * get_frame_time()

        boundary_distance = sqrt(self.position.x ** 2 + self.position.z ** 2)
        if boundary_distance > CITY_RADIUS - 100:
            self.stress_level += 15 * get_frame_time()

        self.stress_level = max(0, self.stress_level - 5 * get_frame_time())


    def calculate_desired_direction(self, player_position, spatial_grid):
        emergency_avoidance = self.calculate_emergency_avoidance(spatial_grid)
        if vector3_length_sqr(emergency_avoidance) > 0.1:
            return emergency_avoidance
        desired_direction = Vector3(0, 0, 0)

        if self.ai_state == AIState.PATROL:
            desired_direction = self.patrol_behavior()
        elif self.ai_state == AIState.CHASE:
            desired_direction = self.chase_behavior(player_position)
        elif self.ai_state == AIState.ATTACK:
            desired_direction = self.attack_behavior(player_position)
        elif self.ai_state == AIState.EVADE:
            desired_direction = self.evade_behavior(player_position)
        elif self.ai_state == AIState.RETREAT:
            desired_direction = self.retreat_behavior(player_position)

        general_avoidance = self.calculate_general_avoidance(spatial_grid)
        desired_direction = vector3_add(desired_direction, general_avoidance)

        boundary_avoidance = self.calculate_boundary_avoidance()
        desired_direction = vector3_add(desired_direction, boundary_avoidance)

        altitude_correction = self.calculate_altitude_correction()
        desired_direction = vector3_add(desired_direction, altitude_correction)

        return vector3_normalize(desired_direction)


    def patrol_behavior(self):
        to_center = vector3_subtract(self.patrol_center, self.position)
        distance_to_center = vector3_length(to_center)

        if distance_to_center > self.patrol_radius:
            return vector3_normalize(to_center)
        else:
            if distance_to_center < 50:
                away_from_center = vector3_normalize(vector3_subtract(self.position, self.patrol_center))
                return away_from_center
            else:
                right_vector = vector3_cross_product(Vector3(0, 1, 0), to_center)
                if vector3_length_sqr(right_vector) > 0.01:
                    return vector3_normalize(right_vector)
                else:
                    return Vector3(1, 0, 0)


    def chase_behavior(self, player_position):
        to_player = vector3_subtract(player_position, self.position)
        distance = vector3_length(to_player)

        if distance > 5.0:
            direct_chase = vector3_normalize(to_player)

            if self.skill_level > 0.6:
                predicted_pos = self.predict_player_position(player_position)
                to_predicted = vector3_subtract(predicted_pos, self.position)
                predicted_chase = vector3_normalize(to_predicted)

                blend_factor = 0.3
                final_direction = vector3_add(
                    vector3_scale(direct_chase, 1.0 - blend_factor),
                    vector3_scale(predicted_chase, blend_factor)
                )
                return vector3_normalize(final_direction)
            else:
                return direct_chase
        return Vector3(0, 0, 0)


    def attack_behavior(self, player_position):
        to_player = vector3_subtract(player_position, self.position)
        distance = vector3_length(to_player)

        if distance < 100:
            self.use_boost_if_needed()
            return self.execute_attack_maneuver(player_position)
        else:
            return self.chase_behavior(player_position)


    def handle_shooting(self, player_position, bullet_manager, audio_manager):
        if self.is_in_burst:
            if not self.burst_timer:
                if self.shots_in_burst_left > 0:
                    self.fire_one_shot(player_position, bullet_manager, audio_manager)
                    self.shots_in_burst_left -= 1
                    if self.shots_in_burst_left > 0:
                        self.burst_timer.activate()
                    else:
                        self.is_in_burst = False
                else:
                    self.is_in_burst = False
            return

        if self.shoot_cooldown:
            return

        to_player = vector3_normalize(vector3_subtract(player_position, self.position))
        forward = vector3_normalize(self.velocity)
        if vector3_length_sqr(forward) < 0.01:
            return

        if vector3_dot_product(forward, to_player) > 0.85:
            self.is_in_burst = True
            self.shots_in_burst_left = self.burst_count
            self.shoot_cooldown.activate()

            self.fire_one_shot(player_position, bullet_manager, audio_manager)
            self.shots_in_burst_left -= 1
            if self.shots_in_burst_left > 0:
                self.burst_timer.activate()


    def fire_one_shot(self, player_position, bullet_manager, audio_manager):
        inaccuracy = (1.0 - self.skill_level) * 0.1
        direction_to_player = vector3_normalize(vector3_subtract(player_position, self.position))

        offset = Vector3(
            uniform(-inaccuracy, inaccuracy),
            uniform(-inaccuracy, inaccuracy),
            uniform(-inaccuracy, inaccuracy)
        )
        final_direction = vector3_normalize(vector3_add(direction_to_player, offset))

        shoot_position = vector3_add(self.position, vector3_scale(final_direction, 6.0))
        bullet_manager.add_bullet(shoot_position, final_direction, self.bullet_type)

        if audio_manager:
            audio_manager.play_sound_3d(
                'shooting',
                self.position,
                self.velocity,
                base_volume=0.6,
                pitch_variation=0.05
            )


    def evade_behavior(self, player_position):
        away_from_player = vector3_subtract(self.position, player_position)
        distance = vector3_length(away_from_player)

        if distance < self.detection_range:
            self.use_boost_if_needed()
            return self.execute_evasive_maneuver(away_from_player)
        return Vector3(0, 0, 0)


    def retreat_behavior(self, player_position):
        to_center = vector3_subtract(Vector3(0, 60, 0), self.position)
        away_from_player = vector3_subtract(self.position, player_position)

        retreat_dir = vector3_add(
            vector3_scale(vector3_normalize(to_center), 0.7),
            vector3_scale(vector3_normalize(away_from_player), 0.3)
        )

        self.use_boost_if_needed()
        return vector3_normalize(retreat_dir)


    def execute_attack_maneuver(self, player_position):
        if not self.maneuver_timer:
            maneuvers = [ManeuverType.CIRCLE_LEFT, ManeuverType.CIRCLE_RIGHT,
                         ManeuverType.CLIMB, ManeuverType.DIVE]
            self.current_maneuver = random.choice(maneuvers)
            self.maneuver_timer.activate()

        return self.execute_maneuver(player_position)


    def execute_evasive_maneuver(self, away_direction):
        if not self.maneuver_timer:
            evasive_maneuvers = [ManeuverType.BARREL_ROLL, ManeuverType.SPLIT_S,
                                 ManeuverType.CLIMB, ManeuverType.CIRCLE_LEFT]
            self.current_maneuver = random.choice(evasive_maneuvers)
            self.maneuver_timer.activate()

        base_direction = vector3_normalize(away_direction)
        maneuver_offset = self.execute_maneuver(Vector3(0, 0, 0))

        return vector3_normalize(vector3_add(base_direction, maneuver_offset))


    def execute_maneuver(self, reference_position):
        self.maneuver_timer.update()
        maneuver_time = get_time()

        if self.current_maneuver == ManeuverType.CIRCLE_LEFT:
            self.target_roll = -25
            angle = maneuver_time * 1.5
            return Vector3(cos(angle) * 0.8, 0, sin(angle) * 0.8)

        elif self.current_maneuver == ManeuverType.CIRCLE_RIGHT:
            self.target_roll = 25
            angle = maneuver_time * -1.5
            return Vector3(cos(angle) * 0.8, 0, sin(angle) * 0.8)

        elif self.current_maneuver == ManeuverType.CLIMB:
            self.target_roll = 0
            return Vector3(0, 0.7, 0.3)

        elif self.current_maneuver == ManeuverType.DIVE:
            self.target_roll = 0
            return Vector3(0, -0.3, 0.7)

        elif self.current_maneuver == ManeuverType.BARREL_ROLL:
            roll_progress = (get_time() - self.maneuver_timer.start_time) * 2.0
            self.target_roll = sin(roll_progress) * 90
            return Vector3(sin(roll_progress) * 0.2, 0, 1)

        elif self.current_maneuver == ManeuverType.SPLIT_S:
            self.target_roll = 90
            return Vector3(0, -0.5, 0.5)

        return Vector3(0, 0, 1)


    def predict_player_position(self, player_position):
        player_velocity = vector3_subtract(player_position, self.last_player_position)
        prediction_time = 1.0

        predicted_position = vector3_add(player_position,
                                         vector3_scale(player_velocity, prediction_time))

        self.last_player_position = Vector3(player_position.x, player_position.y, player_position.z)
        return predicted_position


    def calculate_emergency_avoidance(self, spatial_grid):
        if not spatial_grid:
            return Vector3(0, 0, 0)

        forward_vector = vector3_normalize(self.velocity)
        if vector3_length_sqr(forward_vector) < 0.01:
            return Vector3(0, 0, 0)

        potential_colliders = spatial_grid.get_potential_colliders(self.position)
        for obj in potential_colliders:
            distance = vector3_distance(self.position, obj.position)
            if distance < self.emergency_avoidance_range:
                to_obstacle = vector3_normalize(vector3_subtract(obj.position, self.position))

                if vector3_dot_product(forward_vector, to_obstacle) > 0.8:
                    self.ai_state = AIState.EMERGENCY
                    away_vector = vector3_normalize(vector3_subtract(self.position, obj.position))
                    return vector3_normalize(Vector3(away_vector.x, 0.8, away_vector.z))

        return Vector3(0, 0, 0)


    def calculate_general_avoidance(self, spatial_grid):
        if not spatial_grid:
            return Vector3(0, 0, 0)

        avoidance_vector = Vector3(0, 0, 0)
        potential_colliders = spatial_grid.get_potential_colliders(self.position)
        for obj in potential_colliders:
            distance = vector3_distance(self.position, obj.position)
            if 0 < distance < self.avoidance_range:
                away_vector = vector3_normalize(vector3_subtract(self.position, obj.position))
                avoidance_strength = 1.0 - (distance / self.avoidance_range)
                scaled_avoidance = vector3_scale(away_vector, avoidance_strength)
                avoidance_vector = vector3_add(avoidance_vector, scaled_avoidance)

        return avoidance_vector


    def calculate_boundary_avoidance(self):
        boundary_limit = CITY_RADIUS - 50.0
        distance_from_center = sqrt(self.position.x ** 2 + self.position.z ** 2)

        if distance_from_center > boundary_limit:
            to_center = vector3_normalize(Vector3(-self.position.x, 0, -self.position.z))
            urgency = (distance_from_center - boundary_limit) / 50.0
            return vector3_scale(to_center, urgency * 2.0)

        return Vector3(0, 0, 0)


    def calculate_altitude_correction(self):
        if self.position.y < self.safe_altitude_min:
            urgency = (self.safe_altitude_min - self.position.y) / 20.0
            return Vector3(0, urgency * 2.0, 0)
        elif self.position.y > self.safe_altitude_max:
            urgency = (self.position.y - self.safe_altitude_max) / 50.0
            return Vector3(0, -urgency, 0)

        return Vector3(0, 0, 0)


    def use_boost_if_needed(self):
        if self.current_boost_time > 1.0 and not self.is_boosting:
            if (self.ai_state in [AIState.EVADE, AIState.RETREAT] or
                    self.stress_level > 50 or
                    self.health < self.max_health * 0.5):
                self.is_boosting = True


    def update_boost(self, dt):
        if self.is_boosting:
            self.current_boost_time -= self.boost_depletion_rate * dt
            if self.current_boost_time <= 0:
                self.current_boost_time = 0
                self.is_boosting = False
        else:
            if self.current_boost_time < self.max_boost_time:
                self.current_boost_time += self.boost_recharge_rate * dt
                if self.current_boost_time > self.max_boost_time:
                    self.current_boost_time = self.max_boost_time


    def update_physics(self, dt, desired_direction):
        self.target_direction = desired_direction

        current_max_speed = self.max_speed * self.boost_speed_multiplier if self.is_boosting else self.max_speed

        responsiveness = self.skill_level * self.acceleration
        stress_penalty = 1.0 - (self.stress_level / self.max_stress) * 0.3
        responsiveness *= stress_penalty

        desired_velocity = vector3_scale(self.target_direction, current_max_speed)
        steering_force = vector3_subtract(desired_velocity, self.velocity)
        steering_force = vector3_scale(steering_force, responsiveness * dt)
        self.velocity = vector3_add(self.velocity, steering_force)

        drag_force = vector3_scale(self.velocity, self.drag * dt)
        self.velocity = vector3_subtract(self.velocity, drag_force)

        self.position = vector3_add(self.position, vector3_scale(self.velocity, dt))

        self.roll_angle += (self.target_roll - self.roll_angle) * self.roll_speed * dt


    def update(self, dt, player_position, spatial_grid=None, bullet_manager=None, audio_manager=None):
        self.update_ai_state(player_position, dt)
        self.update_boost(dt)
        self.shoot_cooldown.update()
        self.burst_timer.update()

        desired_direction = self.calculate_desired_direction(player_position, spatial_grid)
        self.update_physics(dt, desired_direction)
        self.update_model_transform()

        if self.ai_state in [AIState.ATTACK, AIState.CHASE, AIState.PATROL, AIState.EVADE] and bullet_manager:
            self.handle_shooting(player_position, bullet_manager, audio_manager)


    def update_model_transform(self):
        if vector3_length_sqr(self.velocity) > 0.01:
            forward = vector3_normalize(self.velocity)
        else:
            forward = vector3_normalize(self.target_direction)

        if vector3_length_sqr(forward) < 0.01:
            forward = Vector3(0, 0, 1)

        world_up = Vector3(0, 1, 0)

        right = vector3_normalize(vector3_cross_product(forward, world_up))
        up = vector3_normalize(vector3_cross_product(right, forward))

        roll_rad = radians(self.roll_angle)

        rolled_up = vector3_rotate_by_axis_angle(up, forward, roll_rad)
        rolled_right = vector3_rotate_by_axis_angle(right, forward, roll_rad)

        self.transform = Matrix(
            rolled_right.x, rolled_up.x, -forward.x, self.position.x,
            rolled_right.y, rolled_up.y, -forward.y, self.position.y,
            rolled_right.z, rolled_up.z, -forward.z, self.position.z,
            0.0, 0.0, 0.0, 1.0
        )


    def draw(self):
        if self.model is None:
            draw_cube(self.position, 4.0, 2.0, 6.0, Color(255, 0, 255, 150))
            return

        for i in range(self.model.meshCount):
            mesh = self.model.meshes[i]
            material = self.model.materials[self.model.meshMaterial[i]]
            draw_mesh(mesh, material, self.transform)

        health_ratio = self.health / self.max_health
        bar_color = GREEN if health_ratio > 0.6 else (YELLOW if health_ratio > 0.3 else RED)

        bar_pos = Vector3(self.position.x, self.position.y + 8, self.position.z)
        bar_width = 10.0
        bar_height = 1.0

        draw_cube(bar_pos, bar_width, bar_height, 0.5, Color(50, 50, 50, 200))
        filled_width = bar_width * health_ratio
        health_bar_pos = Vector3(bar_pos.x - (bar_width - filled_width) / 2, bar_pos.y, bar_pos.z)
        draw_cube(health_bar_pos, filled_width, bar_height, 0.5, bar_color)

        state_colors = {
            AIState.PATROL: GREEN,
            AIState.CHASE: YELLOW,
            AIState.ATTACK: RED,
            AIState.EVADE: PURPLE,
            AIState.RETREAT: BLUE,
            AIState.EMERGENCY: ORANGE
        }
        state_color = state_colors.get(self.ai_state, WHITE)
        state_indicator_pos = Vector3(self.position.x, self.position.y + 10, self.position.z)
        draw_cube(state_indicator_pos, 2.0, 1.0, 0.5, state_color)


class EnemyManager:
    """Manages multiple enemy aircraft"""

    def __init__(self, models, vfx_manager):
        self.models = models
        self.vfx_manager = vfx_manager
        self.enemies = []

        self.max_enemies = 18
        self.spawn_timer = Timer(4.0)
        self.enemy_types = ["fighter", "interceptor", "bomber"]

        self.available_models = []
        for model_name in ["enemy01", "enemy02"]:
            if model_name in self.models and self.models[model_name] is not None:
                self.available_models.append(model_name)
            else:
                print(f"[!] Enemy model '{model_name}' not found or failed to load")

        if not self.available_models:
            print("[ERROR] No enemy models available! Check your model files.")
        else:
            print(f"[*] Available enemy models: {self.available_models}")


    def spawn_enemy(self, position=None, enemy_type=None):
        if len(self.enemies) >= self.max_enemies:
            return None

        if not self.available_models:
            return None

        if position is None:
            angle = random.uniform(0, 360)
            distance = random.uniform(CITY_RADIUS * 0.7, CITY_RADIUS * 0.9)
            x = cos(radians(angle)) * distance
            z = sin(radians(angle)) * distance
            y = random.uniform(40, 100)
            position = Vector3(x, y, z)

        if enemy_type is None:
            enemy_type = random.choice(self.enemy_types)

        model_name = random.choice(self.available_models)
        base_model = self.models[model_name]

        if base_model is None:
            return None

        try:
            enemy = Enemy(base_model, position, enemy_type)
            if enemy.model is None:
                return None

            self.enemies.append(enemy)

            return enemy

        except Exception as e:
            print(f"[ERROR] Failed to create enemy: {e}")
            return None


    def update(self, dt, player_position, spatial_grid=None, bullet_manager=None, audio_manager=None):
        score_from_kills = 0
        enemies_defeated_count = 0
        defeated_enemies_info = []
        self.spawn_timer.update()

        if not self.spawn_timer and len(self.enemies) < self.max_enemies:
            self.spawn_enemy()
            self.spawn_timer.activate()

        for enemy in self.enemies[:]:
            if enemy.health <= 0:
                score_from_kills += enemy.score_value
                enemies_defeated_count += 1
                defeated_enemies_info.append({'position': enemy.position, 'velocity': enemy.velocity})
                self.vfx_manager.create_explosion(enemy.position, "explosion_air02")
                self.enemies.remove(enemy)
                continue

            enemy.update(dt, player_position, spatial_grid, bullet_manager, audio_manager)

            if bullet_manager:
                self.check_enemy_bullet_collisions(enemy, bullet_manager)

        return score_from_kills, enemies_defeated_count, defeated_enemies_info 


    def check_enemy_bullet_collisions(self, enemy, bullet_manager):
        for bullet in bullet_manager.bullets:
            if bullet.active and bullet.check_collision_with(enemy):
                damage = bullet.on_hit(enemy)
                enemy.take_damage(damage)
                self.vfx_manager.create_explosion(bullet.position, "explosion_air01", scale=3.0)
                break


    def draw(self):
        for enemy in self.enemies:
            enemy.draw()


    def get_enemy_count(self):
        return len(self.enemies)


    def clear_all(self):
        self.enemies.clear()


    def get_enemies(self):
        return self.enemies