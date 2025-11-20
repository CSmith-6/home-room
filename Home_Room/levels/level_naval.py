import pygame as p
import random
from systems.parallax import ParallaxLayer, make_island_layer, make_water_layer
from entities.boat import Battleship
from entities.plane import Plane
from entities.prism import Prism
from entities.explosion import Explosion

WIDTH, HEIGHT = 1400, 600
FPS = 60
BASE_SCROLL_SPEED = 1.4
DIST_TOTAL = 4000

SKY_BLUE = (50,90,140)

def dist2(x0,y0,x1,y1): return (x1-x0)**2 + (y1-y0)**2

def draw_progress(screen, progress):
    w = 400; h = 18
    x = WIDTH//2 - w//2; y = 20
    p.draw.rect(screen,(60,60,70),(x,y,w,h),border_radius=4)
    p.draw.rect(screen,(80,220,120),(x,y,int(w*progress),h),border_radius=4)
    p.draw.rect(screen,(255,255,255),(x,y,w,h),2,border_radius=4)

def run_level():
    p.init()
    screen = p.display.set_mode((WIDTH,HEIGHT))
    clock = p.time.Clock()

    island = make_island_layer(WIDTH,HEIGHT)
    deep   = make_water_layer(WIDTH,200,(10,40,80))
    mid    = make_water_layer(WIDTH,180,(20,70,120))
    surf   = make_water_layer(WIDTH,140,(40,110,170))

    layers = [
        ParallaxLayer(island,0.4,0),
        ParallaxLayer(deep,0.8,HEIGHT-210),
        ParallaxLayer(mid,1.3,HEIGHT-190),
        ParallaxLayer(surf,2.0,HEIGHT-160)
    ]

    ship = Battleship(WIDTH//3, HEIGHT-140)
    bullets=[]; planes=[]; explosions=[]
    spawn_t=0; spawn_delay=80

    dist = DIST_TOTAL
    state="TRAVEL"
    prism=None
    arrival_timer=0
    target_x = WIDTH/3
    target_y = HEIGHT-140

    running=True
    while running:
        dt=clock.tick(FPS)
        for e in p.event.get():
            if e.type==p.QUIT: running=False
        keys=p.key.get_pressed()
        world_scroll = BASE_SCROLL_SPEED

        if state=="TRAVEL":
            ship.handle_movement(keys)
            if keys[p.K_LEFT]: ship.rotate_turrets(-2)
            if keys[p.K_RIGHT]: ship.rotate_turrets(2)

            dist -= world_scroll
            progress = max(0,min(1,1 - dist/DIST_TOTAL))
            if progress>=1:
                state="ARRIVAL"
                ship.controls_enabled=False

        if state=="ARRIVAL":
            arrival_timer+=1
            ship.auto_move_to(target_x,target_y)
            if prism is None and arrival_timer>90:
                prism=Prism(WIDTH+200,HEIGHT*0.45)
            progress=1

        if state=="COMPLETE":
            progress=1
            world_scroll=0

        for L in layers: L.update(world_scroll)
        ship.update()

        if state=="TRAVEL" and keys[p.K_SPACE]:
            for t in ship.turrets:
                if t.can_fire(): bullets.append(t.fire())

        for b in bullets: b.update()
        bullets=[b for b in bullets if b.alive]

        for pl in planes: pl.update()
        planes=[pl for pl in planes if pl.alive]

        if state=="TRAVEL":
            spawn_t+=1
            if spawn_t>=spawn_delay:
                planes.append(Plane()); spawn_t=0

        for pl in planes:
            for b in bullets:
                if dist2(pl.x,pl.y,b.x,b.y) <= (pl.radius+b.radius)**2:
                    pl.alive=False; b.alive=False
                    explosions.append(Explosion(pl.x,pl.y))

        for ex in explosions: ex.update()
        explosions=[ex for ex in explosions if not ex.done]

        if prism:
            prism.update()
            if prism.done and state!="COMPLETE":
                state="COMPLETE"

        screen.fill(SKY_BLUE)
        for L in layers: L.draw(screen)

        ship.draw(screen)
        for pl in planes: pl.draw(screen)
        for b in bullets: b.draw(screen)
        for ex in explosions: ex.draw(screen)
        if prism: prism.draw(screen)

        draw_progress(screen,progress)
        p.display.flip()

    p.quit()
