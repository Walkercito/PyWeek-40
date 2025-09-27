from settings import *


class UIManager:
    """Manages drawing all UI screens like menus and game over screens."""

    def __init__(self, font):
        self.font = font

    def draw_button(self, text, rect, font_size, is_hover):
        """Draws a button based on its state. Does not handle logic."""
        base_color = Color(50, 100, 200, 180)
        hover_color = Color(100, 150, 255, 220)

        draw_rectangle_rec(rect, hover_color if is_hover else base_color)
        draw_rectangle_lines_ex(rect, 3, fade(SKYBLUE, 0.8))

        scaled_font_size = int(font_size * (get_screen_height() / 980))
        text_width = measure_text_ex(self.font, text, scaled_font_size, 1).x
        text_pos = Vector2(int(rect.x + (rect.width - text_width) / 2),
                           int(rect.y + (rect.height - scaled_font_size) / 2))
        draw_text_ex(self.font, text, text_pos, scaled_font_size, 1, WHITE)

    def draw_rotating_skybox(self, skybox, camera):
        """Draws the skybox for menu backgrounds."""
        begin_mode_3d(camera)
        skybox.draw()
        end_mode_3d()

    def draw_main_menu(self, skybox, menu_camera, high_score, splash_text, button_rects, hover_states):
        """Draws the main menu screen."""
        self.draw_rotating_skybox(skybox, menu_camera)

        sw, sh = get_screen_width(), get_screen_height()
        title_font_size = int(120 * sh / 980)
        hs_font_size = int(30 * sh / 980)

        title = TITLE
        title_width = measure_text_ex(self.font, title, title_font_size, 1).x
        draw_text_ex(self.font, title, Vector2(int((sw - title_width) / 2), int(sh / 4)), title_font_size, 1, SKYBLUE)

        splash_font_size = int(40 * sh / 980)
        splash_size = measure_text_ex(self.font, splash_text, splash_font_size, 1)
        origin = Vector2(splash_size.x / 2, splash_size.y / 2)
        position = Vector2(int(sw * 0.75), int(sh * 0.35))
        rotation = 20.0 + sin(get_time() * 2) * 2.0
        draw_text_pro(self.font, splash_text, position, origin, rotation, splash_font_size, 1, YELLOW)

        hs_text = f"HIGHEST SCORE: {high_score}"
        hs_width = measure_text_ex(self.font, hs_text, hs_font_size, 1).x
        draw_text_ex(self.font, hs_text, Vector2(int((sw - hs_width) / 2), int(sh / 4 + title_font_size * 1.2)),
                     hs_font_size, 1, WHITE)

        self.draw_button("START GAME", button_rects["start"], 30, hover_states["start"])
        self.draw_button("SETTINGS", button_rects["settings"], 30, hover_states["settings"])
        self.draw_button("QUIT", button_rects["quit"], 30, hover_states["quit"])
        
        version_font_size = int(20 * sh / 980)
        draw_text_ex(self.font, "Aftershock v1.0.0", Vector2(10, sh - 30), version_font_size, 1, fade(WHITE, 0.7))


    def draw_settings_menu(self, skybox, menu_camera, button_rects, hover_states):
        self.draw_rotating_skybox(skybox, menu_camera)
        sw, sh = get_screen_width(), get_screen_height()
        title_font_size = int(80 * sh / 980)
        title = "SETTINGS"
        title_width = measure_text_ex(self.font, title, title_font_size, 1).x
        draw_text_ex(self.font, title, Vector2(int((sw - title_width) / 2), int(sh / 4)), title_font_size, 1, WHITE)

        self.draw_button("GRAPHICS", button_rects["graphics"], 30, hover_states["graphics"])
        self.draw_button("CONTROLS", button_rects["controls"], 30, hover_states["controls"])
        self.draw_button("CREDITS", button_rects["credits"], 30, hover_states["credits"])
        self.draw_button("BACK", button_rects["back"], 30, hover_states["back"])

    def draw_graphics_menu(self, skybox, menu_camera, settings, resolutions, button_rects, hover_states):
        self.draw_rotating_skybox(skybox, menu_camera)
        sw, sh = get_screen_width(), get_screen_height()
        title_font_size = int(80 * sh / 980)
        text_font_size = int(30 * sh / 980)

        title = "GRAPHICS & AUDIO"
        title_width = measure_text_ex(self.font, title, title_font_size, 1).x
        draw_text_ex(self.font, title, Vector2(int((sw - title_width) / 2), int(sh * 0.1)), title_font_size, 1, WHITE)

        base_x = sw * 0.1

        res_text = f"Resolution: {resolutions[settings['resolution_index']][0]} x {resolutions[settings['resolution_index']][1]}"
        draw_text_ex(self.font, res_text, Vector2(int(base_x), int(sh * 0.31)), text_font_size, 1, WHITE)

        fs_text = f"Fullscreen: {'ON' if settings['fullscreen'] else 'OFF'}"
        draw_text_ex(self.font, fs_text, Vector2(int(base_x), int(sh * 0.41)), text_font_size, 1, WHITE)

        audio_text = f"Audio: {'MUTED' if settings['muted'] else 'ON'}"
        draw_text_ex(self.font, audio_text, Vector2(int(base_x), int(sh * 0.51)), text_font_size, 1, WHITE)

        volume_text = f"Volume: {int(settings['master_volume'] * 100)}%"
        draw_text_ex(self.font, volume_text, Vector2(int(base_x), int(sh * 0.61)), text_font_size, 1, WHITE)

        self.draw_button("CHANGE", button_rects["resolution"], 30, hover_states["resolution"])
        self.draw_button("TOGGLE", button_rects["fullscreen"], 30, hover_states["fullscreen"])
        self.draw_button("TOGGLE", button_rects["mute"], 30, hover_states["mute"])
        self.draw_button("-", button_rects["vol_down"], 40, hover_states["vol_down"])
        self.draw_button("+", button_rects["vol_up"], 40, hover_states["vol_up"])

        self.draw_button("BACK", button_rects["back"], 30, hover_states["back"])

    def draw_controls_screen(self, skybox, menu_camera, button_rects, hover_states):
        self.draw_rotating_skybox(skybox, menu_camera)
        sw, sh = get_screen_width(), get_screen_height()
        title_font_size = int(80 * sh / 980)
        text_font_size = int(28 * sh / 980)

        title = "CONTROLS"
        title_width = measure_text_ex(self.font, title, title_font_size, 1).x
        draw_text_ex(self.font, title, Vector2(int((sw - title_width) / 2), int(sh * 0.1)), title_font_size, 1, WHITE)

        controls_text = [
            "MOUSE - Steer the aircraft",
            "W / S - Accelerate / Decelerate",
            "LEFT MOUSE BUTTON - Fire primary weapon",
            "LEFT SHIFT - Engage boost",
            "1, 2, 3 - Switch weapon type (Normal, Heavy, Rapid)",
            "TAB - Toggle enhanced radar mode",
            "P - Pause / Resume the game",
            "ESC - Closes the game without saving",
            "",
            "In the pause menu, you can return to the Main Menu (progress is lost)",
            "or quit the application.",
            "",
            "Objective: Shoot down enemy aircraft to score points.",
            "Avoid crashing into buildings and the ground.",
            "Watch your altitude and stay within the city boundaries!"
        ]

        for i, line in enumerate(controls_text):
            draw_text_ex(self.font, line, Vector2(int(sw * 0.1), int(sh * 0.25 + i * (text_font_size * 1.5))),
                         text_font_size, 1, WHITE)

        self.draw_button("BACK", button_rects["back"], 30, hover_states["back"])

    def draw_credits_screen(self, skybox, menu_camera, credits, button_rects, hover_states, link_hover_states, scroll_y, content_height):
        self.draw_rotating_skybox(skybox, menu_camera)
        sw, sh = get_screen_width(), get_screen_height()
        title_font_size = int(80 * sh / 980)
        name_font_size = int(30 * sh / 980)
        text_font_size = int(25 * sh / 980)

        title = "CREDITS"
        title_width = measure_text_ex(self.font, title, title_font_size, 1).x
        draw_text_ex(self.font, title, Vector2(int((sw - title_width) / 2), int(sh * 0.1)), title_font_size, 1, WHITE)

        view_y_start = int(sh * 0.25)
        view_height = int(sh * 0.55)
        
        begin_scissor_mode(0, view_y_start, sw, view_height)

        y_pos_base = view_y_start - int(scroll_y)
        visible_link_index = 0

        for i, credit in enumerate(credits):
            current_y_pos = y_pos_base + i * int(sh * 0.15)
            
            if current_y_pos < view_y_start - (sh*0.15) or current_y_pos > view_y_start + view_height:
                continue

            draw_text_ex(self.font, f"{credit['name']}:", Vector2(int(sw * 0.1), current_y_pos), name_font_size, 1, SKYBLUE)
            draw_text_ex(self.font, credit['reason'], Vector2(int(sw * 0.1 + 20), int(current_y_pos + name_font_size * 1.2)),
                         text_font_size, 1, WHITE)
            
            if credit.get('link'):
                link_y = int(current_y_pos + name_font_size * 1.2 + text_font_size * 1.2)
                
                if link_y > view_y_start and (link_y + text_font_size) < (view_y_start + view_height):
                    is_hovering = False
                    if visible_link_index < len(link_hover_states):
                        is_hovering = link_hover_states[visible_link_index]
                    
                    link_color = ORANGE if is_hovering else YELLOW
                    draw_text_ex(self.font, credit['link'],
                                 Vector2(int(sw * 0.1 + 20), link_y),
                                 text_font_size, 1, link_color)
                    
                    visible_link_index += 1

        end_scissor_mode()

        if content_height > view_height:
            scrollbar_track_rect = Rectangle(sw - 25, float(view_y_start), 15.0, float(view_height))
            draw_rectangle_rec(scrollbar_track_rect, fade(BLACK, 0.5))
            
            handle_height = max(20.0, view_height * (view_height / content_height))
            scroll_range = content_height - view_height
            scroll_percentage = scroll_y / scroll_range if scroll_range > 0 else 0
            
            handle_y = view_y_start + (view_height - handle_height) * scroll_percentage
            
            scrollbar_handle_rect = Rectangle(sw - 25, handle_y, 15.0, handle_height)
            draw_rectangle_rec(scrollbar_handle_rect, fade(SKYBLUE, 0.8))

        self.draw_button("BACK", button_rects["back"], 30, hover_states["back"])

    def draw_pause_menu(self, button_rects, hover_states):
        draw_rectangle(0, 0, get_screen_width(), get_screen_height(), fade(BLACK, 0.7))
        sw, sh = get_screen_width(), get_screen_height()
        title_font_size = int(80 * sh / 980)

        title = "PAUSED"
        title_width = measure_text_ex(self.font, title, title_font_size, 1).x
        draw_text_ex(self.font, title, Vector2(int((sw - title_width) / 2), int(sh / 4)), title_font_size, 1, WHITE)

        self.draw_button("RESUME", button_rects["resume"], 30, hover_states["resume"])
        self.draw_button("MAIN MENU", button_rects["main_menu"], 30, hover_states["main_menu"])
        self.draw_button("QUIT", button_rects["quit"], 30, hover_states["quit"])

    def draw_game_over(self, score, high_score, enemies_defeated, button_rects, hover_states):
        draw_rectangle(0, 0, get_screen_width(), get_screen_height(), fade(BLACK, 0.8))
        sw, sh = get_screen_width(), get_screen_height()

        title_fs = int(120 * sh / 980)
        score_fs = int(50 * sh / 980)
        hs_fs = int(30 * sh / 980)
        enemies_fs = int(40 * sh / 980)

        title = "GAME OVER"
        title_width = measure_text_ex(self.font, title, title_fs, 1).x
        draw_text_ex(self.font, title, Vector2(int((sw - title_width) / 2), int(sh / 4)), title_fs, 1, RED)

        score_text = f"FINAL SCORE: {score}"
        score_width = measure_text_ex(self.font, score_text, score_fs, 1).x
        draw_text_ex(self.font, score_text, Vector2(int((sw - score_width) / 2), int(sh / 2 - score_fs)), score_fs, 1,
                     YELLOW)

        hs_text = f"HIGHEST SCORE: {high_score}"
        hs_width = measure_text_ex(self.font, hs_text, hs_fs, 1).x
        draw_text_ex(self.font, hs_text, Vector2(int((sw - hs_width) / 2), int(sh / 2 + score_fs * 0.5)), hs_fs, 1,
                     SKYBLUE)

        enemies_text = f"ENEMIES DEFEATED: {enemies_defeated}"
        enemies_width = measure_text_ex(self.font, enemies_text, enemies_fs, 1).x
        draw_text_ex(self.font, enemies_text,
                     Vector2(int((sw - enemies_width) / 2), int(sh / 2 + score_fs * 0.5 + hs_fs * 1.5)), enemies_fs,
                     1, WHITE)

        self.draw_button("RESTART", button_rects["restart"], 30, hover_states["restart"])
        self.draw_button("MAIN MENU", button_rects["main_menu"], 30, hover_states["main_menu"])