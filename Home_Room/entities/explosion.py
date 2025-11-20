import pygame as p

RED    = (220, 70, 70)
ORANGE = (250, 160, 60)
YELLOW = (255, 220, 120)

class Explosion:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.timer = 0
        self.max_timer = 24

    @property
    def done(self):
        return self.timer >= self.max_timer

    def update(self):
        self.timer += 1

    def draw(self, screen):
        t = self.timer
        r = 6 + t * 2
        alpha = max(0, 255 - t * 10)
        for i, col in enumerate((RED, ORANGE, YELLOW)):
            surf = p.Surface((r*2, r*2), p.SRCALPHA)
            c = (*col, alpha)
            p.draw.circle(surf, c, (r, r), max(1, r - i*3), 2)
            screen.blit(surf, (self.x - r, self.y - r))
