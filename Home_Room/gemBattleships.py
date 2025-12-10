import pygame as p
import math
import random
import os

# --- Constants & Configuration ---
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
WATER_BLUE = (0, 105, 148)
DEEP_WATER = (0, 50, 100)
SKY_BLUE = (135, 206, 235)
STORM_SKY = (50, 50, 80)
MTN_GREY = (100, 100, 100)
MTN_FAR = (150, 150, 180)
SHIP_GREY = (80, 80, 80)
ALIEN_GREEN = (57, 255, 20)
PLASMA_PURPLE = (255, 0, 255)
ORANGE = (255, 165, 0)
RED = (255, 0, 0)
MINE_RED = (200, 0, 0)
BUTTON_COLOR = (50, 200, 50)
BUTTON_HOVER = (70, 220, 70)
MENU_BG = (30, 30, 40, 200) # Dark semi-transparent for menu

# Power Up Colors
PWR_SHIELD = (0, 255, 255) 
PWR_BEAM = (255, 255, 0)   
PWR_SHOCK = (200, 0, 200)  

# Game Settings
TOTAL_DISTANCE_TO_PRISM = 7500  
STORM_DISTANCE = 3500           
AURA_FADE_START = 2000          

# --- Helper Functions ---

def deg2Rad(deg):
    return (deg / 180.0) * math.pi

def getDist(x0, y0, x1, y1):
    dist = (x1 - x0)**2 + (y1 - y0)**2
    return int(math.sqrt(dist))

# --- Classes ---

class Bullet:
    def __init__(self, x, y, angle_deg, is_player_bullet, damage=0, size_mod=1.0):
        self.x = x
        self.y = y
        self.radius = int(5 * size_mod) if is_player_bullet else 8
        self.heading = angle_deg
        self.velocity = 15 if is_player_bullet else 8
        self.is_player = is_player_bullet
        self.exists = True
        self.damage = damage if damage > 0 else 5 
        self.is_revenge = (damage > 20) 
        
    def move(self):
        angRad = deg2Rad(self.heading)
        self.x += self.velocity * math.cos(angRad)
        self.y += self.velocity * math.sin(angRad)
        
        if (self.x < -100 or self.x > SCREEN_WIDTH + 100 or 
            self.y < -100 or self.y > SCREEN_HEIGHT + 100):
            self.exists = False

    def draw(self, surface):
        color = ORANGE if self.is_player else PLASMA_PURPLE
        if self.is_revenge: color = (0, 255, 255) 
        
        p.draw.circle(surface, color, (int(self.x), int(self.y)), self.radius)
        if not self.is_player or self.is_revenge:
            p.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.radius // 2)

class Explosion:
    def __init__(self, x, y, type_str):
        self.x = x
        self.y = y
        self.life = 20
        self.max_life = 20
        self.type = type_str 
        
    def update(self):
        self.life -= 1
        return self.life > 0

    def draw(self, surface):
        progress = self.life / self.max_life
        radius = int(30 * (1 - progress))
        
        if self.type == 'mechanical':
            c = (255, int(165 * progress), 0)
            p.draw.circle(surface, c, (int(self.x), int(self.y)), radius)
            p.draw.circle(surface, (100,100,100), (int(self.x), int(self.y)), int(radius*0.7), 2)
        elif self.type == 'organic':
            c = (50, 255, 50)
            p.draw.circle(surface, c, (int(self.x), int(self.y)), radius)
            p.draw.circle(surface, PLASMA_PURPLE, (int(self.x), int(self.y)), int(radius*0.5), 2)
        elif self.type == 'shockwave':
            r = int(720 * (1 - progress)) 
            s = p.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), p.SRCALPHA)
            p.draw.circle(s, (200, 0, 200, int(100 * progress)), (int(self.x), int(self.y)), r, 20)
            surface.blit(s, (0,0))

