import pygame
import os
import random
import math

class TrashItem:
    def __init__(self, x, y, image_path, item_type="trash"):
        self.x = x
        self.y = y
        self.width = 32
        self.height = 32
        self.item_type = item_type
        self.collected = False
        self.bob_offset = 0
        self.bob_speed = 2.0
        
        # Load and scale image
        if os.path.exists(image_path):
            self.image = pygame.image.load(image_path).convert_alpha()
            self.image = pygame.transform.scale(self.image, (self.width, self.height))
        else:
            # Create fallback image
            self.image = pygame.Surface((self.width, self.height))
            self.image.fill((139, 69, 19))  # Brown color for trash
        
        self.rect = pygame.Rect(x, y, self.width, self.height)
    
    def update(self, dt):
        """Update trash item with bobbing animation"""
        self.rect.x = self.x
        self.rect.y = self.y
        
        # Add bobbing animation
        self.bob_offset = math.sin(pygame.time.get_ticks() * 0.003) * 3
    
    def draw(self, screen, camera_x, camera_y):
        """Draw trash item with bobbing animation"""
        if not self.collected:
            draw_y = self.y - camera_y + self.bob_offset
            screen.blit(self.image, (self.x - camera_x, draw_y))
    
    def check_collision(self, player_rect):
        """Check if player collides with trash item"""
        if not self.collected:
            return self.rect.colliderect(player_rect)
        return False
    
    def collect(self):
        """Mark trash item as collected"""
        self.collected = True

class Dustbin:
    def __init__(self, x, y, image_path):
        self.x = x
        self.y = y
        self.width = 48
        self.height = 48
        self.trash_count = 0
        self.max_capacity = 5
        self.full_glow = 0
        
        # Load and scale image
        if os.path.exists(image_path):
            self.image = pygame.image.load(image_path).convert_alpha()
            self.image = pygame.transform.scale(self.image, (self.width, self.height))
        else:
            # Create fallback image
            self.image = pygame.Surface((self.width, self.height))
            self.image.fill((128, 128, 128))  # Gray color for dustbin
        
        self.rect = pygame.Rect(x, y, self.width, self.height)
    
    def update(self, dt):
        """Update dustbin with glow effect when full"""
        self.rect.x = self.x
        self.rect.y = self.y
        
        # Add glow effect when full
        if self.is_full():
            self.full_glow = math.sin(pygame.time.get_ticks() * 0.005) * 0.3 + 0.7
    
    def draw(self, screen, camera_x, camera_y):
        """Draw dustbin with glow effect"""
        # Draw glow effect if full
        if self.is_full() and self.full_glow > 0:
            glow_surface = pygame.Surface((self.width + 10, self.height + 10), pygame.SRCALPHA)
            glow_color = (255, 255, 0, int(50 * self.full_glow))
            pygame.draw.ellipse(glow_surface, glow_color, (0, 0, self.width + 10, self.height + 10))
            screen.blit(glow_surface, (self.x - camera_x - 5, self.y - camera_y - 5))
        
        screen.blit(self.image, (self.x - camera_x, self.y - camera_y))
        
        # Draw trash count indicator
        font = pygame.font.Font(None, 24)
        color = (255, 255, 255) if not self.is_full() else (255, 255, 0)
        text = font.render(f"{self.trash_count}/{self.max_capacity}", True, color)
        text_rect = text.get_rect(center=(self.x - camera_x + self.width//2, self.y - camera_y - 10))
        screen.blit(text, text_rect)
    
    def check_collision(self, player_rect):
        """Check if player collides with dustbin"""
        return self.rect.colliderect(player_rect)
    
    def add_trash(self):
        """Add trash to dustbin"""
        if self.trash_count < self.max_capacity:
            self.trash_count += 1
            return True
        return False
    
    def is_full(self):
        """Check if dustbin is full"""
        return self.trash_count >= self.max_capacity

class HealthItem:
    def __init__(self, x, y, image_path):
        self.x = x
        self.y = y
        self.width = 32
        self.height = 32
        self.collected = False
        self.bob_offset = 0
        self.pulse_scale = 1.0
        
        # Load and scale image
        if os.path.exists(image_path):
            self.image = pygame.image.load(image_path).convert_alpha()
            self.image = pygame.transform.scale(self.image, (self.width, self.height))
        else:
            # Create fallback image
            self.image = pygame.Surface((self.width, self.height))
            self.image.fill((255, 0, 0))  # Red color for health
        
        self.rect = pygame.Rect(x, y, self.width, self.height)
    
    def update(self, dt):
        """Update health item with pulsing animation"""
        self.rect.x = self.x
        self.rect.y = self.y
        
        # Add pulsing animation
        self.pulse_scale = 1.0 + math.sin(pygame.time.get_ticks() * 0.005) * 0.1
    
    def draw(self, screen, camera_x, camera_y):
        """Draw health item with pulsing animation"""
        if not self.collected:
            # Scale the image for pulsing effect
            scaled_width = int(self.width * self.pulse_scale)
            scaled_height = int(self.height * self.pulse_scale)
            scaled_image = pygame.transform.scale(self.image, (scaled_width, scaled_height))
            
            # Center the scaled image
            draw_x = self.x - camera_x - (scaled_width - self.width) // 2
            draw_y = self.y - camera_y - (scaled_height - self.height) // 2
            screen.blit(scaled_image, (draw_x, draw_y))
    
    def check_collision(self, player_rect):
        """Check if player collides with health item"""
        if not self.collected:
            return self.rect.colliderect(player_rect)
        return False
    
    def collect(self):
        """Mark health item as collected"""
        self.collected = True 