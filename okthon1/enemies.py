import pygame
from projectile import Projectile

class Enemy:
    def __init__(self, x, y, scale_factor=1.0):
        self.x = x
        self.y = y
        self.scale_factor = scale_factor
        self.width = int(60 * scale_factor)
        self.height = int(60 * scale_factor)
        self.vel_x = 2 * scale_factor
        self.direction = 1  # 1 = right, -1 = left
        self.shoot_cooldown = 0.8  # Much faster shooting
        self.shoot_timer = 0
        self.projectiles = []
        self.last_shot_time = 0
        self.is_aiming = False

        # Scale enemy sprite
        original_sprite = pygame.image.load('data/images/entities/enemy/idle/00.png')
        self.sprite = pygame.transform.scale(original_sprite, (self.width, self.height))

    def update(self, dt, player, camera_x, screen_width):
        # Move enemy
        self.x += self.vel_x * self.direction
        if self.x < 0 or self.x > 900 * self.scale_factor:
            self.direction *= -1

        # Check if player is visible horizontally (same Y level)
        player_on_screen = camera_x <= player.x <= camera_x + screen_width
        in_range = abs(self.x - player.x) < 1200 * self.scale_factor  # Much larger range
        
        # Check if player is roughly at the same Y level (horizontal line of sight)
        horizontal_sight = abs(self.y - player.y) < 100 * self.scale_factor  # Tighter vertical range
        
        # Check if enemy is facing the player
        enemy_facing_player = False
        if self.direction == 1:  # Enemy facing right
            enemy_facing_player = player.x > self.x
        else:  # Enemy facing left
            enemy_facing_player = player.x < self.x

        # Shoot only if player is on screen, in range, at same Y level, and enemy is facing player
        if player_on_screen and in_range and horizontal_sight and enemy_facing_player:
            self.is_aiming = True
            self.shoot_timer += dt
            if self.shoot_timer >= self.shoot_cooldown:
                self.shoot_timer = 0
                self.shoot(player)
        else:
            self.is_aiming = False

        # Update projectiles
        for proj in self.projectiles:
            proj.update(dt)
        self.projectiles = [p for p in self.projectiles if not p.off_screen()]

    def shoot(self, player):
        # Shoot directly at player
        proj = Projectile(self.x + self.width // 2, self.y + self.height // 2, player.x, player.y)
        self.projectiles.append(proj)

    def draw(self, screen, camera_x, camera_y):
        # Draw aiming indicator
        if self.is_aiming:
            # Draw red glow around enemy when aiming
            glow_radius = self.width // 2 + int(10 * self.scale_factor)
            glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (255, 0, 0, 100), (glow_radius, glow_radius), glow_radius)
            screen.blit(glow_surface, (self.x - camera_x - int(10 * self.scale_factor), self.y - camera_y - int(10 * self.scale_factor)))
        
        screen.blit(self.sprite, (self.x - camera_x, self.y - camera_y))
        for proj in self.projectiles:
            proj.draw(screen, camera_x, camera_y)

    def check_player_collision(self, player):
        player_rect = pygame.Rect(player.x, player.y, player.width, player.height)
        for proj in self.projectiles:
            if player_rect.colliderect(proj.get_rect()):
                return True
        return False

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height) 