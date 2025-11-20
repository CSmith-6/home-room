import math
import os
import pygame as p

# Adjust path if you move it: e.g. "assets/sprites/HitAnimation_Plasma_purple.png"
ASSETS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "assets", "sprites"))
EXPLOSION_SPRITE_PATH = os.path.join(ASSETS_DIR, "green_explosion.png")

# Base scale of the static explosion sprite
EXPLOSION_BASE_SCALE = 0.5
# How large the explosion should get relative to its starting scale over its lifetime
EXPLOSION_GROWTH_MULT = 1.0


class PlasmaExplosion:
    """
    Single-frame explosion that grows and pulses to simulate an animated blast.
    """
    _image = None
    _base_w = 0
    _base_h = 0

    @classmethod
    def _load_image(cls):
        if cls._image is not None:
            return

        if not os.path.exists(EXPLOSION_SPRITE_PATH):
            raise FileNotFoundError(f"Explosion sprite not found at {EXPLOSION_SPRITE_PATH}")

        cls._image = p.image.load(EXPLOSION_SPRITE_PATH).convert_alpha()
        cls._base_w, cls._base_h = cls._image.get_size()

    def __init__(self, x, y, base_scale=None):
        PlasmaExplosion._load_image()
        self.x = float(x)
        self.y = float(y)

        # Use current EXPLOSION_BASE_SCALE when caller does not override
        if base_scale is None:
            base_scale = EXPLOSION_BASE_SCALE

        # Timing / animation state
        self.age = 0
        self.max_age = 24  # frames the explosion stays alive

        # Growth and pulse
        self.scale = base_scale
        # Grow toward a target size proportional to starting scale
        target_scale = base_scale * EXPLOSION_GROWTH_MULT
        self.growth_rate = (target_scale - self.scale) / self.max_age if self.max_age else 0.0
        self.pulse_t = 0.0
        self.pulse_speed = 0.45
        self.pulse_amp = 0.25  # how much the pulse changes scale

        # Alpha fade
        self.base_alpha = 230

    @property
    def done(self):
        return self.age >= self.max_age

    def update(self):
        if self.done:
            return

        self.age += 1
        self.scale += self.growth_rate
        self.pulse_t += self.pulse_speed

    def draw(self, screen):
        if self.done:
            return

        # Compute pulsing scale and fading alpha
        pulse_scale = 1.0 + self.pulse_amp * math.sin(self.pulse_t)
        # Avoid collapsing to zero, but allow small scales
        total_scale = max(0.01, self.scale * pulse_scale)

        fade = max(0.0, 1.0 - (self.age / self.max_age))
        flash = 0.65 + 0.35 * (0.5 + 0.5 * math.sin(self.pulse_t * 1.6))
        alpha = int(self.base_alpha * fade * flash)

        w = max(1, int(self._base_w * total_scale))
        h = max(1, int(self._base_h * total_scale))
        frame = p.transform.smoothscale(self._image, (w, h))
        frame.set_alpha(alpha)

        rect = frame.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(frame, rect)
