import pygame as p
import random
import math
from entities.plane_bullet import PlaneBullet

RED = (220, 70, 70)
WHITE = (230, 230, 240)


class Plane:
    def __init__(self):
        self.x = 1500
        self.y = random.randint(80, 260)
        self.speed = random.uniform(2.5, 4.0)
        self.radius = 20
        self.alive = True

        # shooting
        self.fire_cooldown = random.randint(60, 120)  # frames until first shot
        self.base_cooldown_min = 60
        self.base_cooldown_max = 120

    def update(self):
        self.x -= self.speed
        if self.x < -200:
            self.alive = False

        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1

    def try_fire(self, ship):
        """
        Returns a PlaneBullet or None.
        Shooting style: aim in general direction of ship with random spread.
        """
        if not self.alive:
            return None
        if self.fire_cooldown > 0:
            return None

        # Only shoot if ship is somewhere to the left (ahead)
        if ship.x < self.x + 50:
            # angle towards ship
            dx = ship.x - self.x
            dy = ship.current_y - self.y
            base_angle = math.degrees(math.atan2(dy, dx))

            # Option B: general direction, not perfect aim
            spread = 15  # degrees of randomness
            shot_angle = base_angle + random.uniform(-spread, spread)

            # Set cooldown for next shot
            self.fire_cooldown = random.randint(self.base_cooldown_min, self.base_cooldown_max)

            # Spawn bullet slightly in front of plane nose
            spawn_x = self.x - 20
            spawn_y = self.y
            return PlaneBullet(spawn_x, spawn_y, shot_angle)

        return None

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

        p.draw.rect(screen, WHITE,
                    (body.centerx - 6, body.top + 2, 12, body.height - 4), 1)
