import pygame as p
import random
from systems.parallax import ParallaxLayer, make_island_layer, make_water_layer
from entities.boat import Battleship
from entities.plane import Plane
from entities.plasma_explosion import PlasmaExplosion
from entities.bullet import Bullet   # player bullets (if you still use this)  <-- optional
from entities.plane_bullet import PlaneBullet  # for type hints / clarity

WIDTH, HEIGHT = 1400, 600
FPS = 60
BASE_SCROLL_SPEED = 1.4
DIST_TOTAL = 4000
PLANE_BULLET_DAMAGE = 1  # damage per hit from enemy plasma

SKY_BLUE = (50, 90, 140)


def dist2(x0, y0, x1, y1):
    return (x1 - x0) ** 2 + (y1 - y0) ** 2


def draw_progress(screen, progress):
    w = 400
    h = 18
    x = WIDTH // 2 - w // 2
    y = 20
    p.draw.rect(screen, (60, 60, 70), (x, y, w, h), border_radius=4)
    p.draw.rect(screen, (80, 220, 120), (x, y, int(w * progress), h), border_radius=4)
    p.draw.rect(screen, (255, 255, 255), (x, y, w, h), 2, border_radius=4)


def draw_health_bar(screen, hp, hp_max):
    w = 240
    h = 18
    x = 20
    y = 20
    ratio = 0 if hp_max <= 0 else max(0.0, min(1.0, hp / hp_max))
    fill_w = int(w * ratio)
    bg_color = (40, 40, 50)
    fg_color = (220, 80, 80) if ratio < 0.35 else (240, 180, 70) if ratio < 0.65 else (90, 200, 120)
    p.draw.rect(screen, bg_color, (x, y, w, h), border_radius=4)
    p.draw.rect(screen, fg_color, (x, y, fill_w, h), border_radius=4)
    p.draw.rect(screen, (255, 255, 255), (x, y, w, h), 2, border_radius=4)


