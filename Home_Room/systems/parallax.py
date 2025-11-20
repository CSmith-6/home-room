import pygame as p
import math
import random

SKY_BLUE   = (50, 90, 140)
DEEP_WATER = (10, 40, 80)
MID_WATER  = (20, 70, 120)
SURF_WATER = (40, 110, 170)


class ParallaxLayer:
    def __init__(self, surface, speed, y):
        self.surface = surface
        self.speed = speed
        self.y = y
        self.width = surface.get_width()
        self.x1 = 0
        self.x2 = self.width

    def update(self, scroll_speed):
        dx = self.speed * scroll_speed
        self.x1 -= dx
        self.x2 -= dx

        if self.x1 <= -self.width:
            self.x1 = self.x2 + self.width
        if self.x2 <= -self.width:
            self.x2 = self.x1 + self.width
        if self.x1 >= self.width:
            self.x1 = self.x2 - self.width
        if self.x2 >= self.width:
            self.x2 = self.x1 - self.width

    def draw(self, screen):
        screen.blit(self.surface, (int(self.x1), int(self.y)))
        screen.blit(self.surface, (int(self.x2), int(self.y)))


def make_island_layer(width, height):
    surf = p.Surface((width, height), p.SRCALPHA)
    surf.fill(SKY_BLUE)
    horizon_y = int(height * 0.55)
    p.draw.rect(surf, (40, 70, 110), (0, horizon_y, width, height - horizon_y))

    for _ in range(6):
        base_x = random.randint(0, width - 200)
        base_y = horizon_y + random.randint(10, 40)
        w = random.randint(120, 260)
        h = random.randint(30, 90)
        pts = [
            (base_x, base_y),
            (base_x + w//3, base_y - h),
            (base_x + 2*w//3, base_y - h//2),
            (base_x + w, base_y),
        ]
        p.draw.polygon(surf, (25, 60, 40), pts)
    return surf


def make_water_layer(width, height, color, amp=12, wave_len=180):
    surf = p.Surface((width, height), p.SRCALPHA)
    surf.fill(color)
    pts = []
    for x in range(0, width + 1, 10):
        y = amp * math.sin(2 * math.pi * x / wave_len)
        pts.append((x, y))
    pts.append((width, height))
    pts.append((0, height))
    p.draw.polygon(surf, color, pts)
    return surf
