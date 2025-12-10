import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import random
import math
import array

# --- CONFIGURATION ---
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800
FOV_ANGLE = 60
TARGET_DISTANCE = 1000 

# --- COLORS ---
COLOR_CYAN_GLASS = (0.2, 1.0, 1.0, 0.4)
COLOR_CYAN_SOLID = (0.0, 1.0, 1.0, 1.0)
COLOR_RED = (1.0, 0.1, 0.1, 1.0)
COLOR_YELLOW = (1.0, 1.0, 0.0, 1.0)
COLOR_GREEN = (0.1, 1.0, 0.1, 1.0)
COLOR_PURPLE = (0.8, 0.2, 1.0, 1.0)
COLOR_BLUE = (0.2, 0.2, 1.0, 1.0)
COLOR_WHITE = (1.0, 1.0, 1.0, 1.0)

# --- GLOBAL TEXTURES ---
TEX_EARTH = None
TEX_MOON = None
TEX_ALIEN = None
hud_cache = {"text": "", "tex_id": None, "w": 0, "h": 0}

# --- SOUND MANAGER ---
class SoundManager:
    def __init__(self):
        # Buffer size adjusted for responsiveness
        pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
        self.sounds = {}
        self._generate_sounds()

    def _generate_sounds(self):
        def make_sound(freq_start, freq_end, duration, volume=0.5, type='square'):
            n_samples = int(44100 * duration)
            buf = array.array('h', [0] * n_samples)
            amplitude = 32767 * volume
            for i in range(n_samples):
                t = i / 44100.0
                progress = i / n_samples
                freq = freq_start + (freq_end - freq_start) * progress
                if type == 'square':
                    val = 1 if (int(t * freq * 2) % 2) else -1
                elif type == 'noise':
                    val = random.uniform(-1, 1)
                else:
                    val = 0
                buf[i] = int(val * amplitude * (1 - progress)) 
            return pygame.mixer.Sound(buffer=buf)

        self.sounds['laser'] = make_sound(800, 400, 0.15, 0.3, 'square')
        self.sounds['enemy_laser'] = make_sound(600, 300, 0.15, 0.3, 'square')
        self.sounds['explosion'] = make_sound(0, 0, 0.3, 0.5, 'noise')
        self.sounds['powerup'] = make_sound(1000, 2000, 0.4, 0.4, 'square')
        self.sounds['hit'] = make_sound(200, 100, 0.2, 0.5, 'noise')

    def play(self, name):
        if name in self.sounds:
            self.sounds[name].play()

# --- TEXTURE LOADING ---
def load_texture(path):
    try:
        surf = pygame.image.load(path).convert_alpha()
    except:
        # Fallback generated textures if files are missing
        surf = pygame.Surface((64, 64))
        surf.fill((255, 0, 255)) 
        if "alien" in path: pygame.draw.circle(surf, (0,255,0), (32,32), 20)
        if "earth" in path: surf.fill((0, 0, 255)); pygame.draw.circle(surf, (0,200,0), (32,32), 15)
        if "moon" in path: surf.fill((0, 0, 0)); pygame.draw.circle(surf, (200,200,200), (32,32), 28)
    
    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    w, h = surf.get_width(), surf.get_height()
    data = pygame.image.tostring(surf, "RGBA", 1)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    return tex_id

def create_text_texture(text, font):
    surf = font.render(text, True, (255, 255, 255))
    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    w, h = surf.get_width(), surf.get_height()
    # FIX: Changed flip from 1 to 0 (False) to prevent upside down text
    data = pygame.image.tostring(surf, "RGBA", 0)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    return tex_id, w, h

# --- DRAWING HELPERS ---

def draw_sprite(tex_id, x, y, z, size, alpha=1.0, color_tint=(1,1,1)):
    glDisable(GL_LIGHTING)
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(color_tint[0], color_tint[1], color_tint[2], alpha)
    glPushMatrix()
    glTranslatef(x, y, z)
    s = size / 2.0
    glBegin(GL_QUADS)
    glTexCoord2f(0, 1); glVertex3f(-s, -s, 0)
    glTexCoord2f(1, 1); glVertex3f(s, -s, 0)
    glTexCoord2f(1, 0); glVertex3f(s, s, 0)
    glTexCoord2f(0, 0); glVertex3f(-s, s, 0)
    glEnd()
    glPopMatrix()
    glDisable(GL_TEXTURE_2D)
    glEnable(GL_LIGHTING)

