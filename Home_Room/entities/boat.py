import pygame as p
import math
from entities.turret import Turret

GRAY  = (120, 120, 130)
DARK_GRAY = (60, 60, 70)
LIGHT_GRAY = (200, 200, 210)

class Battleship:
    def __init__(self, x, y):
        self.x = float(x)
        self.y_base = float(y)
        self.width = 260
        self.height = 44
        self.rock_phase = 0
        self.controls_enabled = True
        self.move_speed = 4
        self.min_x = self.width*0.4
        self.max_x = 1400 - self.width*0.4
        self.min_y = 600 - 210
        self.max_y = 600 - 110
        off = -20
        self.turrets = [
            Turret(self.x - 70, self.y_base + off),
            Turret(self.x + 70, self.y_base + off)
        ]
        self.current_y = self.y_base

    def handle_movement(self, keys):
        if not self.controls_enabled:
            return
        dx = (keys[p.K_d] - keys[p.K_a]) * self.move_speed
        dy = (keys[p.K_s] - keys[p.K_w]) * self.move_speed * 0.7
        self.x = min(self.max_x, max(self.min_x, self.x + dx))
        self.y_base = min(self.max_y, max(self.min_y, self.y_base + dy))

    def auto_move_to(self, tx, ty):
        speed = 2.5
        dx = tx - self.x
        dy = ty - self.y_base
        if abs(dx) > 1: self.x += speed * (1 if dx>0 else -1)
        else: self.x = tx
        if abs(dy) > 1: self.y_base += speed * 0.6 * (1 if dy>0 else -1)
        else: self.y_base = ty
        return abs(dx)<1 and abs(dy)<1

    def rotate_turrets(self, delta):
        if not self.controls_enabled:
            return
        for t in self.turrets:
            t.rotate(delta)

    def update(self):
        self.rock_phase += 0.03
        self.current_y = self.y_base + math.sin(self.rock_phase)*4
        for i,t in enumerate(self.turrets):
            off = -70 if i==0 else 70
            t.x = self.x + off
            t.y = self.current_y - 20
            t.update()

    def draw(self, screen):
        hull = p.Rect(0,0,self.width,self.height)
        hull.center = (self.x,self.current_y)
        p.draw.rect(screen,GRAY,hull)
        p.draw.rect(screen,DARK_GRAY,hull,3)
        bow = [
            (hull.right, hull.centery-self.height//2),
            (hull.right+50, hull.centery),
            (hull.right, hull.centery+self.height//2)
        ]
        p.draw.polygon(screen,GRAY,bow)
        p.draw.polygon(screen,DARK_GRAY,bow,2)

        tower = p.Rect(0,0,80,55)
        tower.center = (hull.centerx-20, hull.top-25)
        p.draw.rect(screen,GRAY,tower)
        p.draw.rect(screen,DARK_GRAY,tower,2)
        p.draw.line(screen,DARK_GRAY, (tower.centerx,tower.top),(tower.centerx,tower.top-35),4)

        for t in self.turrets:
            t.draw(screen)
