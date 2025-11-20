import pygame as p
import math
import os

# Adjust this if you move the asset (e.g. "assets/sprites/PlasmaBulletSprite_purple.png")
ASSETS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "assets", "sprites"))
BULLET_SPRITE_PATH = os.path.join(ASSETS_DIR, "PlasmaBulletSprite_purple.png")

# Scale factor to enlarge the bullet sprite
BULLET_SCALE = 0.3
# Damage dealt to the ship per hit (override in level code if needed)
PLANE_BULLET_DAMAGE = 1



class PlaneBullet:
    """
    Plasma bullet fired by enemy planes.
    Uses a single-frame sprite and applies a pulsing scale effect in code.
    """
    _sheet = None
    _frames = []
    _frame_w = 0
    _frame_h = 0

    @classmethod
    def _load_frames(cls):
        if cls._sheet is not None:
            return

        if not os.path.exists(BULLET_SPRITE_PATH):
            raise FileNotFoundError(f"Bullet sprite not found at {BULLET_SPRITE_PATH}")

        cls._sheet = p.image.load(BULLET_SPRITE_PATH).convert_alpha()
        base_w, base_h = cls._sheet.get_size()
        cls._frame_w = int(base_w * BULLET_SCALE)
        cls._frame_h = int(base_h * BULLET_SCALE)

        frame = cls._sheet
        if BULLET_SCALE != 1.0:
            frame = p.transform.smoothscale(frame, (cls._frame_w, cls._frame_h))
        cls._frames = [frame]

    def __init__(self, x, y, angle_deg, speed=8.0):
        PlaneBullet._load_frames()
        self.x = float(x)
        self.y = float(y)
        self.angle = angle_deg
        self.speed = speed
        self.alive = True

        # Pulse animation state
        self.pulse_t = 0.0
        self.pulse_speed = 0.25
        self.pulse_amp = 0.18
        self.pulse_min = 0.8
        self.pulse_scale = 1.0

        # radius for simple collision (updated each frame with pulse scale)
        self.base_radius = max(self._frame_w, self._frame_h) * 0.6
        self.radius = self.base_radius

    def update(self):
        # movement
        rad = math.radians(self.angle)
        self.x += self.speed * math.cos(rad)
        self.y += self.speed * math.sin(rad)

        # kill if off screen-ish
        if (self.x < -100 or self.x > 1500 or
                self.y < -100 or self.y > 800):
            self.alive = False

        # pulse animation (scale up/down smoothly)
        self.pulse_t += self.pulse_speed
        pulse = 1.0 + self.pulse_amp * math.sin(self.pulse_t)
        self.pulse_scale = max(self.pulse_min, pulse)
        self.radius = self.base_radius * self.pulse_scale

    def draw(self, screen):
        frame = self._frames[0]

        # Apply pulsing scale before rotation
        if self.pulse_scale != 1.0:
            target_w = max(1, int(self._frame_w * self.pulse_scale))
            target_h = max(1, int(self._frame_h * self.pulse_scale))
            frame = p.transform.smoothscale(frame, (target_w, target_h))

        # rotate sprite so it points along motion direction
        rotated = p.transform.rotate(frame, -self.angle)
        rect = rotated.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(rotated, rect)
