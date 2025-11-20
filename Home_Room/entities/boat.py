import pygame as p
import math
import os
import random
from entities.turret import Turret

GRAY  = (120, 120, 130)
DARK_GRAY = (60, 60, 70)
LIGHT_GRAY = (200, 200, 210)

# Ship durability
SHIP_MAX_HEALTH = 6
ASSETS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "assets", "sprites"))
FLAME_SPRITE_PATH = os.path.join(ASSETS_DIR, "0_Fire_Flame_1280x720.png")  # sprite sheet (PNG)
FLAME_SHEET_COLS = 5  # adjust to match your sheet layout
FLAME_SHEET_ROWS = 2  # adjust to match your sheet layout
FLAME_ANIM_SPEED = 0.25  # frames advanced per update tick


def _make_default_flame_surface():
    """Fallback flame sprite (simple painted flame) if no art is available."""
    surf = p.Surface((36, 54), p.SRCALPHA)
    p.draw.polygon(surf, (255, 150, 40), [(6, 50), (18, 6), (30, 50)])
    p.draw.polygon(surf, (255, 210, 90), [(12, 40), (18, 14), (24, 40)])
    p.draw.polygon(surf, (255, 240, 150), [(16, 34), (18, 20), (20, 34)])
    return surf


def _load_flame_frames():
    """
    Load and slice a flame sprite sheet into frames.
    Expects a sheet laid out in FLAME_SHEET_COLS x FLAME_SHEET_ROWS grid.
    """
    candidates = [
        os.path.join(ASSETS_DIR, "0_Fire_Flame_1280x720.png"),
        os.path.join(ASSETS_DIR, "0_Fire_Flame_1280x720.gif"),
        os.path.join(ASSETS_DIR, "0_Fire_Flame_1280x720.mp4"),
    ]
    for path in candidates:
        if not os.path.exists(path):
            continue
        try:
            sheet = p.image.load(path).convert_alpha()
            w, h = sheet.get_size()
            cols = max(1, FLAME_SHEET_COLS)
            rows = max(1, FLAME_SHEET_ROWS)
            frame_w = w // cols
            frame_h = h // rows
            frames = []
            for r in range(rows):
                for c in range(cols):
                    rect = p.Rect(c * frame_w, r * frame_h, frame_w, frame_h)
                    frames.append(sheet.subsurface(rect))
            return frames or [_make_default_flame_surface()]
        except Exception:
            continue
    return [_make_default_flame_surface()]


# Loaded lazily after display init to avoid convert_alpha() errors before set_mode
_FLAME_FRAMES_CACHE = None


def get_flame_frames():
    global _FLAME_FRAMES_CACHE
    if _FLAME_FRAMES_CACHE is None:
        _FLAME_FRAMES_CACHE = _load_flame_frames()
    return _FLAME_FRAMES_CACHE


class FlameEmitter:
    """Small flame that flickers based on ship damage."""
    def __init__(self, offset):
        self.offset = offset
        self.t = random.random() * 10
        self.active = False
        self.world_pos = (0, 0)
        self.frame_t = 0.0

    def update(self, ship_x, ship_y):
        self.world_pos = (ship_x + self.offset[0], ship_y + self.offset[1])
        self.t += 0.25
        self.frame_t += FLAME_ANIM_SPEED

    def draw(self, screen):
        if not self.active:
            return
        frames = get_flame_frames()
        if not frames:
            return
        # pulse size and alpha
        scale = 0.45 + 0.35 * (0.5 + 0.5 * math.sin(self.t * 2.6))
        alpha_pulse = 0.65 + 0.35 * (0.5 + 0.5 * math.sin(self.t * 3.8))
        base_frame = frames[int(self.frame_t) % len(frames)]
        w = max(6, int(base_frame.get_width() * scale * 0.08))
        h = max(8, int(base_frame.get_height() * scale * 0.08))
        frame = p.transform.smoothscale(base_frame, (w, h))
        frame.set_alpha(int(220 * alpha_pulse))
        rect = frame.get_rect(center=(int(self.world_pos[0]), int(self.world_pos[1])))
        screen.blit(frame, rect)

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
        self.max_health = SHIP_MAX_HEALTH
        self.health = self.max_health
        self.recently_hit_timer = 0  # brief flash indicator when hit
        self.flames = [
            FlameEmitter((-40, -10)),
            FlameEmitter((0, -18)),
            FlameEmitter((40, -10))
        ]

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
        if self.recently_hit_timer > 0:
            self.recently_hit_timer -= 1

        # Flames increase as health drops
        ratio = self.health_ratio
        active_count = 0
        if ratio <= 0.85:
            active_count = 1
        if ratio <= 0.55:
            active_count = 2
        if ratio <= 0.30:
            active_count = 3

        for idx, f in enumerate(self.flames):
            f.active = idx < active_count
            f.update(self.x, self.current_y - self.height * 0.15)

    def take_damage(self, amount: float):
        if self.health <= 0:
            return False
        self.health = max(0, self.health - amount)
        self.recently_hit_timer = 10
        return True

    @property
    def is_dead(self):
        return self.health <= 0

    @property
    def health_ratio(self):
        return max(0.0, min(1.0, self.health / self.max_health if self.max_health else 0))

    def draw(self, screen):
        hit_flash = min(1.0, self.recently_hit_timer / 10) if self.recently_hit_timer > 0 else 0
        hull_color = (
            min(255, int(GRAY[0] + 70 * hit_flash)),
            min(255, int(GRAY[1] + 70 * hit_flash)),
            min(255, int(GRAY[2] + 70 * hit_flash))
        )

        hull = p.Rect(0,0,self.width,self.height)
        hull.center = (self.x,self.current_y)
        p.draw.rect(screen,hull_color,hull)
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

        for f in self.flames:
            f.draw(screen)

        for t in self.turrets:
            t.draw(screen)
