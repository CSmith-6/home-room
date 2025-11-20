import pygame as p

WHITE = (255, 255, 255)

class Prism:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 3.0
        self.target_x = 950
        self.done = False

    def update(self):
        if self.x > self.target_x:
            self.x -= self.speed
        else:
            self.done = True

    def draw(self, screen):
        pts = [
            (self.x, self.y - 40),
            (self.x - 40, self.y + 40),
            (self.x + 40, self.y + 40),
        ]
        p.draw.polygon(screen, WHITE, pts)
        p.draw.polygon(screen, (180,220,255), pts, 3)
