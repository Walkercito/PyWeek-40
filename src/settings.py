from pyray import *
from raylib import *
from math import sin, cos, radians, degrees, sqrt
from random import randint, uniform, choice
from os.path import join, exists
from custom_timer import Timer
from enum import Enum

def lerp(a, b, t):
    return a + (b - a) * t

GRID_CELL_SIZE = 150.0

BASE_FOV = 45.0
BOOST_FOV = 60.0
ALTITUDE_WARNING_Y = 12.0
CAMERA_SHAKE_INTENSITY = 0.8
PLAYER_MAX_HEALTH = 200.0

BOUNDARY_DAMAGE_START = 15.0
BOUNDARY_DAMAGE_SCALING = 0.5

CITY_RADIUS = 450.0 
BUILDING_COUNT = 100
MIN_DISTANCE_FROM_CENTER = 5.0
MIN_BUILDING_DISTANCE = 35.0

SCREEN_WIDTH, SCREEN_HEIGHT = 1900, 980
MOUSE_SENSITIVITY = 0.003
FPS = 60
FONT_SIZE = 60
FONT_PADDING = 20

DEBUG = False