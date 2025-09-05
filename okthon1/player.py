import pygame
import os
from entities import Knife

class Player:
    def __init__(self, x, y, scale_factor=0.75):
        """Initialize player"""
        self.x = x
        self.y = y
        self.scale_factor = scale_factor
        self.width = int(32 * scale_factor)
        self.height = int(32 * scale_factor)
        
        # Player physics
        self.vel_x = 0
        self.vel_y = 0
        # Physics constants
        self.speed = 150  # Reduced horizontal movement speed for smoother movement
        self.jump_speed = -450  # Slightly reduced jump velocity
        self.gravity = 1000  # Reduced gravity for smoother falling
        self.max_fall_speed = 500  # Reduced max fall speed
        self.on_ground = False
        self.jump_count = 0
        self.max_jumps = 2
        
        # Dashing
        self.is_dashing = False
        self.dash_speed = 400 * scale_factor
        self.dash_duration = 0.2
        self.dash_timer = 0
        self.dash_cooldown_timer = 0
        self.dash_cooldown = 1.0
        
        # Knife throwing
        self.knives_available = 5
        self.knife_cooldown = 0.5
        self.knife_timer = 0
        
        # Health and cleanliness system
        self.health = 100
        self.max_health = 100
        self.lives = 3
        self.cleanliness = 100
        self.is_dirty = False
        self.dirt_timer = 0
        self.health_drain_timer = 0
        self.health_drain_interval = 20.0  # Drain health every 20 seconds when dirty
        self.health_drain_amount = 10  # Drain 10 health points
        
        # Load sprites
        self.load_sprites()
        
        # Animation
        self.animation_index = 0
        self.animation_timer = 0
        self.animation_speed = 0.15  # Much slower animation speed
        
        # Direction
        self.facing_right = True
        
        # Sound effects
        self.last_walk_sound = 0
        self.walk_sound_interval = 0.5  # Play walk sound every 0.5 seconds
        self.last_jump_sound = 0
        self.jump_sound_cooldown = 0.1  # Prevent jump sound spam
        
        # Health
        self.health = 100
        self.max_health = 100
        
        # Knife system
        self.knives_thrown = []
        self.knives_collected = 3
        self.can_throw = True

    def load_sprites(self):
        """Load and process sprite sheets efficiently"""
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
        
        # Handle idle sprite (single image)
        if os.path.exists(sprite_paths['idle']):
            sprite = pygame.image.load(sprite_paths['idle']).convert_alpha()
            scaled_sprite = pygame.transform.scale(sprite, (self.width, self.height))
            self.sprite_frames['idle'] = [scaled_sprite]
            print(f"Loaded player sprite: {sprite_paths['idle']} -> Size: {scaled_sprite.get_width()}x{scaled_sprite.get_height()}")
        else:
            # Create a simple colored rectangle as fallback
            fallback_surface = pygame.Surface((self.width, self.height))
            fallback_surface.fill((255, 0, 0))  # Red rectangle
            self.sprite_frames['idle'] = [fallback_surface]
            print(f"Created fallback sprite: {self.width}x{self.height}")
        
        # Handle animated sprites
        for key, paths in sprite_paths.items():
            if key == 'idle':  # Skip idle as it's already handled
                continue
                
            frames = []
            for path in paths:
                if os.path.exists(path):
                    # Load individual sprite frame
                    sprite = pygame.image.load(path).convert_alpha()
                    # Scale the sprite to player size
                    scaled_sprite = pygame.transform.scale(sprite, (self.width, self.height))
                    frames.append(scaled_sprite)
            
            if frames:
                self.sprite_frames[key] = frames
            else:
                # Use idle sprite as fallback
                self.sprite_frames[key] = self.sprite_frames['idle']

        self.current_sprite = self.sprite_frames['idle'][0]

    def play_sound(self, sound_name, game_sounds):
        """Play a sound effect if available"""
        if sound_name in game_sounds:
            try:
                game_sounds[sound_name].play()
            except:
                pass  # Ignore sound errors

    def update(self, dt, ground_tiles, climb_tiles):
        """Update player physics and input"""
        # Handle input
        keys = pygame.key.get_pressed()
        
        # Handle normal movement
        self.handle_normal_movement(keys, dt)
        
        # Apply gravity
        self.vel_y += self.gravity * dt
        
        # Limit fall speed to prevent skipping through tiles
        if self.vel_y > self.max_fall_speed:
            self.vel_y = self.max_fall_speed
        
        # Update position
        self.x += self.vel_x * dt
        self.y += self.vel_y * dt
        
        # Clamp player to map boundaries
        map_width = 1920  # 60 tiles * 32 pixels
        map_height = 960  # 30 tiles * 32 pixels
        
        # Clamp X position
        self.x = max(0, min(self.x, map_width - self.width))
        
        # Clamp Y position
        self.y = max(0, min(self.y, map_height - self.height))
        
        # Clamp player position to map bounds
        ground_level = 928  # Ground is at Y=29 * 32 = 928 pixels
        if self.y > ground_level:
            self.y = ground_level - self.height  # Position player on top of ground
            self.vel_y = 0
            self.on_ground = True
        
        # Check collisions
        if ground_tiles:
            self.check_horizontal_collisions(ground_tiles)
            self.check_vertical_collisions(ground_tiles)
        else:
            print("No collision grid provided!")
        
        # Update dash
        if self.is_dashing:
            self.dash_timer -= dt
            if self.dash_timer <= 0:
                self.is_dashing = False
        
        if self.dash_cooldown_timer > 0:
            self.dash_cooldown_timer -= dt
        
        # Update health system
        self.update_health_system(dt)
        
        # Update animation
        self.update_animation(dt)
        
        # Update knives
        for knife in self.knives_thrown[:]:
            knife['x'] += knife['vel_x'] * dt
            knife['y'] += knife['vel_y'] * dt
            knife['timer'] -= dt
            
            # Remove knives that have expired
            if knife['timer'] <= 0:
                self.knives_thrown.remove(knife)

    def update_health_system(self, dt):
        """Update health and cleanliness system"""
        # Update cleanliness timer
        if self.is_dirty:
            self.dirt_timer -= dt
            if self.dirt_timer <= 0:
                self.is_dirty = False
                print("You are no longer dirty!")
        
        # Update health drain when dirty
        if self.is_dirty:
            self.health_drain_timer += dt
            if self.health_drain_timer >= self.health_drain_interval:
                self.health_drain_timer = 0
                self.max_health = max(0, self.max_health - self.health_drain_amount)
                print(f"Health drained by {self.health_drain_amount} due to dirtiness!")
                if self.max_health <= 0:
                    print("You died from dirtiness!")
    
    def make_dirty(self):
        """Make the player dirty"""
        self.is_dirty = True
        self.dirt_timer = 0.0
        print("You got dirty!")
    
    def clean_up(self):
        """Clean the player"""
        self.is_dirty = False
        self.dirt_timer = 30.0  # 30 seconds of cleanliness
        print("You are now clean!")

    def handle_dash(self, keys, dt):
        """Handle dash mechanics"""
        if keys[pygame.K_d] and not self.is_dashing and self.dash_cooldown_timer <= 0:
            self.is_dashing = True
            self.dash_timer = self.dash_duration
            self.dash_cooldown_timer = self.dash_cooldown

        if self.is_dashing:
            dash_direction = 1 if self.facing_right else -1
            self.x += dash_direction * self.dash_speed
            self.dash_timer -= dt
            if self.dash_timer <= 0:
                self.is_dashing = False

    def handle_normal_movement(self, keys, dt):
        """Handle normal movement with direct input response"""
        # Direct movement input
        if keys[pygame.K_LEFT]:
            self.vel_x = -self.speed
            self.facing_right = False
        elif keys[pygame.K_RIGHT]:
            self.vel_x = self.speed
            self.facing_right = True
        else:
            # Stop horizontal movement when no keys pressed
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
        if abs(self.vel_x) > 5 and self.on_ground:
            self.last_walk_sound += dt
            if self.last_walk_sound >= self.walk_sound_interval:
                self.play_sound('walk', getattr(self, 'game_sounds', {}))
                self.last_walk_sound = 0

    # def handle_knife_throwing(self, keys):
    #     """Handle knife throwing"""
    #     if keys[pygame.K_f] and self.knives_available > 0:
    #         # Create new knife
    #         knife_x = self.x + (self.width if self.facing_right else 0)
    #         knife_y = self.y + self.height // 2
    #         direction = 1 if self.facing_right else -1
            
    #         new_knife = Knife(knife_x, knife_y, direction)
    #         self.knives_thrown.append(new_knife)
    #         self.knives_available -= 1

    # def update_knives(self, dt):
    #     """Update thrown knives"""
    #     for knife in self.knives_thrown[:]:
    #         knife.update(dt)
    #         # Remove knives that are off-screen or hit something
    #         if (knife.x < 0 or knife.x > 160 * 16 or 
    #             knife.y < 0 or knife.y > 65 * 16):
    #             self.knives_thrown.remove(knife)

    # def clamp_to_map(self):
    #     """Clamp player position to map bounds"""
    #     # Simple map bounds (adjust based on your map size)
    #     max_x = 160 * 16 - self.width  # 160 tiles * 16 pixels
    #     max_y = 65 * 16 - self.height   # 65 tiles * 16 pixels
        
    #     self.x = max(0, min(self.x, max_x))
    #     self.y = max(0, min(self.y, max_y))

    # def throw_knife(self):
    #     """Throw a knife"""
    #     knife_start_x = self.x + self.width if self.facing_right else self.x - 20
    #     knife_start_y = self.y + self.height // 2
    #     direction = 1 if self.facing_right else -1
    #     new_knife = Knife(knife_start_x, knife_start_y, direction)
    #     self.knives_thrown.append(new_knife)
        # self.knives_collected -= 1

    def draw(self, screen, camera_x, camera_y):
        """Draw the player using loaded sprites"""
        # Use the current sprite if available, otherwise draw a fallback rectangle
        if hasattr(self, 'current_sprite') and self.current_sprite:
            screen.blit(self.current_sprite, (self.x - camera_x, self.y - camera_y))
        else:
            # Fallback: Draw player as a bright blue rectangle
            player_rect = pygame.Rect(self.x - camera_x, self.y - camera_y, self.width, self.height)
            pygame.draw.rect(screen, (0, 100, 255), player_rect)  # Bright blue color
            # Draw a border around the player
            pygame.draw.rect(screen, (255, 255, 255), player_rect, 2)  # White border

    @property
    def rect(self):
        """Get player rectangle for collision detection"""
        return pygame.Rect(self.x, self.y, self.width, self.height)

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
                            if self.vel_x > 0 or self.is_dashing:
                                self.x = tile_rect.left - self.width
                            elif self.vel_x < 0 or self.is_dashing:
                                self.x = tile_rect.right

    def check_vertical_collisions(self, tiles):
        """Check vertical collisions with tiles"""
        self.on_ground = False
        player_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        tile_size = 32  # Updated to match TMX tile size
        
        # Only check tiles near the player to improve performance
        player_tile_x = int(self.x // tile_size)
        player_tile_y = int(self.y // tile_size)
        
        # Check a larger area around the player to ensure we don't miss collisions
        start_x = max(0, player_tile_x - 3)
        end_x = min(len(tiles[0]), player_tile_x + 5)
        start_y = max(0, player_tile_y - 3)
        end_y = min(len(tiles), player_tile_y + 5)
        
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                if y < len(tiles) and x < len(tiles[0]):
                    tile_gid = tiles[y][x]
                    if tile_gid != 0:
                        tile_rect = pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)
                        if player_rect.colliderect(tile_rect):
                            if self.vel_y > 0:
                                # Landing on top of a tile
                                self.y = tile_rect.top - self.height
                                self.vel_y = 0
                                self.on_ground = True
                                self.jump_count = 0
                            elif self.vel_y < 0:
                                # Hitting head on a tile
                                self.y = tile_rect.bottom
                                self.vel_y = 0
        
        # Additional check: if player is very close to ground, consider them on ground
        if not self.on_ground and self.vel_y >= 0:
            # Check if player is within 2 pixels of the ground
            ground_y = 928  # Ground level
            if abs(self.y + self.height - ground_y) <= 2:
                self.y = ground_y - self.height
                self.vel_y = 0
                self.on_ground = True
                self.jump_count = 0

    def update_animation(self, dt):
        """Update animation state and current sprite"""
        # Determine state with better thresholds
        if not self.on_ground:
            state = 'jump'
        elif abs(self.vel_x) > 5:  # Higher threshold for movement detection
            state = 'run'
        else:
            state = 'idle'
        
        # Only update animation timer for animated states (not idle)
        if state != 'idle':
            self.animation_timer += dt
            
            # Slower animation speed
            if self.animation_timer >= 0.1:  # Much slower animation
                self.animation_timer = 0
                if state in self.sprite_frames and self.sprite_frames[state]:
                    self.animation_index = (self.animation_index + 1) % len(self.sprite_frames[state])
        else:
            # For idle, always use the first frame and reset animation
            self.animation_index = 0
            self.animation_timer = 0
        
        # Set current sprite
        if state in self.sprite_frames and self.sprite_frames[state]:
            if state == 'idle':
                # For idle, always use the first (and only) frame
                self.current_sprite = self.sprite_frames[state][0]
            else:
                # For animated states, ensure index is within bounds
                if self.animation_index >= len(self.sprite_frames[state]):
                    self.animation_index = 0
                self.current_sprite = self.sprite_frames[state][self.animation_index]
        else:
            # Fallback to idle sprite
            if 'idle' in self.sprite_frames and self.sprite_frames['idle']:
                self.current_sprite = self.sprite_frames['idle'][0]
            else:
                # Create a fallback sprite if no sprites are loaded
                self.current_sprite = pygame.Surface((self.width, self.height))
                self.current_sprite.fill((255, 0, 0))
