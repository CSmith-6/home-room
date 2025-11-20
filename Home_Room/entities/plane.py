import pygame as p
import random

RED = (220, 70, 70)
WHITE = (230, 230, 240)

class Plane:
    def __init__(self):
        self.x = 1500
        self.y = random.randint(80, 260)
        self.speed = random.uniform(2.5, 4.0)
        self.radius = 20
        self.alive = True

    def update(self):
        self.x -= self.speed
        if self.x < -200:
            self.alive = False

    def draw(self, screen):
        body = p.Rect(0, 0, 52, 14)
        body.center = (self.x, self.y)
        p.draw.rect(screen, RED, body)

        nose = [
            (body.left - 14, body.centery),
            (body.left, body.top),
            (body.left, body.bottom)
        ]
        p.draw.polygon(screen, RED, nose)

        p.draw.rect(screen, WHITE, (body.centerx-6, body.top+2, 12, body.height-4), 1)
