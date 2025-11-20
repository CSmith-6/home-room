import pygame as p
import math
from entities.bullet import Bullet

DARK_GRAY  = (60, 60, 70)
LIGHT_GRAY = (200, 200, 210)

class Turret:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.radius = 18
        self.barrel_length = 55
        self.angle = -90
        self.min_angle = -160
        self.max_angle = -20
        self.cooldown = 0
        self.cooldown_max = 18

    def rotate(self, delta):
        self.angle += delta
        self.angle = max(self.min_angle, min(self.max_angle, self.angle))

    def can_fire(self):
        return self.cooldown <= 0

    def fire(self):
        self.cooldown = self.cooldown_max
        rad = math.radians(self.angle)
        tip_x = self.x + self.barrel_length * math.cos(rad)
        tip_y = self.y + self.barrel_length * math.sin(rad)
        return Bullet(tip_x, tip_y, self.angle)

    def update(self):
        if self.cooldown > 0:
            self.cooldown -= 1

    def draw(self, screen):
        p.draw.circle(screen, DARK_GRAY, (int(self.x), int(self.y)), self.radius)
        p.draw.circle(screen, LIGHT_GRAY, (int(self.x), int(self.y)), self.radius, 2)
        rad = math.radians(self.angle)
        tip_x = self.x + self.barrel_length * math.cos(rad)
        tip_y = self.y + self.barrel_length * math.sin(rad)
        p.draw.line(screen, LIGHT_GRAY, (int(self.x), int(self.y)), (int(tip_x), int(tip_y)), 4)
