from pyray import *
from raylib import *
from math import sin, cos, radians
from random import randint, uniform, choice
from os.path import join, exists
from custom_timer import Timer

SCREEN_WIDTH, SCREEN_HEIGHT = 1900, 980
MOUSE_SENSITIVITY = 0.003
FPS = 60
FONT_SIZE = 60
FONT_PADDING = 20