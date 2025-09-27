from settings import *
from collections import defaultdict
from os import listdir


class Animation:
    """Represents an animation instance in the game."""

    def __init__(self, position, frames, frame_rate, scale=1.0, on_finish=None):
        self.position = position
        self.frames = frames
        self.frame_rate = frame_rate
        self.frame_duration = 1.0 / frame_rate
        self.scale = scale
        self.on_finish = on_finish

        self.active = True
        self.current_frame_index = 0
        self.frame_timer = 0.0

    def update(self, dt):
        if not self.active:
            return

        self.frame_timer += dt
        if self.frame_timer >= self.frame_duration:
            self.frame_timer = 0
            self.current_frame_index += 1
            if self.current_frame_index >= len(self.frames):
                self.active = False
                if self.on_finish:
                    self.on_finish()

    def get_current_texture(self):
        if self.active:
            return self.frames[self.current_frame_index]
        return None


class VFXManager:
    """Manages all visual effects, such as explosion animations."""

    def __init__(self):
        self.animations = []
        self.animation_frames = defaultdict(list)
        self.load_animations()

    def load_animations(self):
        print("[*] Loading VFX animations...")
        vfx_folders = {
            "explosion_air01": join("assets", "vfx", "explosion_air01"),
            "explosion_air02": join("assets", "vfx", "explosion_air02")
        }

        for name, path in vfx_folders.items():
            if not exists(path):
                print(f"[!] VFX folder not found: {path}")
                continue

            try:
                files = sorted([f for f in listdir(path) if f.endswith('.png')])
                for filename in files:
                    texture = load_texture(join(path, filename))
                    self.animation_frames[name].append(texture)
                print(f"[*] Loaded {len(self.animation_frames[name])} frames for '{name}'")
            except Exception as e:
                print(f"[ERROR] Failed to load animation '{name}': {e}")

    def create_explosion(self, position, explosion_type="explosion_air01", scale=9.0, on_finish=None):
        if explosion_type not in self.animation_frames or not self.animation_frames[explosion_type]:
            print(f"[WARNING] Tried to create an explosion of type '{explosion_type}', but no frames are loaded.")
            return

        frames = self.animation_frames[explosion_type]
        animation = Animation(position, frames, frame_rate=24, scale=scale, on_finish=on_finish)
        self.animations.append(animation)

    def update(self, dt):
        for anim in self.animations[:]:
            anim.update(dt)
            if not anim.active:
                self.animations.remove(anim)

    def draw(self, camera):
        if not self.animations:
            return

        begin_blend_mode(BLEND_ALPHA)
        rl_disable_depth_mask()

        for anim in self.animations:
            texture = anim.get_current_texture()
            if texture:
                draw_billboard(
                    camera,
                    texture,
                    anim.position,
                    anim.scale,
                    WHITE
                )

        rl_enable_depth_mask()
        end_blend_mode()

    def __del__(self):
        print("[*] Unloading VFX textures...")
        for frame_list in self.animation_frames.values():
            for texture in frame_list:
                unload_texture(texture)