def run_level():
    p.init()
    screen = p.display.set_mode((WIDTH, HEIGHT))
    p.display.set_caption("Dark Side Odyssey - Naval Patrol")
    clock = p.time.Clock()

    island = make_island_layer(WIDTH, HEIGHT)
    deep = make_water_layer(WIDTH, 200, (10, 40, 80))
    mid = make_water_layer(WIDTH, 180, (20, 70, 120))
    surf = make_water_layer(WIDTH, 140, (40, 110, 170))

    layers = [
        ParallaxLayer(island, 0.4, 0),
        ParallaxLayer(deep, 0.8, HEIGHT - 210),
        ParallaxLayer(mid, 1.3, HEIGHT - 190),
        ParallaxLayer(surf, 2.0, HEIGHT - 160),
    ]

    ship = Battleship(WIDTH // 3, HEIGHT - 140)

    # Player bullets (from ship turrets) – if you're still using the simple Bullet class
    player_bullets = []

    # Enemy bullets (from planes, using your sprite)
    enemy_bullets = []

    planes = []
    explosions = []

    spawn_t = 0
    spawn_delay = 80

    dist = DIST_TOTAL
    state = "TRAVEL"
    prism = None
    arrival_timer = 0
    target_x = WIDTH / 3
    target_y = HEIGHT - 140
    progress = 0.0

    running = True
    while running:
        dt = clock.tick(FPS)
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False

        keys = p.key.get_pressed()
        if keys[p.K_ESCAPE]:
            running = False

        world_scroll = BASE_SCROLL_SPEED

        # --- STATE: TRAVEL ---
        if state == "TRAVEL":
            ship.handle_movement(keys)

            # Turret rotation
            if keys[p.K_LEFT]:
                ship.rotate_turrets(-2)
            if keys[p.K_RIGHT]:
                ship.rotate_turrets(2)

            # Travel distance / progress
            dist -= world_scroll
            dist = max(0, dist)
            progress = max(0, min(1, 1 - dist / DIST_TOTAL))

            if progress >= 1:
                state = "ARRIVAL"
                ship.controls_enabled = False

        # --- STATE: ARRIVAL ---
        if state == "ARRIVAL":
            arrival_timer += 1
            ship.auto_move_to(target_x, target_y)
            progress = 1.0
            if prism is None and arrival_timer > 90:
                from entities.prism import Prism
                prism = Prism(WIDTH + 200, HEIGHT * 0.45)

        if state == "COMPLETE":
            world_scroll = 0.0
            progress = 1.0
        if state == "GAME_OVER":
            world_scroll = 0.0
            ship.controls_enabled = False
            progress = max(progress, 0.0)

        # Update parallax layers
        for layer in layers:
            layer.update(world_scroll)

        # Update ship (rocking, turret positions)
        ship.update()

        # Player firing (from ship turrets) – still optional
        if state == "TRAVEL" and keys[p.K_SPACE]:
            for t in ship.turrets:
                if t.can_fire():
                    player_bullets.append(t.fire())

        # Update player bullets
        for b in player_bullets:
            b.update()
        player_bullets = [b for b in player_bullets if b.alive]

        # Spawn planes during TRAVEL
        if state == "TRAVEL":
            spawn_t += 1
            if spawn_t >= spawn_delay:
                planes.append(Plane())
                spawn_t = 0

        # Update planes + have them fire at the ship
        new_enemy_bullets = []
        for pl in planes:
            pl.update()
            if state == "TRAVEL":
                bullet = pl.try_fire(ship)
                if bullet is not None:
                    new_enemy_bullets.append(bullet)
        enemy_bullets.extend(new_enemy_bullets)
        planes = [pl for pl in planes if pl.alive]

        # Update enemy bullets
        for eb in enemy_bullets:
            eb.update()
        enemy_bullets = [eb for eb in enemy_bullets if eb.alive]

        # Collisions: player bullet vs plane
        for pl in planes:
            if not pl.alive:
                continue
            for b in player_bullets:
                if not b.alive:
                    continue
                if dist2(pl.x, pl.y, b.x, b.y) <= (pl.radius + b.radius) ** 2:
                    pl.alive = False
                    b.alive = False
                    explosions.append(PlasmaExplosion(pl.x, pl.y))
                    break

        # Collisions: enemy bullet vs ship
        ship_left = ship.x - ship.width / 2
        ship_right = ship.x + ship.width / 2
        ship_top = ship.current_y - ship.height / 2 - 20
        ship_bottom = ship.current_y + ship.height / 2 + 20

        for eb in enemy_bullets:
            if ship_left < eb.x < ship_right and ship_top < eb.y < ship_bottom:
                eb.alive = False
                explosions.append(PlasmaExplosion(eb.x, eb.y))
                ship.take_damage(PLANE_BULLET_DAMAGE)
                if ship.is_dead:
                    state = "GAME_OVER"

        # Update explosions (plasma)
        for ex in explosions:
            ex.update()
        explosions = [ex for ex in explosions if not ex.done]

        # Update prism (arrival)
        if prism is not None:
            prism.update()
            if prism.done and state != "COMPLETE":
                state = "COMPLETE"

        # --- DRAW ---
        screen.fill(SKY_BLUE)
        for layer in layers:
            layer.draw(screen)

        ship.draw(screen)

        for pl in planes:
            pl.draw(screen)

        for b in player_bullets:
            b.draw(screen)

        for eb in enemy_bullets:
            eb.draw(screen)

        for ex in explosions:
            ex.draw(screen)

        if prism is not None:
            prism.draw(screen)

        draw_health_bar(screen, ship.health, ship.max_health)
        draw_progress(screen, progress)
        if state == "GAME_OVER":
            font = p.font.SysFont(None, 64)
            text = font.render("Ship Destroyed", True, (250, 80, 80))
            rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(text, rect)
        p.display.flip()

    p.quit()
