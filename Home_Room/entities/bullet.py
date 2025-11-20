import pygame as p
import math

YELLOW = (245, 230, 120)

class Bullet:
    def __init__(self, x, y, angle, speed=12, radius=4):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed
        self.radius = radius
        self.alive = True

    def update(self):
        rad = math.radians(self.angle)
        self.x += self.speed * math.cos(rad)
        self.y += self.speed * math.sin(rad)

        if self.x < -50 or self.x > 1500 or self.y < -50 or self.y > 800:
            self.alive = False

    def draw(self, screen):
        p.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), self.radius)