def draw_hud_2d(score, distance, hp, powerup_name, font, game_state):
    global hud_cache
    
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    if game_state == "GAME_OVER":
        current_text = "SYSTEM FAILURE - PRESS 'R' TO RESTART"
    elif game_state == "FINISHED":
        current_text = "MISSION ACCOMPLISHED"
    else:
        current_text = f"SCORE: {int(score)}   DIST: {int(distance)}/{TARGET_DISTANCE}   HP: {int(hp)}%   SYSTEM: {powerup_name}"
    
    if current_text != hud_cache["text"]:
        if hud_cache["tex_id"]: glDeleteTextures([hud_cache["tex_id"]])
        tex, w, h = create_text_texture(current_text, font)
        hud_cache["text"] = current_text
        hud_cache["tex_id"] = tex
        hud_cache["w"] = w
        hud_cache["h"] = h
    
    tex = hud_cache["tex_id"]
    w, h = hud_cache["w"], hud_cache["h"]

    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, tex)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(1, 1, 1, 1)

    if game_state in ["GAME_OVER", "FINISHED"]:
        x, y = (SCREEN_WIDTH - w)//2, SCREEN_HEIGHT//2
    else:
        x, y = 20, SCREEN_HEIGHT - 50

    # Ensure consistent texture mapping
    glBegin(GL_QUADS)
    glTexCoord2f(0, 1); glVertex2f(x, y)          
    glTexCoord2f(1, 1); glVertex2f(x + w, y)
    glTexCoord2f(1, 0); glVertex2f(x + w, y + h)
    glTexCoord2f(0, 0); glVertex2f(x, y + h)
    glEnd()

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glDisable(GL_TEXTURE_2D) 

def draw_ship(x, y, z, tilt, shield_active):
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(tilt, 0, 0, 1)
    glRotatef(-90, 1, 0, 0)

    glDisable(GL_LIGHTING)
    glDisable(GL_TEXTURE_2D) 
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    top, bl, br, back = (0, 2, 0), (-1.2, -1.5, 1), (1.2, -1.5, 1), (0, -0.5, -1)
    faces = [[top, bl, br], [top, bl, back], [top, br, back], [bl, br, back]]

    glColor4f(*COLOR_CYAN_GLASS)
    glBegin(GL_TRIANGLES)
    for f in faces: 
        for v in f: glVertex3fv(v)
    glEnd()

    glLineWidth(2)
    glColor4f(*COLOR_CYAN_SOLID)
    for f in faces:
        glBegin(GL_LINE_LOOP)
        for v in f: glVertex3fv(v)
        glEnd()

    if shield_active:
        glColor4f(0.8, 0.2, 1.0, 0.3)
        quad = gluNewQuadric()
        gluSphere(quad, 3.5, 16, 16)

    glDisable(GL_BLEND)
    glEnable(GL_LIGHTING)
    glPopMatrix()

