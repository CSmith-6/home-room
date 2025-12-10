import pygame
import gemBattleships
import space
import spaceship_interior

def main():
    full_game_running = True
    
    while full_game_running:
        # --- GAME 1: Gem Battleships ---
        print("Starting Gem Battleships...")
        result = gemBattleships.run_game()
        
        if result == "QUIT":
            break
        elif result == "RESTART_GAME":
            continue # Goes back to top of while loop
        
        # --- GAME 2: Space ---
        # Re-init pygame is handled inside the games, but we ensure clean slate here
        print("Launching into Space...")
        result = space.run_game()
        
        if result == "QUIT":
            break
        elif result == "RESTART_GAME":
            continue
            
        # --- GAME 3: Spaceship Interior ---
        print("Entering Ship Interior...")
        result = spaceship_interior.run_game()
        
        if result == "QUIT":
            break
        elif result == "RESTART_GAME":
            continue
            
        # If we get here, the whole sequence finished naturally
        full_game_running = False
        print("All games finished.")

    pygame.quit()

if __name__ == "__main__":
    main()