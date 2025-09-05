import pygame
import os

class Medicine:
    def __init__(self, x, y, scale_factor=1.0):
        self.x = x
        self.y = y
        self.scale_factor = scale_factor
        self.width = int(48 * scale_factor)  # Made larger
        self.height = int(48 * scale_factor)  # Made larger
        self.collected = False
        
        # Load medicine sprite
        self.load_sprite()
        
        # Quest item properties
        self.item_type = "medicine"
        self.quest_item = True

    def load_sprite(self):
        """Load medicine sprite from available items"""
        # Try to use a suitable medicine-like item from the available sprites
        medicine_paths = [
            'tiled/PNG/Items/platformPack_item005.png',  # Potion-like item
            'tiled/PNG/Items/platformPack_item006.png',  # Alternative medicine
            'tiled/PNG/Items/platformPack_item009.png',  # Another option
        ]
        
        self.sprite = None
        for path in medicine_paths:
            if os.path.exists(path):
                try:
                    self.sprite = pygame.image.load(path).convert_alpha()
                    # Scale the sprite
                    self.sprite = pygame.transform.scale(self.sprite, (self.width, self.height))
                    break
                except Exception as e:
                    continue
        
        # If no sprite found, create a fallback
        if self.sprite is None:
            self.sprite = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            # Create a simple medicine bottle shape
            pygame.draw.rect(self.sprite, (255, 255, 255), (0, 0, self.width, self.height))
            pygame.draw.rect(self.sprite, (0, 255, 0), (4, 4, self.width-8, self.height-8))  # Green medicine
            pygame.draw.rect(self.sprite, (0, 200, 0), (8, 8, self.width-16, 8))  # Bottle cap

    def check_collision(self, player):
        """Check if player has collected this medicine"""
        if not self.collected:
            player_rect = player.rect
            medicine_rect = pygame.Rect(self.x, self.y, self.width, self.height)
            
            if player_rect.colliderect(medicine_rect):
                self.collected = True
                return True
        return False

    def draw(self, screen, camera_x, camera_y):
        """Draw medicine item if not collected"""
        if not self.collected:
            screen_x = self.x - camera_x
            screen_y = self.y - camera_y
            screen.blit(self.sprite, (screen_x, screen_y))

    @property
    def rect(self):
        """Get medicine rectangle for collision detection"""
        return pygame.Rect(self.x, self.y, self.width, self.height) 