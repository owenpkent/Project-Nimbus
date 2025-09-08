"""
Simple test to verify axis configuration dialog works independently.
"""

import pygame
import sys
from config import ControllerConfig
from axis_config_dialog import AxisConfigDialog

def main():
    pygame.init()
    
    # Create display
    width, height = 800, 600
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Dialog Test")
    
    # Initialize config and dialog
    config = ControllerConfig()
    dialog = AxisConfigDialog(config, screen)
    
    # Show dialog immediately
    dialog.show()
    print(f"Dialog visible: {dialog.is_visible}")
    
    clock = pygame.time.Clock()
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    # Toggle dialog visibility
                    if dialog.is_visible:
                        dialog.hide()
                    else:
                        dialog.show()
                    print(f"Dialog visible: {dialog.is_visible}")
            
            # Let dialog handle events
            dialog.handle_event(event)
        
        # Clear screen
        screen.fill((30, 30, 30))
        
        # Draw instructions
        font = pygame.font.Font(None, 24)
        text = font.render("Press SPACE to toggle dialog, ESC to exit", True, (255, 255, 255))
        screen.blit(text, (10, 10))
        
        # Draw dialog
        dialog.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
