import pygame
import sys
import math
import random

WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1080
GAME_WIDTH = 480
GAME_HEIGHT = 270

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.canvas = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 10)
        self.paused = False

    def draw_menu(self):
        overlay = pygame.Surface((GAME_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.canvas.blit(overlay, (0,0))
        
        mx, my = pygame.mouse.get_pos()
        # Scale mouse down to canvas size
        mx = int(mx * (GAME_WIDTH / WINDOW_WIDTH))
        my = int(my * (GAME_HEIGHT / WINDOW_HEIGHT))
        
        btn_w, btn_h = 100, 20
        cx, cy = GAME_WIDTH // 2, GAME_HEIGHT // 2
        
        buttons = [
            ("RESUME", (cx-btn_w//2, cy-30, btn_w, btn_h), "RESUME"),
            ("RESTART LEVEL", (cx-btn_w//2, cy, btn_w, btn_h), "LEVEL"),
            ("RESTART GAME", (cx-btn_w//2, cy+30, btn_w, btn_h), "GAME"),
            ("QUIT", (cx-btn_w//2, cy+60, btn_w, btn_h), "QUIT")
        ]
        
        click = pygame.mouse.get_pressed()[0]
        action = None
        
        for text, rect_tuple, act in buttons:
            rect = pygame.Rect(rect_tuple)
            color = (50, 200, 50)
            if rect.collidepoint(mx, my):
                color = (100, 255, 100)
                if click: action = act
            
            pygame.draw.rect(self.canvas, color, rect)
            pygame.draw.rect(self.canvas, (255,255,255), rect, 1)
            txt = self.font.render(text, True, (0,0,0))
            self.canvas.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))
            
        return action

    def run(self):
        while True: # Game Loop
            if self.paused:
                action = self.draw_menu()
                if action == "RESUME": 
                    self.paused = False
                    pygame.time.wait(200) # Debounce
                elif action == "LEVEL": return "RESTART_LEVEL"
                elif action == "GAME": return "RESTART_GAME"
                elif action == "QUIT": return "QUIT"
            else:
                # Update Logic
                keys = pygame.key.get_pressed()
                # ... player movement ...
                
            # Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT: return "QUIT"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_m:
                        self.paused = not self.paused

            # Draw to Canvas
            self.canvas.fill((20, 20, 30))
            # ... draw room ...
            
            # Scale and Flip
            scaled = pygame.transform.scale(self.canvas, (WINDOW_WIDTH, WINDOW_HEIGHT))
            self.screen.blit(scaled, (0,0))
            pygame.display.flip()
            self.clock.tick(60)

def run_game():
    while True: # Level Restart Loop
        g = Game()
        result = g.run()
        if result == "RESTART_LEVEL": continue
        return result # RESTART_GAME, QUIT, or None (finished)

if __name__ == "__main__":
    run_game()