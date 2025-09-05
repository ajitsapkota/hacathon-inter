import pygame

class Entity:
    """Base class for all game entities."""
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False

    def update(self, dt, tilemap):
        pass  # To be implemented by subclasses

    def draw(self, screen, camera_x, camera_y):
        # Draw a placeholder rectangle for now
        rect = pygame.Rect(self.x - camera_x, self.y - camera_y, self.width, self.height)
        pygame.draw.rect(screen, (255, 0, 0), rect, 2)

class Enemy(Entity):
    """Placeholder enemy class for demonstration."""
    def __init__(self, x, y):
        super().__init__(x, y, 32, 32)
        # Add enemy-specific initialization here

    def update(self, dt, tilemap):
        # Add enemy logic here
        pass 
class Knife:
    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.speed = 15 * direction
        self.width = 20
        self.height = 10
        # Load knife sprite
        self.image = pygame.image.load('tiled/PNG/Items/knife.png')  # your knife image path
        self.image = pygame.transform.scale(self.image, (self.width, self.height))
        if direction == -1:
            self.image = pygame.transform.flip(self.image, True, False)
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)    

    def update(self, dt):
        self.x += self.speed
        self.rect.x = self.x

    def draw(self, screen, camera_x, camera_y):
        screen.blit(self.image, (self.x - camera_x, self.y - camera_y))

    def off_screen(self):
        return self.x < 0 or self.x > 2000  # Adjust 2000 to your map width or screen width
class KnifePickup:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 16
        self.height = 16
        self.image = pygame.image.load('tiled/PNG/Items/knife.png')  # Your knife pickup image
        self.image = pygame.transform.scale(self.image, (self.width, self.height))
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, screen, camera_x, camera_y):
        screen.blit(self.image, (self.x - camera_x, self.y - camera_y))