class PowerUp:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 15
        self.type = random.choice(['shield', 'beam', 'shockwave'])
        self.rect = p.Rect(x - 15, y - 15, 30, 30)
        
    def update(self, scroll_speed):
        self.y += 3 
        self.rect.topleft = (self.x - 15, self.y - 15)
        return self.y < SCREEN_HEIGHT + 50 and self.x > -50

    def draw(self, surface):
        color = WHITE
        label = "?"
        if self.type == 'shield': 
            color = PWR_SHIELD
            label = "S"
        elif self.type == 'beam': 
            color = PWR_BEAM
            label = "B"
        elif self.type == 'shockwave': 
            color = PWR_SHOCK
            label = "W"
            
        p.draw.circle(surface, color, (int(self.x), int(self.y)), self.radius)
        p.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.radius, 2)
        
        font_obj = p.font.SysFont("Arial", 20, bold=True)
        txt = font_obj.render(label, True, BLACK)
        surface.blit(txt, (self.x - txt.get_width()//2, self.y - txt.get_height()//2))

class Turret:
    def __init__(self, mount_x_offset, mount_y_offset, length):
        self.mount_x = mount_x_offset 
        self.mount_y = mount_y_offset
        self.len = length
        self.angle = 0 
        self.tip_x = 0
        self.tip_y = 0
        self.world_x = 0
        self.world_y = 0

    def update(self, ship_x, ship_y, angle_deg):
        self.world_x = ship_x + self.mount_x
        self.world_y = ship_y + self.mount_y
        self.angle = angle_deg
        
        rads = deg2Rad(self.angle)
        self.tip_x = self.world_x + self.len * math.cos(rads)
        self.tip_y = self.world_y + self.len * math.sin(rads)

    def draw(self, surface):
        p.draw.circle(surface, (50, 50, 50), (int(self.world_x), int(self.world_y)), 10)
        p.draw.line(surface, (30, 30, 30), 
                    (self.world_x, self.world_y), 
                    (self.tip_x, self.tip_y), 6)

class Battleship:
    def __init__(self):
        self.width = 150
        self.height = 50
        self.x = 100
        self.y = SCREEN_HEIGHT - 120
        self.speed = 6
        self.rect = p.Rect(self.x, self.y, self.width, self.height)
        self.turrets = [
            Turret(-40, -20, 35),
            Turret(40, -20, 35)
        ]
        self.health = 100
        self.turret_angle = -45 
        
        self.shoot_cooldown = 0
        self.shoot_delay = 10 
        
        self.shield_active = False
        self.shield_hp = 0
        self.shield_accumulated_dmg = 0
        
        self.beam_active = False
        self.beam_timer = 0
        
    def move(self, keys, scroll_speed_boost):
        water_top = SCREEN_HEIGHT - 250
        water_bottom = SCREEN_HEIGHT - self.height
        
        if keys[p.K_w] and self.y > water_top: 
            self.y -= self.speed
        if keys[p.K_s] and self.y < water_bottom:
            self.y += self.speed
        if keys[p.K_a] and self.x > 0:
            self.x -= self.speed
        if keys[p.K_d] and self.x < SCREEN_WIDTH - self.width:
            self.x += self.speed
        
        self.rect.topleft = (self.x, self.y)
        
        if keys[p.K_LEFT]:
            self.turret_angle -= 3
        if keys[p.K_RIGHT]:
            self.turret_angle += 3
            
        is_pushing = False
        if self.x >= SCREEN_WIDTH - self.width - 20:
            is_pushing = True
            
        return is_pushing

    def update_turrets(self):
        for t in self.turrets:
            t.update(self.rect.centerx, self.rect.centery, self.turret_angle)

    def update_powerups(self):
        if self.beam_active:
            self.beam_timer -= 1
            if self.beam_timer <= 0:
                self.beam_active = False
        
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def take_damage(self, amount):
        if self.shield_active:
            self.shield_hp -= amount
            self.shield_accumulated_dmg += amount
            if self.shield_hp <= 0:
                self.shield_active = False
                return "revenge" 
            return None
        else:
            self.health -= amount
            return None

    def draw(self, surface):
        p.draw.rect(surface, SHIP_GREY, self.rect)
        p.draw.rect(surface, (100,100,100), (self.x + 15, self.y - 12, self.width - 30, 12))
        p.draw.rect(surface, (60,60,60), (self.x + 50, self.y - 30, 40, 18))
        
        for t in self.turrets:
            t.draw(surface)
            
        if self.beam_active:
            for t in self.turrets:
                end_x = t.tip_x + 2000 * math.cos(deg2Rad(t.angle))
                end_y = t.tip_y + 2000 * math.sin(deg2Rad(t.angle))
                p.draw.line(surface, PWR_BEAM, (t.tip_x, t.tip_y), (end_x, end_y), 4)

        if self.shield_active:
            p.draw.circle(surface, (0, 255, 255), self.rect.center, 90, 3)

        p.draw.rect(surface, RED, (self.x, self.y - 50, self.width, 6))
        health_pct = max(0, self.health / 100)
        p.draw.rect(surface, (0, 255, 0), (self.x, self.y - 50, self.width * health_pct, 6))

class Alien:
    sprite_image = None 

    def __init__(self):
        self.width = 90
        self.height = 60
        self.x = SCREEN_WIDTH + random.randint(10, 300)
        self.y = random.randint(50, int(SCREEN_HEIGHT * 0.6)) 
        self.speed = random.randint(4, 7)
        self.rect = p.Rect(self.x, self.y, self.width, self.height)
        self.shoot_timer = 0
        self.shoot_delay = random.randint(60, 180)

        if Alien.sprite_image is None:
            sprite_path = "assets/images/alien_sprite.png"
            if os.path.exists(sprite_path):
                try:
                    img = p.image.load(sprite_path).convert_alpha()
                    Alien.sprite_image = p.transform.scale(img, (self.width, self.height))
                except:
                    Alien.sprite_image = "FAILED"
            else:
                Alien.sprite_image = "FAILED"

    def update(self, scroll_speed):
        self.x -= (self.speed + scroll_speed)
        self.y += math.sin(p.time.get_ticks() * 0.005) * 2
        self.rect.topleft = (self.x, self.y)
        
        self.shoot_timer += 1
        if self.shoot_timer >= self.shoot_delay:
            self.shoot_timer = 0
            return True
        return False

    def draw(self, surface):
        if Alien.sprite_image and Alien.sprite_image != "FAILED":
            surface.blit(Alien.sprite_image, (self.x, self.y))
        else:
            p.draw.ellipse(surface, ALIEN_GREEN, self.rect)
            p.draw.circle(surface, (200, 255, 200), self.rect.center, 18) 

class Mine:
    def __init__(self):
        self.radius = 15
        self.x = SCREEN_WIDTH + random.randint(10, 200)
        water_top = SCREEN_HEIGHT - 220
        water_bottom = SCREEN_HEIGHT - 40
        self.y = random.randint(water_top, water_bottom)
        self.rect = p.Rect(self.x - self.radius, self.y - self.radius, self.radius*2, self.radius*2)
        
    def update(self, scroll_speed):
        self.x -= scroll_speed
        self.rect.topleft = (self.x - self.radius, self.y - self.radius)
        self.y += math.sin(p.time.get_ticks() * 0.008) * 0.5
        
    def draw(self, surface):
        p.draw.circle(surface, MINE_RED, (int(self.x), int(self.y)), self.radius)
        for i in range(0, 360, 45):
            rad = deg2Rad(i)
            sx = self.x + (self.radius + 5) * math.cos(rad)
            sy = self.y + (self.radius + 5) * math.sin(rad)
            p.draw.line(surface, (100, 0, 0), (self.x, self.y), (sx, sy), 3)

class MountainLayer:
    def __init__(self, color, height_min, height_max, speed_factor, y_base):
        self.color = color
        self.speed_factor = speed_factor
        self.points = []
        self.width = SCREEN_WIDTH + 100
        self.y_base = y_base
        
        x = 0
        while x < self.width * 2:
            h = random.randint(height_min, height_max)
            self.points.append([x, y_base - h])
            x += random.randint(30, 80)
        
        self.points.append([self.width*2, SCREEN_HEIGHT])
        self.points.append([0, SCREEN_HEIGHT])

    def update(self, scroll_speed):
        move = scroll_speed * self.speed_factor
        for pnt in self.points:
            pnt[0] -= move
            
        if self.points[0][0] < -100:
            first = self.points.pop(0)
            last_x = self.points[-3][0]
            new_h = random.randint(50, 250)
            self.points.insert(-2, [last_x + random.randint(40, 100), self.y_base - new_h])
            self.points[-2][0] = self.points[-3][0] 
            self.points[-1][0] = self.points[0][0]  

    def draw(self, surface):
        p.draw.polygon(surface, self.color, self.points)

class Prism:
    def __init__(self):
        self.x = SCREEN_WIDTH + 100
        self.y = 300
        self.visible = False
        self.angle = 0
        self.size = 120
        self.beam_active = False 
    
    def update(self, cinematic_active, phase="ARRIVE"):
        self.angle += 1
        
        if phase == "DEPART":
            self.y -= 5 
            return

        if cinematic_active:
            self.y = 300 + math.sin(p.time.get_ticks() * 0.002) * 30
            if phase == "ARRIVE":
                target_x = SCREEN_WIDTH - 400
                if self.x > target_x:
                    self.x -= 3
                elif self.x < target_x:
                    self.x += 3
            
    def draw_beam(self, surface, target_x, target_y):
        s = p.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), p.SRCALPHA)
        px, py = self.x, self.y
        points = [
            (px, py), 
            (target_x - 30, target_y), 
            (target_x + 30, target_y)  
        ]
        p.draw.polygon(s, (0, 255, 255, 100), points) 
        p.draw.line(s, (200, 255, 255, 200), (px, py), (target_x, target_y), 2) 
        surface.blit(s, (0,0))

    def draw(self, surface):
        if not self.visible: return
        h = self.size
        w = self.size * 0.8
        
        points_3d = [[0, -h, 0], [-w, h, -w], [w, h, -w], [0, h, w]]
        faces = [(0, 1, 2), (0, 2, 3), (0, 3, 1), (1, 2, 3)]

        angle_rad = math.radians(self.angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        surf_size = int(self.size * 3)
        temp_surf = p.Surface((surf_size, surf_size), p.SRCALPHA)
        cx, cy = surf_size // 2, surf_size // 2

        projected_points = []
        for pt in points_3d:
            rx = pt[0] * cos_a - pt[2] * sin_a
            rz = pt[0] * sin_a + pt[2] * cos_a
            ry = pt[1]
            projected_points.append((cx + rx, cy + ry))

        fill_color = (0, 255, 255, 100) 
        edge_color = (200, 255, 255, 255) 

        for face in faces:
            poly_pts = [projected_points[i] for i in face]
            p.draw.polygon(temp_surf, fill_color, poly_pts)
            p.draw.polygon(temp_surf, edge_color, poly_pts, 3) 

        surface.blit(temp_surf, (self.x - cx, self.y - cy))

class Soldier:
    sprite_image = None
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 90  
        self.height = 90 
        self.visible = False
        
        if Soldier.sprite_image is None:
            sprite_path = "assets/images/soldier_ascend.png"
            if os.path.exists(sprite_path):
                try:
                    img = p.image.load(sprite_path).convert_alpha()
                    scaled_img = p.transform.scale(img, (self.width, self.height))
                    Soldier.sprite_image = p.transform.rotate(scaled_img, 25)
                except:
                    Soldier.sprite_image = "FAILED"
            else:
                Soldier.sprite_image = "FAILED"

    def move_towards(self, target_x, target_y, speed):
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist < speed:
            self.x = target_x
            self.y = target_y
            return True 
        else:
            self.x += (dx/dist) * speed
            self.y += (dy/dist) * speed
            return False

    def draw(self, surface):
        if not self.visible: return
        
        if Soldier.sprite_image and Soldier.sprite_image != "FAILED":
            rect = Soldier.sprite_image.get_rect(center=(self.x, self.y))
            surface.blit(Soldier.sprite_image, rect.topleft)
        else:
            p.draw.rect(surface, (255, 255, 0), (self.x - 10, self.y - 20, 20, 40))


# --- Main Game Function ---

def run_game():
    p.init()
    p.mixer.init() 
    
    screen = p.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    p.display.set_caption("Battleship Voyage")
    clock = p.time.Clock()
    font = p.font.SysFont("Arial", 24)
    menu_font = p.font.SysFont("Arial", 40, bold=True)
    
    # Audio
    music_path = "assets/music/Joel Eriksson - Battlefield 1942 Theme (Original 2021 Version).mp3"
    aura_path = "assets/music/Jay Sosaki - Super Saiyan (DBS) Aura Sound Effect Extended.mp3"
    aura_sound = None
    aura_channel = None

    if os.path.exists(music_path):
        try:
            p.mixer.music.load(music_path)
            p.mixer.music.play(-1)
            p.mixer.music.set_volume(1.0)
        except: pass
    
    if os.path.exists(aura_path):
        try:
            aura_sound = p.mixer.Sound(aura_path)
            aura_channel = aura_sound.play(loops=-1)
            if aura_channel: aura_channel.set_volume(0.0)
        except: pass

    # Pause Menu Buttons
    btn_w, btn_h = 300, 60
    cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
    
    btn_resume = p.Rect(cx - btn_w//2, cy - 100, btn_w, btn_h)
    btn_restart_lvl = p.Rect(cx - btn_w//2, cy - 20, btn_w, btn_h)
    btn_restart_game = p.Rect(cx - btn_w//2, cy + 60, btn_w, btn_h)
    btn_quit = p.Rect(cx - btn_w//2, cy + 140, btn_w, btn_h)

    while True: # --- OUTER LOOP: Restarts the Level ---
        
        # Initialize Game Data (Reset Level)
        game_data = {
            "player": Battleship(),
            "aliens": [],
            "mines": [],
            "bullets": [],
            "explosions": [],
            "powerups": [],
            "prism": Prism(),
            "soldier": Soldier(0,0),
            "mtn_far": MountainLayer(MTN_FAR, 200, 400, 0.2, SCREEN_HEIGHT - 200),
            "mtn_near": MountainLayer(MTN_GREY, 100, 300, 0.5, SCREEN_HEIGHT - 150),
            "distance": 0,
            "state": "TRAVEL", 
            "storm": 0,
            "cin_phase": "ARRIVE", 
            "cin_timer": 0
        }

        running = True
        paused = False
        
        # Audio Volume Reset
        if p.mixer.music.get_busy(): p.mixer.music.set_volume(1.0)
        if aura_channel: aura_channel.set_volume(0.0)

        while running: # --- INNER LOOP: Frame Updates ---
            events = p.event.get()
            mouse_pos = p.mouse.get_pos()
            
            for event in events:
                if event.type == p.QUIT:
                    return "QUIT"
                
                if event.type == p.KEYDOWN:
                    if event.key == p.K_m: # Toggle Pause
                        paused = not paused
                        if paused: 
                            p.mixer.music.pause()
                            if aura_channel: aura_channel.pause()
                        else: 
                            p.mixer.music.unpause()
                            if aura_channel: aura_channel.unpause()

                # Menu Clicks
                if paused and event.type == p.MOUSEBUTTONDOWN:
                    if btn_resume.collidepoint(mouse_pos):
                        paused = False
                        p.mixer.music.unpause()
                        if aura_channel: aura_channel.unpause()
                    elif btn_restart_lvl.collidepoint(mouse_pos):
                        running = False # Break inner loop, will restart outer loop
                    elif btn_restart_game.collidepoint(mouse_pos):
                        return "RESTART_GAME"
                    elif btn_quit.collidepoint(mouse_pos):
                        return "QUIT"
            
            if paused:
                # --- DRAW PAUSE MENU ---
                # Draw the game behind the menu first (optional, or just overlay)
                # For simplicity, we just draw the overlay on top of whatever was there
                overlay = p.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), p.SRCALPHA)
                overlay.fill(MENU_BG)
                screen.blit(overlay, (0,0))
                
                buttons = [
                    (btn_resume, "RESUME"),
                    (btn_restart_lvl, "RESTART LEVEL"),
                    (btn_restart_game, "RESTART GAME"),
                    (btn_quit, "QUIT")
                ]
                
                for btn, text in buttons:
                    color = BUTTON_HOVER if btn.collidepoint(mouse_pos) else BUTTON_COLOR
                    p.draw.rect(screen, color, btn)
                    p.draw.rect(screen, WHITE, btn, 2)
                    
                    txt_surf = menu_font.render(text, True, BLACK)
                    screen.blit(txt_surf, (btn.centerx - txt_surf.get_width()//2, btn.centery - txt_surf.get_height()//2))
                
                p.display.flip()
                clock.tick(30) # Low framerate for menu
                continue # Skip game logic

            # --- GAME LOGIC (Only runs if not paused) ---
            
            player = game_data["player"]
            prism = game_data["prism"]
            soldier = game_data["soldier"]
            base_scroll_speed = 3
            current_scroll_speed = base_scroll_speed
            keys = p.key.get_pressed()

            # 1. TRAVEL STATE
            if game_data["state"] == "TRAVEL":
                is_pushing = player.move(keys, current_scroll_speed)
                if is_pushing:
                    current_scroll_speed = 9 
                
                game_data["distance"] += current_scroll_speed
                player.update_turrets() 
                player.update_powerups()
                
                # Shooting
                if keys[p.K_SPACE]:
                    if not player.beam_active and player.shoot_cooldown <= 0:
                        for t in player.turrets:
                            b = Bullet(t.tip_x, t.tip_y, t.angle, True)
                            game_data["bullets"].append(b)
                        player.shoot_cooldown = player.shoot_delay

                # Manual Power Ups (For testing/cheats if desired, kept from original)
                if keys[p.K_1]: 
                    player.shield_active = True; player.shield_hp = 50
                if keys[p.K_2]: 
                    player.beam_active = True; player.beam_timer = FPS * 5
                
                # Beam Logic
                if player.beam_active:
                    aim_rad = deg2Rad(player.turret_angle)
                    for list_name, obj_type in [("aliens", 'organic'), ("mines", 'mechanical')]:
                        for obj in game_data[list_name][:]:
                            dx = obj.rect.centerx - player.rect.centerx
                            dy = obj.rect.centery - player.rect.centery
                            dist = math.sqrt(dx*dx + dy*dy)
                            angle_to_obj = math.atan2(dy, dx)
                            diff = abs(angle_to_obj - aim_rad)
                            while diff > math.pi: diff -= 2*math.pi
                            while diff < -math.pi: diff += 2*math.pi
                            if abs(diff) < 0.2 and dist < 2000:
                                 game_data["explosions"].append(Explosion(obj.rect.centerx, obj.rect.centery, obj_type))
                                 game_data[list_name].remove(obj)

                # Spawning
                if random.randint(0, 100) < 2:
                    game_data["aliens"].append(Alien())
                if random.randint(0, 200) < 2: 
                    game_data["mines"].append(Mine())

            # 2. CINEMATIC STATE
            elif game_data["state"] == "CINEMATIC":
                current_scroll_speed = 0
                cin_phase = game_data["cin_phase"]
                
                if cin_phase == "ARRIVE":
                    target_x = 300
                    arrived = True
                    if player.x < target_x: player.x += 2; arrived = False
                    if player.x > target_x: player.x -= 2; arrived = False
                    
                    target_y = SCREEN_HEIGHT - 200
                    if player.y < target_y: player.y += 1; arrived = False
                    if player.y > target_y: player.y -= 1; arrived = False
                        
                    player.rect.topleft = (player.x, player.y)
                    player.update_turrets() 
                    prism.update(True, "ARRIVE")
                    
                    if arrived and abs(prism.x - (SCREEN_WIDTH - 400)) < 10:
                        game_data["cin_phase"] = "WAIT"
                        game_data["cin_timer"] = FPS * 2 
                
                elif cin_phase == "WAIT":
                    prism.update(True, "WAIT")
                    game_data["cin_timer"] -= 1
                    if game_data["cin_timer"] <= 0:
                        game_data["cin_phase"] = "BEAM_UP"
                        soldier.x = player.rect.centerx
                        soldier.y = player.rect.centery
                        soldier.visible = True
                        
                elif cin_phase == "BEAM_UP":
                    prism.update(True, "WAIT")
                    prism.beam_active = True
                    arrived = soldier.move_towards(prism.x, prism.y, 2.0) 
                    
                    if arrived:
                        soldier.visible = False 
                        prism.beam_active = False
                        game_data["cin_phase"] = "DEPART_WAIT"
                        game_data["cin_timer"] = FPS * 1 
                        
                elif cin_phase == "DEPART_WAIT":
                    prism.update(True, "WAIT")
                    game_data["cin_timer"] -= 1
                    if game_data["cin_timer"] <= 0:
                         game_data["cin_phase"] = "DEPART"
                
                elif cin_phase == "DEPART":
                    prism.update(True, "DEPART")
                    if prism.y < -200:
                        return "NEXT" # <--- EXIT TO NEXT GAME

            # Environment & Audio
            remaining = TOTAL_DISTANCE_TO_PRISM - game_data["distance"]
            if remaining <= 0 and game_data["state"] != "CINEMATIC":
                game_data["state"] = "CINEMATIC"
                prism.visible = True
                game_data["aliens"].clear()
                game_data["mines"].clear()
                game_data["powerups"].clear()
                player.beam_active = False
                player.shield_active = False

            is_stormy = remaining < STORM_DISTANCE and remaining > 0
            if is_stormy:
                game_data["storm"] = min(game_data["storm"] + 1, 150)
            else:
                game_data["storm"] = max(game_data["storm"] - 1, 0)
            
            if p.mixer.music.get_busy():
                if remaining < STORM_DISTANCE and remaining > 0:
                    vol = remaining / STORM_DISTANCE
                    p.mixer.music.set_volume(max(0.0, vol))
                elif game_data["state"] == "CINEMATIC":
                    p.mixer.music.set_volume(0.0)
                else:
                    p.mixer.music.set_volume(1.0)
            
            if aura_channel:
                if remaining < AURA_FADE_START and remaining > 0:
                    progress = (AURA_FADE_START - remaining) / AURA_FADE_START
                    aura_channel.set_volume(min(1.0, progress))
                elif game_data["state"] == "CINEMATIC":
                    aura_channel.set_volume(1.0)
                else:
                    aura_channel.set_volume(0.0)

            # Object Updates
            game_data["mtn_far"].update(current_scroll_speed)
            game_data["mtn_near"].update(current_scroll_speed)

            if game_data["state"] == "TRAVEL":
                # Aliens
                for a in game_data["aliens"][:]:
                    shot = a.update(current_scroll_speed)
                    if shot:
                        dx = player.rect.centerx - a.rect.centerx
                        dy = player.rect.centery - a.rect.centery
                        ang = math.degrees(math.atan2(dy, dx))
                        game_data["bullets"].append(Bullet(a.rect.centerx, a.rect.centery, ang, False))
                    
                    if a.x < -100: game_data["aliens"].remove(a)
                    
                    if player.rect.colliderect(a.rect):
                        reaction = player.take_damage(10)
                        if reaction == "revenge":
                            b = Bullet(player.rect.centerx, player.rect.centery, player.turret_angle, True, damage=player.shield_accumulated_dmg, size_mod=3.0)
                            game_data["bullets"].append(b)
                            player.shield_accumulated_dmg = 0
                        game_data["explosions"].append(Explosion(a.rect.centerx, a.rect.centery, 'mechanical'))
                        if a in game_data["aliens"]: game_data["aliens"].remove(a)

                # Mines
                for m in game_data["mines"][:]:
                    m.update(current_scroll_speed)
                    if m.x < -50: game_data["mines"].remove(m)
                    
                    if player.rect.colliderect(m.rect):
                        reaction = player.take_damage(20)
                        if reaction == "revenge":
                             b = Bullet(player.rect.centerx, player.rect.centery, player.turret_angle, True, damage=player.shield_accumulated_dmg, size_mod=3.0)
                             game_data["bullets"].append(b)
                             player.shield_accumulated_dmg = 0
                        game_data["explosions"].append(Explosion(m.x, m.y, 'mechanical'))
                        if m in game_data["mines"]: game_data["mines"].remove(m)
                
                # Powerups
                for pup in game_data["powerups"][:]:
                    if not pup.update(current_scroll_speed):
                        game_data["powerups"].remove(pup)
                        continue
                    
                    if player.rect.colliderect(pup.rect):
                        if pup.type == 'shield':
                            player.shield_active = True; player.shield_hp = 50; player.shield_accumulated_dmg = 0
                        elif pup.type == 'beam':
                            player.beam_active = True; player.beam_timer = FPS * 5 
                        elif pup.type == 'shockwave':
                            game_data["explosions"].append(Explosion(player.rect.centerx, player.rect.centery, 'shockwave'))
                            for a in game_data["aliens"][:]:
                                if getDist(player.x, player.y, a.x, a.y) < 720:
                                    game_data["explosions"].append(Explosion(a.x, a.y, 'organic'))
                                    game_data["aliens"].remove(a)
                            for m in game_data["mines"][:]:
                                if getDist(player.x, player.y, m.x, m.y) < 720:
                                    game_data["explosions"].append(Explosion(m.x, m.y, 'mechanical'))
                                    game_data["mines"].remove(m)
                        game_data["powerups"].remove(pup)

            # Bullets
            for b in game_data["bullets"][:]:
                b.move()
                if not b.exists:
                    game_data["bullets"].remove(b)
                    continue
                
                if b.is_player:
                    hit = False
                    for a in game_data["aliens"][:]:
                        if getDist(b.x, b.y, a.rect.centerx, a.rect.centery) < a.width/2:
                            game_data["explosions"].append(Explosion(a.x, a.y, 'organic'))
                            if random.random() < 0.10: game_data["powerups"].append(PowerUp(a.x, a.y))
                            game_data["aliens"].remove(a)
                            if not b.is_revenge: 
                                b.exists = False
                                game_data["bullets"].remove(b)
                            hit = True
                            break
                    if not hit:
                         for m in game_data["mines"][:]:
                            if getDist(b.x, b.y, m.x, m.y) < m.radius * 2:
                                game_data["explosions"].append(Explosion(m.x, m.y, 'mechanical'))
                                game_data["mines"].remove(m)
                                if not b.is_revenge:
                                    b.exists = False
                                    game_data["bullets"].remove(b)
                                break
                else:
                    if player.rect.collidepoint(b.x, b.y):
                        reaction = player.take_damage(5)
                        if reaction == "revenge":
                             b_rev = Bullet(player.rect.centerx, player.rect.centery, player.turret_angle, True, damage=player.shield_accumulated_dmg, size_mod=3.0)
                             game_data["bullets"].append(b_rev)
                             player.shield_accumulated_dmg = 0
                        game_data["explosions"].append(Explosion(b.x, b.y, 'mechanical'))
                        b.exists = False
                        game_data["bullets"].remove(b)

            for e in game_data["explosions"][:]:
                if not e.update():
                    game_data["explosions"].remove(e)

            # --- DRAWING ---
            screen.fill(SKY_BLUE)
            game_data["mtn_far"].draw(screen)
            game_data["mtn_near"].draw(screen)
            
            p.draw.rect(screen, DEEP_WATER, (0, SCREEN_HEIGHT - 300, SCREEN_WIDTH, 300))
            p.draw.rect(screen, WATER_BLUE, (0, SCREEN_HEIGHT - 250, SCREEN_WIDTH, 250))
            
            wave_offset = (p.time.get_ticks() // 5) % 50
            for i in range(0, SCREEN_WIDTH, 50):
                p.draw.line(screen, (255,255,255, 100), 
                            (i - wave_offset, SCREEN_HEIGHT - 240), 
                            (i + 20 - wave_offset, SCREEN_HEIGHT - 240), 2)

            for m in game_data["mines"]: m.draw(screen)
            game_data["player"].draw(screen)
            for a in game_data["aliens"]: a.draw(screen)
            for pup in game_data["powerups"]: pup.draw(screen)
            
            if game_data["prism"].visible:
                if game_data["prism"].beam_active:
                    game_data["prism"].draw_beam(screen, player.rect.centerx, player.rect.centery)
                game_data["prism"].draw(screen)
                soldier.draw(screen)
                
            for b in game_data["bullets"]: b.draw(screen)
            for e in game_data["explosions"]: e.draw(screen)
                
            if game_data["storm"] > 0:
                s_surface = p.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                s_surface.set_alpha(game_data["storm"])
                s_surface.fill(STORM_SKY)
                screen.blit(s_surface, (0,0))
                for _ in range(20):
                    rx = random.randint(0, SCREEN_WIDTH)
                    ry = random.randint(0, SCREEN_HEIGHT)
                    p.draw.line(screen, (200, 200, 220), (rx, ry), (rx-5, ry+15), 1)

            p.draw.rect(screen, BLACK, (10, 10, 300, 30))
            fill_amt = min(1.0, game_data["distance"] / TOTAL_DISTANCE_TO_PRISM)
            p.draw.rect(screen, ORANGE, (12, 12, 296 * fill_amt, 26))

            p.display.flip()
            clock.tick(FPS)

    p.quit()

if __name__ == "__main__":
    run_game()