# --- MENU DRAWING (OpenGL 2D Overlay) ---
def draw_menu_gl(font, mouse_pos):
    """Draws the Pause Menu and returns the ID of the clicked button."""
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Semi-transparent Background
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0, 0, 0, 0.7)
    glBegin(GL_QUADS)
    glVertex2f(0, 0); glVertex2f(SCREEN_WIDTH, 0)
    glVertex2f(SCREEN_WIDTH, SCREEN_HEIGHT); glVertex2f(0, SCREEN_HEIGHT)
    glEnd()

    btn_w, btn_h = 240, 50
    cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
    
    # In OpenGL 2D with gluOrtho2D(0,W,0,H), Y=0 is bottom. 
    # Pygame mouse Y=0 is top. We must invert Pygame Y.
    inv_mouse_y = SCREEN_HEIGHT - mouse_pos[1]
    
    buttons = [
        {"text": "RESUME", "rect": (cx - btn_w/2, cy + 60, btn_w, btn_h), "id": "RESUME"},
        {"text": "RESTART LEVEL", "rect": (cx - btn_w/2, cy, btn_w, btn_h), "id": "LEVEL"},
        {"text": "RESTART GAME", "rect": (cx - btn_w/2, cy - 60, btn_w, btn_h), "id": "GAME"},
        {"text": "QUIT", "rect": (cx - btn_w/2, cy - 120, btn_w, btn_h), "id": "QUIT"}
    ]
    
    clicked_id = None
    mouse_click = pygame.mouse.get_pressed()[0]

    for btn in buttons:
        x, y, w, h = btn["rect"]
        hover = (x < mouse_pos[0] < x + w) and (y < inv_mouse_y < y + h)
        
        # Draw Button Body
        if hover: glColor4f(0.3, 0.8, 0.3, 1.0)
        else: glColor4f(0.2, 0.6, 0.2, 1.0)
        
        glBegin(GL_QUADS)
        glVertex2f(x, y); glVertex2f(x + w, y)
        glVertex2f(x + w, y + h); glVertex2f(x, y + h)
        glEnd()
        
        # Draw Border
        glLineWidth(2)
        glColor4f(1, 1, 1, 1)
        glBegin(GL_LINE_LOOP)
        glVertex2f(x, y); glVertex2f(x + w, y)
        glVertex2f(x + w, y + h); glVertex2f(x, y + h)
        glEnd()
        
        # Draw Text
        surf = font.render(btn["text"], True, (255, 255, 255))
        text_w, text_h = surf.get_width(), surf.get_height()
        
        # Create temporary texture
        # FIX: flip=0 (False) ensures text is upright
        tex_data = pygame.image.tostring(surf, "RGBA", 0)
        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, text_w, text_h, 0, GL_RGBA, GL_UNSIGNED_BYTE, tex_data)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        
        glEnable(GL_TEXTURE_2D)
        glColor4f(1,1,1,1)
        # Center text in button
        tx = x + (w - text_w)/2
        ty = y + (h - text_h)/2
        
        glBegin(GL_QUADS)
        # Map Texture Coordinates so (0,0) is Top-Left to match upright Pygame data
        glTexCoord2f(0, 1); glVertex2f(tx, ty)                # Bottom Left
        glTexCoord2f(1, 1); glVertex2f(tx + text_w, ty)       # Bottom Right
        glTexCoord2f(1, 0); glVertex2f(tx + text_w, ty + text_h) # Top Right
        glTexCoord2f(0, 0); glVertex2f(tx, ty + text_h)       # Top Left
        glEnd()
        glDisable(GL_TEXTURE_2D)
        glDeleteTextures([tex_id])

        if hover and mouse_click:
            clicked_id = btn["id"]

    # Restore State
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    
    return clicked_id

# --- ENTITIES ---

class PowerUpDrop:
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z
        self.type = random.choice(["SHIELD", "REFLECT", "LASER", "SLOW"])
        self.active = True
        self.rot = 0
        
        if self.type == "SHIELD": self.color = COLOR_PURPLE
        elif self.type == "REFLECT": self.color = COLOR_BLUE
        elif self.type == "LASER": self.color = COLOR_GREEN
        elif self.type == "SLOW": self.color = COLOR_YELLOW

    def update(self, speed_mod):
        self.z += 0.3 * speed_mod 
        self.rot += 5
        self.y = self.y * 0.95 # Magnetic gravity to align with player
        if self.z > 10: self.active = False 

    def draw(self):
        glDisable(GL_LIGHTING)
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.rot, 1, 1, 0)
        glColor4f(*self.color)
        
        s = 0.5
        glBegin(GL_QUADS)
        glVertex3f(-s,-s,s); glVertex3f(s,-s,s); glVertex3f(s,s,s); glVertex3f(-s,s,s)
        glVertex3f(-s,-s,-s); glVertex3f(-s,s,-s); glVertex3f(s,s,-s); glVertex3f(s,-s,-s)
        glEnd()
        glPopMatrix()
        glEnable(GL_LIGHTING)

