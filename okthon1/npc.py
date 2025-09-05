import pygame
import os

class NPC:
    def __init__(self, x, y, scale_factor=1.0):
        self.x = x
        self.y = y
        self.scale_factor = scale_factor
        self.width = int(60 * scale_factor)
        self.height = int(60 * scale_factor)
        
        # Player physics
        self.vel_x = 0
        self.vel_y = 0
        self.speed = 100 * scale_factor
        self.jump_speed = -300 * scale_factor
        self.gravity = 600 * scale_factor
        self.on_ground = False
        self.jump_count = 0
        self.max_jumps = 2
        
        # Player movement
        self.facing_right = True
        self.is_dashing = False
        self.dash_timer = 0
        self.dash_duration = 0.2
        self.dash_cooldown = 1.0
        self.dash_cooldown_timer = 0
        self.dash_speed = 200 * scale_factor
        
        # Health and cleanliness system
        self.health = 100
        self.max_health = 100
        self.lives = 3
        self.is_clean = True
        self.clean_timer = 30.0
        self.dirt_timer = 0.0
        self.health_drain_timer = 0.0
        self.health_drain_interval = 20.0
        self.health_drain_amount = 10
        
        # Sound effects
        self.last_walk_sound = 0
        self.walk_sound_interval = 0.5
        self.last_jump_sound = 0
        self.jump_sound_cooldown = 0.1
        self.game_sounds = {}
        
        # NPC state
        self.has_quest = True
        self.quest_completed = False
        self.quest_accepted = False
        self.interaction_range = 80 * scale_factor
        
        # Load NPC sprite (using the same character sprites as player)
        self.load_sprites()
        self.current_sprite = self.sprite_frames['idle'][0]
        
        # Quest details
        self.quest_title = "Medicine Collection"
        self.quest_description = "I need medicine to help the villagers. Please collect 3 medicine items from around the map and bring them back to me."
        self.required_items = 3
        self.collected_items = 0
        
        # Dialogue
        self.dialogue_lines = {
            'greeting': "Hello traveler! I am in need of your help.",
            'quest_offer': "The villagers are sick and need medicine. Can you collect 3 medicine items for me?",
            'quest_accepted': "Thank you! Please find the medicine items scattered around the map.",
            'quest_in_progress': f"You have collected {self.collected_items}/{self.required_items} medicine items.",
            'quest_complete': "Excellent! You've collected all the medicine. The villagers will be grateful!",
            'quest_finished': "Thank you again for your help. The village is in your debt."
        }
        
        # Animation
        self.animation_index = 0
        self.animation_timer = 0
        self.animation_speed = 0.15
        self.state = 'idle'
        self.animation_timer = 0
        self.animation_index = 0

    def load_sprites(self):
        """Load NPC sprites (using character sprites)"""
        sprite_paths = {
            'idle': 'game images/front facing.png',
            'walk': [
                'game images/front facing.png',
                'game images/left.png',
                'game images/front facing.png',
                'game images/left.png'
            ],
            'run': [
                'game images/front facing.png',
                'game images/left.png',
                'game images/front facing.png',
                'game images/left.png'
            ],
            'jump': [
                'game images/jump.png',
                'game images/jump.png',
                'game images/jump.png'
            ]
        }
        
        self.sprite_frames = {}
        
        for key, path in sprite_paths.items():
            if isinstance(path, list):
                # Multiple frames for animation
                frames = []
                for p in path:
                    if os.path.exists(p):
                        sprite = pygame.image.load(p).convert_alpha()
                        scaled_sprite = pygame.transform.scale(sprite, (self.width, self.height))
                        frames.append(scaled_sprite)
                    else:
                        # Fallback sprite
                        fallback_surface = pygame.Surface((self.width, self.height))
                        fallback_surface.fill((0, 255, 0))  # Green for NPC
                        frames.append(fallback_surface)
                self.sprite_frames[key] = frames
            else:
                # Single frame
                if os.path.exists(path):
                    sprite = pygame.image.load(path).convert_alpha()
                    scaled_sprite = pygame.transform.scale(sprite, (self.width, self.height))
                    self.sprite_frames[key] = [scaled_sprite]
                else:
                    # Fallback sprite
                    fallback_surface = pygame.Surface((self.width, self.height))
                    fallback_surface.fill((0, 255, 0))  # Green for NPC
                    self.sprite_frames[key] = [fallback_surface]

    def play_sound(self, sound_name, game_sounds):
        """Play a sound effect if available"""
        if sound_name in game_sounds:
            try:
                game_sounds[sound_name].play()
            except:
                pass  # Ignore sound errors

    def update(self, dt, collision_grid, climb_grid):
        """Update NPC logic with player movement"""
        # Handle input
        keys = pygame.key.get_pressed()
        
        # Handle normal movement
        self.handle_normal_movement(keys, dt)
        
        # Handle knife throwing
        self.handle_knife_throwing(keys)
        
        # Apply gravity
        self.vel_y += self.gravity * dt
        
        # Update position
        self.x += self.vel_x * dt
        self.y += self.vel_y * dt
        
        # Check collisions
        if collision_grid:
            self.check_horizontal_collisions(collision_grid)
            self.check_vertical_collisions(collision_grid)
        
        # Update animation
        self.update_animation(dt)
        
        # Update dash
        if self.is_dashing:
            self.dash_timer -= dt
            if self.dash_timer <= 0:
                self.is_dashing = False
        
        if self.dash_cooldown_timer > 0:
            self.dash_cooldown_timer -= dt

    def handle_normal_movement(self, keys, dt):
        """Handle normal movement input"""
        # Horizontal movement
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.vel_x = -self.speed
            self.facing_right = False
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.vel_x = self.speed
            self.facing_right = True
        else:
            self.vel_x = 0
        
        # Jumping
        if keys[pygame.K_SPACE] and self.on_ground:
            self.vel_y = self.jump_speed
            self.on_ground = False
            self.jump_count += 1
            # Play jump sound
            self.play_sound('jump', getattr(self, 'game_sounds', {}))
        
        # Dashing
        if keys[pygame.K_d] and not self.is_dashing and self.dash_cooldown_timer <= 0:
            self.is_dashing = True
            self.dash_timer = self.dash_duration
            self.dash_cooldown_timer = self.dash_cooldown
        
        # Play walk sound when moving on ground
        if abs(self.vel_x) > 0 and self.on_ground:
            self.last_walk_sound += dt
            if self.last_walk_sound >= self.walk_sound_interval:
                self.play_sound('walk', getattr(self, 'game_sounds', {}))
                self.last_walk_sound = 0

    def handle_knife_throwing(self, keys):
        """Handle knife throwing input"""
        if keys[pygame.K_f]:
            # Knife throwing logic would go here
            pass

    def check_horizontal_collisions(self, tiles):
        """Check horizontal collisions with tiles"""
        player_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        tile_size = 32  # Updated to match TMX tile size
        
        # Only check tiles near the player to improve performance
        player_tile_x = int(self.x // tile_size)
        player_tile_y = int(self.y // tile_size)
        
        # Check a smaller area around the player
        start_x = max(0, player_tile_x - 2)
        end_x = min(len(tiles[0]), player_tile_x + 4)
        start_y = max(0, player_tile_y - 2)
        end_y = min(len(tiles), player_tile_y + 4)
        
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                if y < len(tiles) and x < len(tiles[0]):
                    tile_gid = tiles[y][x]
                    if tile_gid != 0:
                        tile_rect = pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)
                        if player_rect.colliderect(tile_rect):
                            if self.vel_x > 0:
                                self.x = tile_rect.left - self.width
                            elif self.vel_x < 0:
                                self.x = tile_rect.right

    def check_vertical_collisions(self, tiles):
        """Check vertical collisions with tiles"""
        self.on_ground = False
        player_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        tile_size = 32  # Updated to match TMX tile size
        
        # Only check tiles near the player to improve performance
        player_tile_x = int(self.x // tile_size)
        player_tile_y = int(self.y // tile_size)
        
        # Check a smaller area around the player
        start_x = max(0, player_tile_x - 2)
        end_x = min(len(tiles[0]), player_tile_x + 4)
        start_y = max(0, player_tile_y - 2)
        end_y = min(len(tiles), player_tile_y + 4)
        
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                if y < len(tiles) and x < len(tiles[0]):
                    tile_gid = tiles[y][x]
                    if tile_gid != 0:
                        tile_rect = pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)
                        if player_rect.colliderect(tile_rect):
                            if self.vel_y > 0:
                                self.y = tile_rect.top - self.height
                                self.vel_y = 0
                                self.on_ground = True
                                self.jump_count = 0
                                print(f"NPC landed on ground at Y={self.y}")
                            elif self.vel_y < 0:
                                self.y = tile_rect.bottom
                                self.vel_y = 0

    def update_animation(self, dt):
        """Update animation state and timing"""
        self.animation_timer += dt
        
        # Determine animation state
        if not self.on_ground:
            self.state = 'jump'
        elif abs(self.vel_x) > 5:
            self.state = 'run'
        else:
            self.state = 'idle'
        
        # Update animation frame
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            if self.state in self.sprite_frames:
                self.animation_index = (self.animation_index + 1) % len(self.sprite_frames[self.state])
            else:
                self.animation_index = 0
        
        # Get current sprite
        if self.state in self.sprite_frames:
            self.current_sprite = self.sprite_frames[self.state][self.animation_index]
        else:
            self.current_sprite = self.sprite_frames['idle'][0]

    def make_dirty(self):
        """Make the NPC dirty"""
        self.is_clean = False
        self.dirt_timer = 30.0
        print("NPC got dirty!")

    def make_clean(self):
        """Make the NPC clean"""
        self.is_clean = True
        self.clean_timer = 30.0
        print("NPC is now clean!")

    def update_quest_progress(self, player):
        """Update quest progress based on player's collected items"""
        # This will be called from the main game to update collected items
        pass

    def is_player_nearby(self, player):
        """Check if player is within interaction range"""
        distance = ((player.x - self.x) ** 2 + (player.y - self.y) ** 2) ** 0.5
        return distance <= self.interaction_range

    def get_dialogue(self, player):
        """Get appropriate dialogue based on quest state"""
        if not self.quest_accepted:
            return [("NPC", self.dialogue_lines['greeting']),
                   ("NPC", self.dialogue_lines['quest_offer'])]
        elif self.quest_accepted and not self.quest_completed:
            return [("NPC", self.dialogue_lines['quest_in_progress'])]
        else:
            return [("NPC", self.dialogue_lines['quest_finished'])]

    def accept_quest(self):
        """Accept the quest"""
        self.quest_accepted = True
        return [("NPC", self.dialogue_lines['quest_accepted'])]

    def complete_quest(self):
        """Complete the quest"""
        self.quest_completed = True
        return [("NPC", self.dialogue_lines['quest_complete'])]

    def draw(self, screen, camera_x, camera_y):
        """Draw the NPC"""
        screen.blit(self.current_sprite, (self.x - camera_x, self.y - camera_y))

    @property
    def rect(self):
        """Get the NPC's rectangle for collision detection"""
        return pygame.Rect(self.x, self.y, self.width, self.height) 