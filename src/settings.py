from pyray import *
from raylib import *
from math import sin, cos, radians, degrees
from random import randint, uniform, choice
from os.path import join, exists
from custom_timer import Timer

def lerp(a, b, t):
    return a + (b - a) * t

BASE_FOV = 45.0
BOOST_FOV = 60.0
ALTITUDE_WARNING_Y = 12.0
CAMERA_SHAKE_INTENSITY = 0.8
PLAYER_MAX_HEALTH = 200.0

SCREEN_WIDTH, SCREEN_HEIGHT = 1900, 980
MOUSE_SENSITIVITY = 0.003
FPS = 60
FONT_SIZE = 60
FONT_PADDING = 20

DEBUG = False