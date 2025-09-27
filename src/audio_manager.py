from settings import *


class AudioManager:
    """
    Manage all audio functionalities including loading assets, playing 3D and UI sounds,
    handling music streams, and applying user settings.
    """
    def __init__(self, camera, player, initial_settings):
        self.camera = camera
        self.player = player
        self.settings = initial_settings

        self.sounds = {}
        self.music = {}
        self.current_game_music = None
        self.warning_sound_timer = Timer(1.0)  
        self.warning_sound_instance = None  
        
        self.load_assets()
        self.apply_settings()


    def load_assets(self):
        print("[*] Loading audio assets...")
        self.sounds = {
            "warning": load_sound(join("assets", "audio", "beep-warning.mp3")),
            "player_explosion": load_sound(join("assets", "audio", "massive-explosion.mp3")),
            "enemy_explosions": [
                load_sound(join("assets", "audio", "explosion.mp3")),
                load_sound(join("assets", "audio", "explosion01.mp3"))
            ],
            "shooting": load_sound(join("assets", "audio", "normal-shooting.mp3"))
        }

        self.music = {
            "menu": load_music_stream(join("assets", "audio", "menu.mp3")),
            "game": [
                load_music_stream(join("assets", "audio", "game-background01.mp3")),
                load_music_stream(join("assets", "audio", "game-background02.mp3")),
                load_music_stream(join("assets", "audio", "game-background03.mp3"))
            ]
        }
        print("[*] Audio assets loaded successfully!")


    def manage_music_streams(self, game_state):
        is_menu_state = game_state in [GameState.MAIN_MENU, GameState.SETTINGS, GameState.GRAPHICS_SETTINGS,
                                       GameState.CONTROLS_INFO, GameState.CREDITS_SCREEN]
        if is_menu_state and self.warning_sound_instance and is_sound_playing(self.warning_sound_instance):
            stop_sound(self.warning_sound_instance)
            self.warning_sound_instance = None
            self.warning_sound_timer.deactivate()

        target_music = None
        if is_menu_state:
            target_music = self.music['menu']
        elif game_state == GameState.PLAYING:
            if self.current_game_music is None or not is_music_stream_playing(self.current_game_music):
                self.current_game_music = choice(self.music['game'])
            target_music = self.current_game_music
        
        if target_music:
            if not is_music_stream_playing(target_music):
                for stream_list in self.music.values():
                    streams = stream_list if isinstance(stream_list, list) else [stream_list]
                    for stream in streams:
                        if is_music_stream_playing(stream):
                            stop_music_stream(stream)
                play_music_stream(target_music)
            
            update_music_stream(target_music)
        else:
            active_music = self.current_game_music if self.current_game_music else self.music['menu']
            if active_music and is_music_stream_playing(active_music):
                 stop_music_stream(active_music)
            self.current_game_music = None


    def manage_warning_sound(self, game_state, show_altitude_warning, show_boundary_warning):
        if game_state != GameState.PLAYING:
            if self.warning_sound_instance and is_sound_playing(self.warning_sound_instance):
                stop_sound(self.warning_sound_instance)
                self.warning_sound_instance = None
            self.warning_sound_timer.deactivate()
            return

        self.warning_sound_timer.update()
        
        if (show_altitude_warning or show_boundary_warning) and not self.warning_sound_timer:
            self.warning_sound_instance = self.play_sound_ui("warning")
            self.warning_sound_timer.activate()
        elif not (show_altitude_warning or show_boundary_warning):
            if self.warning_sound_instance and is_sound_playing(self.warning_sound_instance):
                stop_sound(self.warning_sound_instance)
                self.warning_sound_instance = None
            self.warning_sound_timer.deactivate()


    def play_sound_3d(self, sound_key, position, velocity, base_volume=1.0, pitch_variation=0.0):
        if self.settings['muted']:
            return

        sound_to_play = None
        if isinstance(self.sounds[sound_key], list):
            sound_to_play = choice(self.sounds[sound_key])
        else:
            sound_to_play = self.sounds[sound_key]

        listener_pos = self.camera.position

        distance = vector3_distance(listener_pos, position)
        if distance > MAX_AUDIO_DISTANCE:
            return

        attenuation = 1.0 - (distance / MAX_AUDIO_DISTANCE)**2
        volume = base_volume * max(0.0, attenuation)

        # calculate pan based on camera orientation
        to_sound = vector3_normalize(vector3_subtract(position, listener_pos))
        cam_forward = vector3_normalize(vector3_subtract(self.camera.target, listener_pos))
        cam_right = vector3_normalize(vector3_cross_product(cam_forward, self.camera.up))
        
        pan_dot = vector3_dot_product(to_sound, cam_right)
        pan = 0.5 + pan_dot * 0.5
        pan = min(max(pan, 0.0), 1.0)

        # simulate dopler effect
        listener_velocity = self.player.velocity
        relative_velocity = vector3_subtract(velocity, listener_velocity)
        speed_towards_listener = vector3_dot_product(relative_velocity, to_sound)
        
        pitch_shift = 1.0 - (speed_towards_listener / SPEED_OF_SOUND)
        pitch = 1.0 * pitch_shift

        # add random tone variation
        if pitch_variation > 0:
            pitch += uniform(-pitch_variation, pitch_variation)
        
        pitch = max(0.1, pitch)

        set_sound_volume(sound_to_play, volume)
        set_sound_pan(sound_to_play, pan)
        set_sound_pitch(sound_to_play, pitch)
        play_sound(sound_to_play)


    def play_sound_ui(self, sound_key):
        if self.settings['muted']:
            return None
            
        sound = self.sounds.get(sound_key)
        if sound:
            set_sound_volume(sound, 1.0)
            set_sound_pan(sound, 0.5)
            set_sound_pitch(sound, 1.0)
            play_sound(sound)
            return sound  # return to sound to be stoped later
        return None


    def apply_settings(self):
        base_volume = self.settings['master_volume'] if not self.settings['muted'] else 0.0
        set_master_volume(base_volume)


    def cleanup(self):
        print("[*] Unloading audio assets...")
        for sound_or_list in self.sounds.values():
            if isinstance(sound_or_list, list):
                for s in sound_or_list: unload_sound(s)
            else:
                unload_sound(sound_or_list)
        
        for music_or_list in self.music.values():
            if isinstance(music_or_list, list):
                for m in music_or_list: unload_music_stream(m)
            else:
                unload_music_stream(music_or_list)