class Bullet:
    def __init__(self, x, y, z, is_laser=False):
        self.x, self.y, self.z = x, y, z
        self.is_laser = is_laser
        self.active = True
        self.pierce = 3 if is_laser else 1

    def update(self, speed_mod=1.0):
        speed = 4.0 if self.is_laser else 1.5
        self.z -= speed 
        if self.z < -150: self.active = False

    def draw(self):
        glDisable(GL_LIGHTING)
        glLineWidth(4 if self.is_laser else 2)
        glBegin(GL_LINES)
        
        if self.is_laser:
            glColor4f(*COLOR_GREEN)
            glVertex3f(self.x, self.y, self.z)
            glVertex3f(self.x, self.y, self.z + 10) 
        else:
            glColor4f(*COLOR_YELLOW)
            glVertex3f(self.x, self.y, self.z)
            glVertex3f(self.x, self.y, self.z + 3)
            
        glEnd()
        glEnable(GL_LIGHTING)

class EnemyBullet:
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z
        self.active = True
        self.vz = 0.8 
        self.reflected = False

    def update(self, speed_mod):
        self.z += self.vz * speed_mod
        if self.z > 20 or self.z < -100: self.active = False

    def draw(self):
        glDisable(GL_LIGHTING)
        glLineWidth(2)
        glBegin(GL_LINES)
        if self.reflected:
            glColor4f(*COLOR_BLUE) 
        else:
            glColor4f(*COLOR_RED)  
        glVertex3f(self.x, self.y, self.z)
        glVertex3f(self.x, self.y, self.z - 2)
        glEnd()
        glEnable(GL_LIGHTING)

class Enemy:
    def __init__(self, delay, behavior_type):
        self.active = True
        self.start_delay = delay
        self.frame = 0
        self.behavior = behavior_type
        self.hp = 1
        
        if self.behavior == "KAMIKAZE":
            base_x = random.choice([-30, 30])
            offset_x = random.uniform(-5, 5) 
            self.x = base_x + offset_x
            self.y = random.uniform(-10, 10)
            self.z = -120
            self.color = (1.0, 0.2, 0.2) 
            
        elif self.behavior == "HELIX":
            self.angle = random.uniform(0, 6.28)
            self.radius = 25
            self.x, self.y = 0, 0
            self.z = -150 - random.uniform(0, 20) 
            self.color = (0.2, 1.0, 0.2) 
            
        elif self.behavior == "STALKER":
            self.x = 0
            self.y = 5
            self.z = -100
            self.dest_x = 0
            self.color = (1.0, 1.0, 0.0) 
            self.hp = 3 

    def update(self, speed_mod, enemy_bullets, audio, player_x):
        self.frame += 1 * speed_mod
        if self.frame < self.start_delay: return

        if self.behavior == "KAMIKAZE":
            self.z += 1.2 * speed_mod
            self.x += (player_x - self.x) * 0.05 * speed_mod
            self.y = math.sin(self.frame * 0.2) * 2

        elif self.behavior == "HELIX":
            self.z += 0.4 * speed_mod
            self.angle += 0.05 * speed_mod
            self.x = math.cos(self.angle) * self.radius
            self.y = math.sin(self.angle) * self.radius

        elif self.behavior == "STALKER":
            if self.z < -40:
                self.z += 1.5 * speed_mod
            else:
                self.z = -40 + math.sin(self.frame * 0.1) * 5
                self.x += (player_x - self.x) * 0.03 * speed_mod
        
        shoot_chance = 0.01
        if self.behavior == "STALKER": shoot_chance = 0.05 
        
        if self.z > -100 and self.z < -10 and random.random() < shoot_chance * speed_mod:
            enemy_bullets.append(EnemyBullet(self.x, self.y, self.z))
            audio.play('enemy_laser')

        if self.z > 20: self.active = False

    def draw(self):
        if self.frame < self.start_delay: return
        glPushMatrix()
        
        if self.behavior == "KAMIKAZE":
            glTranslatef(self.x, self.y, self.z)
            glRotatef((self.x * -2), 0, 0, 1) 
        elif self.behavior == "HELIX":
            glTranslatef(self.x, self.y, self.z)
            glRotatef(self.frame * 5, 0, 0, 1) 
        else:
            glTranslatef(self.x, self.y, self.z)

        glDisable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, TEX_ALIEN)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        glColor4f(self.color[0], self.color[1], self.color[2], 1.0)
        s = 5.0 / 2.0
        glBegin(GL_QUADS)
        glTexCoord2f(0, 1); glVertex3f(-s, -s, 0)
        glTexCoord2f(1, 1); glVertex3f(s, -s, 0)
        glTexCoord2f(1, 0); glVertex3f(s, s, 0)
        glTexCoord2f(0, 0); glVertex3f(-s, s, 0)
        glEnd()
        
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_LIGHTING)
        glPopMatrix()

class Particle:
    def __init__(self, x, y, z, color):
        self.x, self.y, self.z = x, y, z
        self.color = color
        self.vel = [random.uniform(-0.5,0.5) for _ in range(3)]
        self.life = 1.0
    def update(self):
        self.x += self.vel[0]; self.y += self.vel[1]; self.z += self.vel[2]
        self.life -= 0.04
        return self.life > 0
    def draw(self):
        glDisable(GL_LIGHTING)
        glColor4f(self.color[0], self.color[1], self.color[2], self.life)
        glPointSize(3)
        glBegin(GL_POINTS)
        glVertex3f(self.x, self.y, self.z)
        glEnd()
        glEnable(GL_LIGHTING)

# --- GAME RUNNER ---

def run_game():
    global TEX_EARTH, TEX_MOON, TEX_ALIEN, hud_cache
    pygame.init()
    display = (SCREEN_WIDTH, SCREEN_HEIGHT)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Galaga 3D: Ultimate")
    
    font = pygame.font.SysFont("Arial", 24, bold=True)
    audio = SoundManager()

    gluPerspective(FOV_ANGLE, (display[0]/display[1]), 0.1, 500.0)
    gluLookAt(0, 25, 20, 0, 0, -15, 0, 1, 0)

    glEnable(GL_LIGHTING); glEnable(GL_LIGHT0); glEnable(GL_COLOR_MATERIAL)
    glLightfv(GL_LIGHT0, GL_POSITION, (50, 50, 50, 1.0))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (1, 1, 1, 1))

    TEX_EARTH = load_texture("assets/images/earth_sprite.png")
    TEX_MOON = load_texture("assets/images/moon_sprite.png")
    TEX_ALIEN = load_texture("assets/images/alien_sprite.png")

    while True: # LEVEL RESTART LOOP
        
        def reset_game():
            return {
                "player_x": 0, "player_z": 0, "player_tilt": 0,
                "player_hp": 100, "score": 0, "distance": 0,
                "bullets": [], "enemy_bullets": [], "enemies": [],
                "powerups": [], "particles": [],
                "stars": [[random.uniform(-100, 100), random.uniform(-20, 50), random.uniform(-200, 50)] for _ in range(400)],
                "active_powerup": "NONE", "powerup_timer": 0,
                "game_state": "DEPARTURE", "spawn_timer": 0,
                "earth_y": -40, "earth_scale": 120,
                "moon_alpha": 0.0, "moon_scale": 10.0,
                "landing_progress": 0
            }

        state = reset_game()
        clock = pygame.time.Clock()
        paused = False

        while True: # MAIN GAME LOOP
            for event in pygame.event.get():
                if event.type == pygame.QUIT: 
                    return "QUIT"
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_m:
                        paused = not paused
                    
                    if not paused:
                        if state["game_state"] in ["DEPARTURE", "COMBAT", "APPROACH"]:
                            if event.key == pygame.K_SPACE: 
                                state["bullets"].append(Bullet(state["player_x"], 0, 0, is_laser=(state["active_powerup"] == "LASER")))
                                audio.play('laser')
                        
                        if state["game_state"] in ["FINISHED", "GAME_OVER"]:
                            if event.key == pygame.K_r:
                                break # Restarts Level
            
            if paused:
                # Clear and Draw Static Scene for Background
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                glDisable(GL_LIGHTING); glPointSize(1); glBegin(GL_POINTS); glColor3f(1, 1, 1)
                for s in state["stars"]: glVertex3f(s[0], s[1], s[2])
                glEnd(); glEnable(GL_LIGHTING)
                if state["game_state"] == "DEPARTURE": draw_sprite(TEX_EARTH, 0, state["earth_y"], -80, state["earth_scale"])
                draw_ship(state["player_x"], 0, state["player_z"], state["player_tilt"], (state["active_powerup"] == "SHIELD"))
                
                # Draw Menu
                action = draw_menu_gl(font, pygame.mouse.get_pos())
                
                if action == "RESUME":
                    paused = False
                    pygame.time.wait(200)
                elif action == "LEVEL":
                    break # Breaks inner loop -> Restarts Level
                elif action == "GAME":
                    return "RESTART_GAME"
                elif action == "QUIT":
                    return "QUIT"
                
                pygame.display.flip()
                clock.tick(60)
                continue

            # --- GAME UPDATE ---

            if state["game_state"] == "FINISHED":
                pygame.time.wait(3000)
                return "NEXT"

            speed_mod = 1.0 
            if state["active_powerup"] != "NONE":
                state["powerup_timer"] -= 1
                if state["active_powerup"] == "SLOW": speed_mod = 0.25 
                if state["powerup_timer"] <= 0: state["active_powerup"] = "NONE"

            if state["game_state"] == "DEPARTURE":
                state["earth_y"] -= 0.5 * speed_mod
                state["earth_scale"] -= 0.2 * speed_mod
                if state["earth_y"] < -220: state["game_state"] = "COMBAT"

            if state["game_state"] == "COMBAT":
                state["distance"] += 1 * speed_mod
                state["spawn_timer"] += 1
                
                spawn_limit = 100 if state["active_powerup"] != "SLOW" else 400
                
                if state["spawn_timer"] > spawn_limit:
                    state["spawn_timer"] = 0
                    wave_type = random.choice(["KAMIKAZE", "HELIX", "STALKER"])
                    
                    if wave_type == "KAMIKAZE":
                        for i in range(3): 
                            state["enemies"].append(Enemy(delay=i*20, behavior_type="KAMIKAZE"))
                    elif wave_type == "HELIX":
                        for i in range(5):
                            state["enemies"].append(Enemy(delay=i*10, behavior_type="HELIX"))
                    elif wave_type == "STALKER":
                        state["enemies"].append(Enemy(delay=0, behavior_type="STALKER"))
                
                if state["distance"] >= TARGET_DISTANCE:
                    state["enemies"], state["enemy_bullets"], state["powerups"] = [], [], [] 
                    state["game_state"] = "APPROACH"

            if state["game_state"] == "APPROACH":
                state["distance"] += 1
                state["moon_alpha"] += 0.005
                state["moon_scale"] += 0.2
                if state["moon_alpha"] >= 1.0 and state["moon_scale"] >= 80: state["game_state"] = "LANDING"

            if state["game_state"] == "LANDING":
                state["player_x"] *= 0.95
                state["player_tilt"] *= 0.9
                state["player_z"] -= 0.5
                state["landing_progress"] += 1
                if state["landing_progress"] > 200: state["game_state"] = "FINISHED"

            if state["player_hp"] <= 0:
                state["game_state"] = "GAME_OVER"

            if state["game_state"] in ["DEPARTURE", "COMBAT", "APPROACH"]:
                keys = pygame.key.get_pressed()
                target_tilt = 0
                if keys[K_LEFT] and state["player_x"] > -22: 
                    state["player_x"] -= 0.6 * speed_mod; target_tilt = 30
                if keys[K_RIGHT] and state["player_x"] < 22: 
                    state["player_x"] += 0.6 * speed_mod; target_tilt = -30
                state["player_tilt"] += (target_tilt - state["player_tilt"]) * 0.1

            for b in state["bullets"]: b.update()
            for eb in state["enemy_bullets"]: 
                eb.update(speed_mod)
                if state["active_powerup"] == "REFLECT" and not eb.reflected:
                    if eb.z > -10 and eb.z < 5 and abs(eb.x - state["player_x"]) < 4:
                        eb.reflected = True
                        eb.vz = -1.5 
                        audio.play('powerup') 

            for e in state["enemies"]: 
                e.update(speed_mod, state["enemy_bullets"], audio, state["player_x"])
                
            for p in state["powerups"]: p.update(speed_mod)
            for par in state["particles"]: 
                if not par.update(): state["particles"].remove(par)

            # --- COLLISIONS ---
            
            for p in state["powerups"][:]:
                if not p.active: continue
                if math.sqrt((p.x-state["player_x"])**2 + (p.z-0)**2) < 3.0:
                    p.active = False
                    state["active_powerup"] = p.type
                    state["powerup_timer"] = 600
                    state["score"] += 50
                    audio.play('powerup')

            for eb in state["enemy_bullets"][:]:
                if not eb.active: continue
                if eb.reflected:
                    for e in state["enemies"][:]:
                        if not e.active: continue
                        if math.sqrt((e.x-eb.x)**2 + (e.z-eb.z)**2) < 3.5:
                            e.active = False; eb.active = False; state["score"] += 200
                            for _ in range(8): state["particles"].append(Particle(e.x, e.y, e.z, COLOR_BLUE))
                            audio.play('explosion')
                            break
                else:
                    if math.sqrt((eb.x-state["player_x"])**2 + (eb.z-0)**2) < 2.0:
                        eb.active = False
                        if state["active_powerup"] != "SHIELD": 
                            state["player_hp"] -= 10
                            audio.play('hit')
                            for _ in range(10): state["particles"].append(Particle(state["player_x"], 0, 0, COLOR_RED))

            for e in state["enemies"][:]:
                if not e.active: continue
                if state["active_powerup"] == "SHIELD":
                    if math.sqrt((e.x-state["player_x"])**2 + (e.z-0)**2) < 5.0:
                        e.active = False; state["score"] += 50
                        for _ in range(8): state["particles"].append(Particle(e.x, e.y, e.z, COLOR_PURPLE))
                        audio.play('explosion')
                        continue

                for b in state["bullets"][:]:
                    if not b.active: continue
                    if math.sqrt((e.x-b.x)**2 + (e.z-b.z)**2) < 2.5:
                        e.active = False; state["score"] += 100
                        if random.random() < 0.1: state["powerups"].append(PowerUpDrop(e.x, e.y, e.z))
                        
                        if b.is_laser:
                            b.pierce -= 1
                            if b.pierce <= 0: b.active = False
                        else:
                            b.active = False
                        
                        for _ in range(8): state["particles"].append(Particle(e.x, e.y, e.z, COLOR_RED))
                        audio.play('explosion')
                        break
                
                if e.active and math.sqrt((e.x-state["player_x"])**2 + (e.z-0)**2) < 3:
                    e.active = False
                    if state["active_powerup"] != "SHIELD":
                        state["player_hp"] -= 20
                        audio.play('hit')
                        for _ in range(15): state["particles"].append(Particle(state["player_x"], 0, 0, COLOR_CYAN_SOLID))

            state["bullets"] = [b for b in state["bullets"] if b.active]
            state["enemy_bullets"] = [b for b in state["enemy_bullets"] if b.active]
            state["enemies"] = [e for e in state["enemies"] if e.active]
            state["powerups"] = [p for p in state["powerups"] if p.active]

            # --- DRAWING ---
            glClearColor(0.0, 0.0, 0.05, 1)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            glDisable(GL_LIGHTING); glPointSize(1); glBegin(GL_POINTS); glColor3f(1, 1, 1)
            for s in state["stars"]:
                s[2] += 2.0 * speed_mod
                if s[2] > 20: s[2] = -200
                glVertex3f(s[0], s[1], s[2])
            glEnd(); glEnable(GL_LIGHTING)

            if state["game_state"] == "DEPARTURE":
                draw_sprite(TEX_EARTH, 0, state["earth_y"], -80, state["earth_scale"])
            if state["game_state"] in ["APPROACH", "LANDING", "FINISHED"]:
                a = min(1.0, state["moon_alpha"]) if state["game_state"] == "APPROACH" else 1.0
                draw_sprite(TEX_MOON, 0, 0, -80, state["moon_scale"], alpha=a)

            if state["game_state"] not in ["FINISHED", "GAME_OVER"]:
                draw_ship(state["player_x"], 0, state["player_z"], state["player_tilt"], (state["active_powerup"] == "SHIELD"))
            
            for e in state["enemies"]: e.draw()
            for eb in state["enemy_bullets"]: eb.draw()
            for b in state["bullets"]: b.draw()
            for p in state["powerups"]: p.draw()
            for par in state["particles"]: par.draw()

            draw_hud_2d(state["score"], state["distance"], state["player_hp"], state["active_powerup"], font, state["game_state"])

            pygame.display.flip()
            clock.tick(60)

if __name__ == "__main__":
    run_game()