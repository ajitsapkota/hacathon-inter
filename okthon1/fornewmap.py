import pygame
import sys
import time
import xml.etree.ElementTree as ET
import os
import json
import math
from player import Player
from dialogue import DialogueBox
from coin import Coin
from entities import Knife, KnifePickup
from npc import NPC
from medicine import Medicine
from trash_item import TrashItem, Dustbin
from item_system import Inventory

class Game:
    def __init__(self):
        """Initialize the game"""
        pygame.init()
        
        # Performance detection
        self.detect_performance_settings()
        
        # Setup resolution
        self.setup_resolution()
        
        # Initialize game objects
        self.clock = pygame.time.Clock()
        self.paused = False
        
        # Scale factors (updated by setup_resolution)
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.scale_factor = 1.0
        
        # UI settings
        self.font_size = int(24 * self.scale_factor)
        self.ui_padding = int(20 * self.scale_factor)
        
        # Performance monitoring
        self.frame_times = []
        self.last_frame_time = time.time()
        self.fps = 60.0  # Initialize FPS
        
        # Tile cache for performance
        self.tile_cache = {}
        
        # Load game assets
        self.load_game_assets()
        
        # Load sound effects
        self.load_sound_effects()
        
        # Initialize game state
        self.reset_game()

    def detect_performance_settings(self):
        """Detect system performance capabilities"""
        try:
            if self.screen_width >= 1920 and self.screen_height >= 1080:
                self.performance_level = "high"
            elif self.screen_width >= 1366 and self.screen_height >= 768:
                self.performance_level = "medium"
            else:
                self.performance_level = "low"
        except:
            self.performance_level = "low"

    def setup_resolution(self):
        """Setup game resolution to match map size"""
        # Map size: 60x30 tiles, 32x32 pixels each
        self.screen_width = 60 * 32  # 1920 pixels
        self.screen_height = 30 * 32  # 960 pixels
        
        # Create screen with map dimensions
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Trash Collection Game")
        
        # No scaling needed - 1:1 pixel mapping
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.scale_factor = 1.0
        
        print(f"Window size: {self.screen_width}x{self.screen_height}")
        print(f"Map size: {self.screen_width}x{self.screen_height}")
        print(f"Scale factors: X={self.scale_x:.2f}, Y={self.scale_y:.2f}")

    def load_game_assets(self):
        """Load all game assets"""
        # Load map data
        self.map_data = self.load_tmx_map_with_tilesets('mapps/Legacy-Fantasy - High Forest 2.3/finalmap.tmx')
        self.collision_grid = self.create_collision_grid()
        
        # Initialize game objects
        self.player = Player(self.screen_width, self.screen_height)
        self.npc = NPC(self.screen_width, self.screen_height)
        self.enemies = []
        self.trash_items = []
        self.dustbins = []
        
        print("Game assets loaded successfully!")
        
        # Pass sounds to player after loading
        if hasattr(self, 'sounds'):
            self.player.game_sounds = self.sounds

    def load_sound_effects(self):
        """Load sound effects for the game"""
        self.sounds = {}
        
        # Sound effect paths
        sound_paths = {
            'walk': 'sfx/walk.mp3',
            'jump': 'sfx/jump_07-80241.mp3',
            'coin': 'sfx/coin-257878.mp3',
            'die': 'sfx/die-246012.mp3',
            'damage': 'sfx/take-damage-163912.mp3',
            'drink': 'sfx/drink-nilo.mp3',
            'background': 'sfx/the bg.mp3'
        }
        
        # Load sound effects
        for sound_name, sound_path in sound_paths.items():
            try:
                if os.path.exists(sound_path):
                    self.sounds[sound_name] = pygame.mixer.Sound(sound_path)
                    print(f"Loaded sound: {sound_name}")
                else:
                    print(f"Sound file not found: {sound_path}")
            except Exception as e:
                print(f"Error loading sound {sound_name}: {e}")
        
        # Start background music
        try:
            if 'background' in self.sounds:
                self.sounds['background'].play(-1)  # Loop background music
                print("Background music started")
        except Exception as e:
            print(f"Error playing background music: {e}")

    def load_tmx_map_with_tilesets(self, tmx_file):
        """Load TMX map with proper tileset handling"""
        tree = ET.parse(tmx_file)
        root = tree.getroot()
        
        # Get map properties
        map_width = int(root.get('width'))
        map_height = int(root.get('height'))
        tile_width = int(root.get('tilewidth'))
        tile_height = int(root.get('tileheight'))
        
        # Load tilesets
        self.tilesets = {}
        for tileset in root.findall('tileset'):
            firstgid = int(tileset.get('firstgid'))
            source = tileset.get('source')
            
            # Load tileset image
            if source:
                # Handle relative paths
                if source.startswith('2.tsx'):
                    tileset_image = 'mapps/Tiles.png'
                elif source.startswith('4.tsx'):
                    tileset_image = 'mapps/Background.png'
                else:
                    tileset_image = 'mapps/Tiles.png'  # Default
                
                if os.path.exists(tileset_image):
                    tileset_surface = pygame.image.load(tileset_image).convert_alpha()
                    self.tilesets[firstgid] = {
                        'image': tileset_surface,
                        'tilewidth': 32,
                        'tileheight': 32,
                        'columns': tileset_surface.get_width() // 32,
                        'name': source,
                        'firstgid': firstgid
                    }
                    print(f"Loaded tileset: {source} (GID {firstgid}) - Image size: {tileset_surface.get_width()}x{tileset_surface.get_height()}")
                else:
                    print(f"Warning: Tileset image not found: {tileset_image}")
        
        # Load layers
        layers = []
        for layer in root.findall('layer'):
            layer_data = {
                'name': layer.get('name'),
                'width': int(layer.get('width')),
                'height': int(layer.get('height')),
                'data': []
            }
            
            data_elem = layer.find('data')
            if data_elem is not None:
                csv_data = data_elem.text.strip()
                layer_data['data'] = [int(x) for x in csv_data.split(',') if x.strip()]
            
            layers.append(layer_data)
        
        # Load object groups
        object_groups = {}
        for objectgroup in root.findall('objectgroup'):
            group_name = objectgroup.get('name')
            objects = []
            
            for obj in objectgroup.findall('object'):
                obj_data = {
                    'id': int(obj.get('id')),
                    'x': float(obj.get('x')),
                    'y': float(obj.get('y')),
                    'width': float(obj.get('width', 0)),
                    'height': float(obj.get('height', 0))
                }
                objects.append(obj_data)
            
            object_groups[group_name] = objects
        
        return {
            'width': map_width,
            'height': map_height,
            'tilewidth': tile_width,
            'tileheight': tile_height,
            'layers': layers,
            'object_groups': object_groups
        }

    def get_tileset_for_gid(self, gid):
        """Get the appropriate tileset for a given GID"""
        if gid == 0:
            return None
            
        # Find the tileset with the highest firstgid that's <= gid
        best_tileset = None
        best_firstgid = 0
        
        for firstgid, tileset in self.tilesets.items():
            if firstgid <= gid and firstgid > best_firstgid:
                best_tileset = tileset
                best_firstgid = firstgid
        
        return best_tileset

    def get_player_spawn_point(self):
        """Get the player spawn point from the TMX object group"""
        if 'object_groups' in self.map_data and 'player' in self.map_data['object_groups']:
            player_objects = self.map_data['object_groups']['player']
            if player_objects:
                spawn = player_objects[0]
                # Use exact coordinates from TMX map but adjust Y to be right above ground
                x = spawn['x']
                y = 900  # Spawn right above ground level (ground is at Y=928)
                print(f"Player spawn point from TMX: {x}, {y}")
                return x, y
        
        # Fallback to default spawn point
        print("Using fallback spawn point")
        return 100, 900  # Spawn right above ground level

    def create_collision_grid(self):
        """Create collision grid from ground layer"""
        grid = [[0 for _ in range(self.map_data['width'])] for _ in range(self.map_data['height'])]
        
        # Get ground layer
        ground_layer = next((l for l in self.map_data['layers'] if l['name'] == 'ground'), None)
        
        if ground_layer:
            solid_tiles = 0
            print(f"Ground layer found: {ground_layer['name']}")
            print(f"Ground layer dimensions: {ground_layer['width']}x{ground_layer['height']}")
            print(f"Ground layer data length: {len(ground_layer['data'])}")
            
            for y in range(self.map_data['height']):
                for x in range(self.map_data['width']):
                    index = y * ground_layer['width'] + x
                    if index < len(ground_layer['data']):
                        gid = ground_layer['data'][index]
                        if gid != 0:
                            grid[y][x] = 1  # Solid tile
                            solid_tiles += 1
            
            print(f"Created collision grid with {solid_tiles} solid tiles")
            print(f"Grid dimensions: {len(grid)}x{len(grid[0])}")
            
            # Print some sample ground tiles around the expected ground level
            ground_y = 25  # Expected ground level (around y=800 in pixels)
            print(f"Sample ground tiles at Y={ground_y}:")
            for x in range(0, min(10, len(grid[0]))):  # First 10 tiles
                print(f"  Tile at ({x}, {ground_y}): {grid[ground_y][x]}")
            
            # Also check the bottom rows where ground should be
            print(f"Sample ground tiles at Y=29 (bottom):")
            for x in range(0, min(10, len(grid[0]))):  # First 10 tiles
                print(f"  Tile at ({x}, 29): {grid[29][x]}")
        else:
            print("No ground layer found for collision grid")
            print("Available layers:")
            for layer in self.map_data['layers']:
                print(f"  - {layer['name']}")
        
        return grid

    def load_coins(self):
        """Load coin assets and initialize coin objects"""
        coin_image = pygame.image.load('tiled/PNG/Items/blue diamond.png').convert_alpha()
        coin_size = int(32 * self.scale_factor)
        coin_image = pygame.transform.scale(coin_image, (coin_size, coin_size))
        
        coins = [
            Coin(900 * self.scale_x, 930 * self.scale_y, coin_image),
            Coin(700 * self.scale_x, 300 * self.scale_y, coin_image),
            Coin(1000 * self.scale_x, 320 * self.scale_y, coin_image),
        ]
        return coins

    def render_map(self):
        """Render the TMX map with all layers"""
        # Get all layers and sort them by name for proper rendering order
        all_layers = self.map_data['layers']
        
        # Sort layers: background first, then ground
        layers_sorted = sorted(all_layers, key=lambda x: x['name'])
        
        # Calculate tile dimensions
        tile_width = self.map_data['tilewidth']
        tile_height = self.map_data['tileheight']
        
        # Render all layers
        for layer in layers_sorted:
            tiles_rendered = 0
            for y in range(self.map_data['height']):
                for x in range(self.map_data['width']):
                    index = y * layer['width'] + x
                    if index < len(layer['data']):
                        gid = layer['data'][index]
                        if gid != 0:
                            tileset = self.get_tileset_for_gid(gid)
                            if tileset:
                                # Calculate tile position
                                local_tid = gid - tileset.get('firstgid', 0)
                                if local_tid >= 0:  # Ensure valid local tile ID
                                    tile_x = (local_tid % tileset['columns']) * tileset['tilewidth']
                                    tile_y = (local_tid // tileset['columns']) * tileset['tileheight']
                                    
                                    screen_x = x * tile_width - self.camera_x
                                    screen_y = y * tile_height - self.camera_y

                                    # Only render tiles that are visible on screen
                                    if -tile_width <= screen_x < self.screen.get_width() and -tile_height <= screen_y < self.screen.get_height():
                                        # Use tile cache for performance
                                        cache_key = f"{tileset['name']}_{local_tid}"
                                        
                                        if cache_key not in self.tile_cache:
                                            try:
                                                tile_surface = pygame.Surface((tile_width, tile_height), pygame.SRCALPHA)
                                                tile_surface.blit(tileset['image'], (0, 0),
                                                                  (tile_x, tile_y, tile_width, tile_height))
                                                self.tile_cache[cache_key] = tile_surface
                                            except Exception as e:
                                                continue
                                        else:
                                            tile_surface = self.tile_cache[cache_key]
                                        
                                        self.screen.blit(tile_surface, (screen_x, screen_y))
                                        tiles_rendered += 1

    def update_performance_monitoring(self):
        """Update performance monitoring"""
        current_time = time.time()
        frame_time = current_time - self.last_frame_time
        self.frame_times.append(frame_time)
        
        # Keep only last 60 frames
        if len(self.frame_times) > 60:
            self.frame_times.pop(0)
        
        self.last_frame_time = current_time
        
        # Calculate average FPS
        if len(self.frame_times) > 0:
            avg_frame_time = sum(self.frame_times) / len(self.frame_times)
            fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0
            # Print FPS every 120 frames (once per 4 seconds at 30 FPS)
            if hasattr(self, '_fps_counter'):
                self._fps_counter += 1
            else:
                self._fps_counter = 0
                
            if self._fps_counter % 120 == 0:
                print(f"FPS: {fps:.1f}")

    def draw_ui(self):
        """Draw UI elements"""
        # Cache font to avoid recreating it every frame
        if not hasattr(self, '_ui_font'):
            try:
                self._ui_font = pygame.font.SysFont('Arial', self.font_size, bold=True)
            except:
                self._ui_font = pygame.font.SysFont(None, self.font_size)
        
        # Draw health and lives
        health_percentage = self.player.health / self.player.max_health
        health_width = 200
        health_height = 20
        
        # Health bar background
        pygame.draw.rect(self.screen, (100, 100, 100), (10, 10, health_width, health_height))
        # Health bar fill
        health_fill_width = int(health_width * health_percentage)
        health_color = (255, 0, 0) if health_percentage < 0.3 else (255, 255, 0) if health_percentage < 0.7 else (0, 255, 0)
        pygame.draw.rect(self.screen, health_color, (10, 10, health_fill_width, health_height))
        # Health bar border
        pygame.draw.rect(self.screen, (255, 255, 255), (10, 10, health_width, health_height), 2)
        
        # Health text
        health_text = f"Health: {self.player.health}/{self.player.max_health}"
        health_surface = self._ui_font.render(health_text, True, (255, 255, 255))
        self.screen.blit(health_surface, (10, 35))
        
        # Lives text
        lives_text = f"Lives: {self.player.lives}"
        lives_surface = self._ui_font.render(lives_text, True, (255, 255, 255))
        self.screen.blit(lives_surface, (10, 60))
        
        # Cleanliness status
        cleanliness_text = f"Clean: {'Yes' if not self.player.is_dirty else 'No'}"
        cleanliness_surface = self._ui_font.render(cleanliness_text, True, (255, 255, 255))
        self.screen.blit(cleanliness_surface, (10, 85))
        
        # FPS counter (top right)
        fps_text = f"FPS: {self.fps:.1f}"
        fps_surface = self._ui_font.render(fps_text, True, (255, 255, 255))
        self.screen.blit(fps_surface, (self.screen.get_width() - 100, 20))
        
        # Draw dustbin image at right corner, 60% from top
        try:
            dustbin_image = pygame.image.load('game images/dustbin.jpeg').convert_alpha()
            dustbin_width = int(dustbin_image.get_width() * 0.5)
            dustbin_height = int(dustbin_image.get_height() * 0.5)
            dustbin_image = pygame.transform.scale(dustbin_image, (dustbin_width, dustbin_height))
            dustbin_x = self.screen.get_width() - dustbin_width - 10
            dustbin_y = int(self.screen.get_height() * 0.6)
            self.screen.blit(dustbin_image, (dustbin_x, dustbin_y))
        except Exception as e:
            print(f"Error loading dustbin image: {e}")
        
        # UI elements for bottom of screen
        ui_elements = []
        
        # Add health and cleanliness info
        ui_elements.append(f"Health: {self.player.health}/{self.player.max_health}")
        ui_elements.append(f"Lives: {self.player.lives}")
        ui_elements.append(f"Clean: {'Yes' if not self.player.is_dirty else 'No'}")
        ui_elements.append(f"FPS: {self.fps:.1f}")
        
        # Add trash collection info
        if self.held_trash is not None:
            ui_elements.append("Holding trash - Press T to throw, D to drop")
        
        # Add NPC quest info
        if hasattr(self, 'npc') and self.npc:
            if self.npc.quest_completed:
                quest_status = "Quest Completed!"
            elif self.npc.quest_accepted:
                quest_status = f"Quest: {self.npc.collected_items}/{self.npc.required_items} medicine"
            else:
                quest_status = "Quest: Talk to NPC (E)"
            ui_elements.append(quest_status)
        
        # Add control hints
        controls_text = [
            "I: Inventory | T: Throw | D: Drop | E: Dialogue",
            "SPACE: Jump | SHIFT: Dash"
        ]
        
        for i, text in enumerate(controls_text):
            controls_surface = self._ui_font.render(text, True, (255, 255, 255))
            self.screen.blit(controls_surface, (10, self.screen.get_height() - 60 + i * 25))

    def reset_game(self):
        """Reset game state"""
        # Initialize game state
        self.lives = 3
        self.max_health = 100
        self.score = 0
        
        # Get player spawn point from TMX
        spawn_point = self.get_player_spawn_point()
        
        # Initialize regular player at spawn point or default position
        if spawn_point:
            print(f"Player spawn point: {spawn_point[0]:.1f}, {spawn_point[1]:.1f}")
            self.player = Player(spawn_point[0], spawn_point[1], 2.0)  # Use regular Player
        else:
            # Default spawn position for full-screen map - spawn above ground
            # Ground level is around y=1000, so spawn at y=800 to be above ground
            default_x = 100
            default_y = 800
            print(f"Default player spawn: {default_x:.1f}, {default_y:.1f}")
            self.player = Player(default_x, default_y, 2.0)  # Use regular Player
        
        # Pass sounds to player after loading
        if hasattr(self, 'sounds'):
            self.player.game_sounds = self.sounds
        
        # Initialize a separate NPC for quests (stationary)
        if 'npc' in self.map_data['object_groups']:
            npc_data = self.map_data['object_groups']['npc'][0]
            npc_x = npc_data['x'] * self.scale_x
            npc_y = (npc_data['y'] - 20) * self.scale_y  # Move NPC up slightly
            self.npc = NPC(npc_x, npc_y, self.scale_factor)
            # Make this NPC stationary (no movement)
            self.npc.speed = 0
            self.npc.jump_speed = 0
            self.npc.gravity = 0
        else:
            self.npc = NPC(self.player.x + 200, self.player.y - 50, self.scale_factor)
            # Make this NPC stationary
            self.npc.speed = 0
            self.npc.jump_speed = 0
            self.npc.gravity = 0

        # Initialize dialogue box
        self.dialogue_box = DialogueBox(self.screen.get_width(), self.screen.get_height(), 
                                       [("Narrator", "Welcome! Collect trash and throw it in dustbins!")])
        self.dialogue_timer = 3.0
        self.dialogue_auto_dismiss_time = 3.0
        
        # Initialize inventory
        self.inventory = Inventory()
        
        # Initialize coins
        self.coins = []
        for coin_data in self.map_data['object_groups'].get('coin', []):
            coin_x = coin_data['x'] * self.scale_x
            coin_y = coin_data['y'] * self.scale_y
            # Create a simple coin image (placeholder)
            coin_image = pygame.Surface((16, 16))
            coin_image.fill((255, 215, 0))  # Gold color
            self.coins.append(Coin(coin_x, coin_y, coin_image))
        
        # Initialize medicine items
        self.medicine_items = []
        medicine_positions = [
            (400, 400),
            (800, 300),
            (1200, 500)
        ]
        for x, y in medicine_positions:
            self.medicine_items.append(Medicine(x * self.scale_x, y * self.scale_y, self.scale_factor))
        
        # Initialize trash collection system
        self.trash_items = []
        self.dustbins = []
        self.held_trash = None
        self.trash_collected = 0
        self.total_trash = 0
        
        # Create trash items from TMX object group
        if 'trash' in self.map_data['object_groups']:
            for i, trash_data in enumerate(self.map_data['object_groups']['trash']):
                x = trash_data['x'] * self.scale_x
                y = (trash_data['y'] - 20) * self.scale_y  # Move items up slightly
                print(f"Trash {i+1}: {x:.1f}, {y:.1f}")
                # Use trash.jpeg and trash1.jpeg alternately
                image_path = f"game images/trash{'1' if i % 2 == 0 else ''}.jpeg"
                self.trash_items.append(TrashItem(x, y, image_path))
                self.total_trash += 1
        
        # Create dustbins from TMX object group
        if 'dustbin' in self.map_data['object_groups']:
            for dustbin_data in self.map_data['object_groups']['dustbin']:
                x = dustbin_data['x'] * self.scale_x
                y = (dustbin_data['y'] - 20) * self.scale_y  # Move dustbin up slightly
                self.dustbins.append(Dustbin(x, y, "game images/dustbin.jpeg"))
        
        # Create collectible items on the map
        self.collectible_items = []
        
        # Add water bottles to map
        if 'water bottle' in self.map_data['object_groups']:
            for water_data in self.map_data['object_groups']['water bottle']:
                x = water_data['x'] * self.scale_x
                y = (water_data['y'] - 20) * self.scale_y
                self.collectible_items.append({
                    'type': 'water',
                    'x': x,
                    'y': y,
                    'image_path': 'game images/water.jpeg',
                    'collected': False
                })
                print(f"Water bottle at: {x:.1f}, {y:.1f}")
        
        # Add first aid to map
        if 'first aid' in self.map_data['object_groups']:
            for aid_data in self.map_data['object_groups']['first aid']:
                x = aid_data['x'] * self.scale_x
                y = (aid_data['y'] - 20) * self.scale_y
                self.collectible_items.append({
                    'type': 'first_aid',
                    'x': x,
                    'y': y,
                    'image_path': 'game images/first aid.jpeg',
                    'collected': False
                })
                print(f"First aid at: {x:.1f}, {y:.1f}")
        
        # Add soap to map
        if 'soap' in self.map_data['object_groups']:
            for soap_data in self.map_data['object_groups']['soap']:
                x = soap_data['x'] * self.scale_x
                y = (soap_data['y'] - 20) * self.scale_y
                self.collectible_items.append({
                    'type': 'soap',
                    'x': x,
                    'y': y,
                    'image_path': 'game images/soap.jpeg',
                    'collected': False
                })
                print(f"Soap at: {x:.1f}, {y:.1f}")
        
        # Add items to inventory based on TMX object groups with correct images
        if 'water bottle' in self.map_data['object_groups']:
            for water_data in self.map_data['object_groups']['water bottle']:
                self.inventory.add_item("water", 1)
        
        if 'first aid' in self.map_data['object_groups']:
            for aid_data in self.map_data['object_groups']['first aid']:
                self.inventory.add_item("first_aid", 1)
        
        if 'soap' in self.map_data['object_groups']:
            for soap_data in self.map_data['object_groups']['soap']:
                self.inventory.add_item("soap", 1)
        
        # Quest system
        self.quest_active = False
        self.medicine_collected = 0
        self.medicine_required = 3
        
        # Initialize camera
        self.camera_x = 0
        self.camera_y = 0
        self.update_camera()

    def run(self):
        """Main game loop"""
        running = True
        dt = 0.016  # Initialize dt with a default value
        
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    self.handle_keydown(event)
                elif event.type == pygame.VIDEORESIZE:
                    self.handle_resize(event.w, event.h)
            
            if not self.paused:
                self.update_game(dt)
                self.render()
            
            # Cap at 60 FPS for better performance
            dt = self.clock.tick(60) / 1000.0
            
            pygame.display.flip()
        
        pygame.quit()
        sys.exit()

    def handle_keydown(self, event):
        """Handle key press events"""
        if event.key == pygame.K_ESCAPE:
            # Exit fullscreen or quit game
            pygame.quit()
            sys.exit()
        elif event.key == pygame.K_r:
            # Restart game
            self.reset_game()
        elif event.key == pygame.K_q:
            # Quit game
            pygame.quit()
            sys.exit()
        elif event.key in (pygame.K_SPACE, pygame.K_UP) and not self.paused:
            # Handle jump
            pass
        elif event.key == pygame.K_i:
            # Toggle inventory
            self.inventory.toggle()
        elif event.key == pygame.K_t and not self.paused:
            # Throw trash handled in handle_trash_input
            # No action needed here as trash throwing is handled in handle_trash_input()
            pass
        elif event.key == pygame.K_e and not self.paused:
            # Interact with NPC/dialogue
            self.interact_with_npc()
        elif event.key == pygame.K_c and not self.paused:
            # Climbing handled in player update
            # No action needed here as climbing is handled in player.update()
            pass

    def interact_with_npc(self):
        """Handle NPC interaction"""
        if not self.npc.quest_accepted:
            # Offer quest
            dialogue_lines = self.npc.get_dialogue(self.player)
            self.dialogue_box = DialogueBox(self.screen.get_width(), self.screen.get_height(), dialogue_lines)
            self.dialogue_timer = 0
        elif self.npc.quest_accepted and not self.npc.quest_completed:
            # Check if quest can be completed
            if self.medicine_collected >= self.medicine_required:
                self.npc.collected_items = self.medicine_collected
                dialogue_lines = self.npc.complete_quest()
                if dialogue_lines:
                    self.dialogue_box = DialogueBox(self.screen.get_width(), self.screen.get_height(), dialogue_lines)
                    self.dialogue_timer = 0
                    self.quest_active = False
            else:
                # Show progress
                dialogue_lines = self.npc.get_dialogue(self.player)
                self.dialogue_box = DialogueBox(self.screen.get_width(), self.screen.get_height(), dialogue_lines)
                self.dialogue_timer = 0

    def update_game(self, dt):
        """Update game logic"""
        # Update player with input
        self.player.update(dt, self.collision_grid, None)
        
        # Update camera to follow player
        self.update_camera()
        
        # Update dialogue timer
        if self.dialogue_box.is_active():
            self.dialogue_box.update(dt)
            if self.dialogue_timer > 0:
                self.dialogue_timer -= dt
                if self.dialogue_timer <= 0:
                    self.dialogue_box.active = False
        
        # Check medicine collection
        self.check_medicine_collection()
        
        # Check trash collection with health effects
        self.check_trash_collection_with_health()
        
        # Update performance monitoring
        self.update_performance_monitoring()
        
        # Update stationary NPC (quest giver)
        self.npc.update_quest_progress(self.player)
        
        # Update inventory
        keys = pygame.key.get_pressed()
        self.inventory.handle_input(keys, self.player)
        
        # Update trash items
        for trash in self.trash_items:
            trash.update(dt)
        
        # Update dustbins
        for dustbin in self.dustbins:
            dustbin.update(dt)
        
        # Handle trash input
        self.handle_trash_input(keys)

    def check_medicine_collection(self):
        """Check if player has collected medicine items"""
        # Only check medicine collection every few frames to reduce lag
        if hasattr(self, '_medicine_check_counter'):
            self._medicine_check_counter += 1
        else:
            self._medicine_check_counter = 0
            
        # Check every 10 frames (at 30 FPS = 3 times per second)
        if self._medicine_check_counter % 10 == 0:
            for medicine in self.medicine_items:
                if medicine.check_collision(self.player):
                    self.medicine_collected += 1
                    self.quest_active = True
                    self.npc.collected_items = self.medicine_collected
                    print(f"Medicine collected! {self.medicine_collected}/{self.medicine_required}")
    
    def check_trash_collection_with_health(self):
        """Check for trash collection and health effects"""
        # Check for collectible items
        for item in self.collectible_items:
            if not item['collected']:
                item_rect = pygame.Rect(item['x'], item['y'], 32, 32)
                if item_rect.colliderect(self.player.rect):
                    item['collected'] = True
                    if item['type'] == 'water':
                        self.inventory.add_item("water", 1)
                        print(f"Collected water bottle!")
                    elif item['type'] == 'first_aid':
                        self.inventory.add_item("first_aid", 1)
                        print(f"Collected first aid!")
                    elif item['type'] == 'soap':
                        self.inventory.add_item("soap", 1)
                        print(f"Collected soap!")
        
        # Check for trash items and health effects
        for trash in self.trash_items:
            if not trash.collected:
                # Check if player is near trash (within 20 pixels)
                distance = ((self.player.x - trash.x) ** 2 + (self.player.y - trash.y) ** 2) ** 0.5
                if distance <= 20:
                    # Player is near trash - decrease health
                    if self.player.is_dirty:
                        self.player.health_drain_timer += 1/60  # Assuming 60 FPS
                        if self.player.health_drain_timer >= 20.0:  # Every 20 seconds
                            self.player.health = max(0, self.player.health - 10)
                            self.player.health_drain_timer = 0
                            print("Health decreased due to being near trash!")
                
                # Check for trash collection
                if self.held_trash is None and trash.rect.colliderect(self.player.rect):
                    self.held_trash = trash
                    trash.collected = True
                    print("Picked up trash!")
        
        # Check for dustbin interaction
        for dustbin in self.dustbins:
            if self.held_trash is not None and dustbin.rect.colliderect(self.player.rect):
                self.held_trash = None
                print("Threw trash in dustbin!")
        
        # Check for stepping on dropped trash (health penalty)
        for trash in self.trash_items:
            if not trash.collected and trash.check_collision(self.player.rect):
                if self.player.is_dirty:
                    self.player.max_health = max(0, self.player.max_health - 3)
                    print("You stepped on trash while dirty! Health -3")
                else:
                    self.player.make_dirty()
                    print("You got dirty from stepping on trash!")

    def handle_trash_input(self, keys):
        """Handle trash-related input"""
        # Drop held trash with D key
        if keys[pygame.K_d] and self.held_trash is not None:
            # Drop trash near player
            self.held_trash.x = self.player.x + 50
            self.held_trash.y = self.player.y
            self.held_trash.collected = False
            self.held_trash = None
            print("Trash dropped!")
        
        # Throw held trash with T key
        if keys[pygame.K_t] and self.held_trash is not None:
            # Throw trash in the direction player is facing
            throw_distance = 100
            if self.player.facing_right:
                self.held_trash.x = self.player.x + throw_distance
            else:
                self.held_trash.x = self.player.x - throw_distance
            self.held_trash.y = self.player.y
            self.held_trash.collected = False
            self.held_trash = None
            print("Trash thrown!")

    def handle_resize(self, new_width, new_height):
        """Handle window resize"""
        self.game_width = new_width
        self.game_height = new_height
        self.screen = pygame.display.set_mode((new_width, new_height), pygame.RESIZABLE)
        
        # Recalculate scaling factors
        self.scale_x = self.game_width / 1280.0
        self.scale_y = self.game_height / 720.0
        self.scale_factor = min(self.scale_x, self.scale_y)
        
        # Update UI elements
        self.font_size = int(30 * self.scale_factor)
        self.ui_padding = int(20 * self.scale_factor)

    def render(self):
        """Main rendering function"""
        # Clear screen
        self.screen.fill((135, 206, 235))  # Sky blue background
        
        # Render all map layers properly
        self.render_map()
        
        # Draw UI
        self.draw_ui()
        
        # Render game objects
        self.player.draw(self.screen, self.camera_x, self.camera_y)
        
        # Render stationary NPC (quest giver)
        self.npc.draw(self.screen, self.camera_x, self.camera_y)
        
        # Render coins
        for coin in self.coins:
            coin.draw(self.screen, self.camera_x, self.camera_y)
        
        # Render medicine items
        for medicine in self.medicine_items:
            medicine.draw(self.screen, self.camera_x, self.camera_y)
        
        # Draw trash items
        for trash in self.trash_items:
            trash.draw(self.screen, self.camera_x, self.camera_y)
        
        # Draw dustbins
        for dustbin in self.dustbins:
            dustbin.draw(self.screen, self.camera_x, self.camera_y)
        
        # Draw collectible items
        for item in self.collectible_items:
            if not item['collected']:
                try:
                    # Load and scale the image
                    image = pygame.image.load(item['image_path']).convert_alpha()
                    image = pygame.transform.scale(image, (32, 32))
                    self.screen.blit(image, (item['x'] - self.camera_x, item['y'] - self.camera_y))
                except:
                    # Fallback if image not found
                    pygame.draw.rect(self.screen, (255, 255, 255), 
                                   (item['x'] - self.camera_x, item['y'] - self.camera_y, 32, 32))
        
        # Draw held trash (if any)
        if self.held_trash is not None:
            # Draw held trash above player
            held_x = self.player.x + 20
            held_y = self.player.y - 40
            self.screen.blit(self.held_trash.image, (held_x - self.camera_x, held_y - self.camera_y))
        
        # Render dialogue box
        if self.dialogue_box.is_active():
            self.dialogue_box.draw(self.screen)
        
        # Render inventory
        self.inventory.draw(self.screen, self.camera_x, self.camera_y)

    def render_ground_only(self):
        """Render only the ground layer for maximum performance"""
        # Draw UI
        self.draw_ui()

        # Get ground layer only
        ground_layer = next((l for l in self.map_data['layers'] if l['name'] == 'ground'), None)
        if not ground_layer:
            return

        # Calculate visible tile range for culling
        tile_width = self.map_data['tilewidth']
        tile_height = self.map_data['tileheight']
        
        # Very aggressive culling - only render exactly what's visible
        start_x = max(0, int(self.camera_x // tile_width))
        end_x = min(self.map_data['width'], int((self.camera_x + self.screen.get_width()) // tile_width) + 1)
        start_y = max(0, int(self.camera_y // tile_height))
        end_y = min(self.map_data['height'], int((self.camera_y + self.screen.get_height()) // tile_height) + 1)

        # Render only ground tiles
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                index = y * ground_layer['width'] + x
                if index < len(ground_layer['data']):
                    gid = ground_layer['data'][index]
                    if gid != 0:
                        tileset = self.get_tileset_for_gid(gid)
                        if tileset:
                            # Calculate tile position
                            local_tid = gid - tileset.get('firstgid', 0)
                            tile_x = (local_tid % tileset['columns']) * tileset['tilewidth']
                            tile_y = (local_tid // tileset['columns']) * tileset['tileheight']
                            
                            screen_x = x * tile_width - self.camera_x
                            screen_y = y * tile_height - self.camera_y

                            # Only render tiles that are visible on screen
                            if 0 <= screen_x < self.screen.get_width() and 0 <= screen_y < self.screen.get_height():
                                # Use tile cache for performance
                                cache_key = f"{tileset['name']}_{local_tid}"
                                
                                if cache_key not in self.tile_cache:
                                    tile_surface = pygame.Surface((tile_width, tile_height), pygame.SRCALPHA)
                                    tile_surface.blit(tileset['image'], (0, 0),
                                                      (tile_x, tile_y, tile_width, tile_height))
                                    self.tile_cache[cache_key] = tile_surface
                                else:
                                    tile_surface = self.tile_cache[cache_key]
                                
                                self.screen.blit(tile_surface, (screen_x, screen_y))

    def draw_pause_menu(self):
        """Draw pause menu"""
        # Create overlay
        overlay_width = int(400 * self.scale_factor)
        overlay_height = int(300 * self.scale_factor)
        overlay = pygame.Surface((overlay_width, overlay_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        
        center_x = self.screen.get_width() // 2
        center_y = self.screen.get_height() // 2
        self.screen.blit(overlay, (center_x - overlay_width // 2, center_y - overlay_height // 2))

        try:
            title_font = pygame.font.SysFont('Comic Sans MS', int(60 * self.scale_factor), bold=True)
            option_font = pygame.font.SysFont('Arial', int(35 * self.scale_factor), bold=True)
        except:
            title_font = pygame.font.SysFont(None, int(60 * self.scale_factor), bold=True)
            option_font = pygame.font.SysFont(None, int(35 * self.scale_factor))

        # Menu text
        title_text = title_font.render("PAUSED", True, (255, 255, 255))
        resume_text = option_font.render("Press ESC to Resume", True, (255, 255, 255))
        restart_text = option_font.render("Press R to Restart", True, (255, 255, 255))
        quit_text = option_font.render("Press Q to Quit", True, (255, 255, 255))
        
        # Draw text
        self.screen.blit(title_text, (center_x - title_text.get_width() // 2, center_y - 100))
        self.screen.blit(resume_text, (center_x - resume_text.get_width() // 2, center_y - 20))
        self.screen.blit(restart_text, (center_x - restart_text.get_width() // 2, center_y + 30))
        self.screen.blit(quit_text, (center_x - quit_text.get_width() // 2, center_y + 80))

    def update_camera(self):
        """Update camera to follow player and clamp to map boundaries"""
        # Map dimensions in pixels
        map_width = self.map_data['width'] * self.map_data['tilewidth']  # 60 * 32 = 1920
        map_height = self.map_data['height'] * self.map_data['tileheight']  # 30 * 32 = 960
        
        # Center camera on player
        target_camera_x = self.player.x - self.screen_width // 2
        target_camera_y = self.player.y - self.screen_height // 2
        
        # Clamp camera to map boundaries (allow movement even if screen = map size)
        max_camera_x = max(0, map_width - self.screen_width)
        max_camera_y = max(0, map_height - self.screen_height)
        
        self.camera_x = max(0, min(target_camera_x, max_camera_x))
        self.camera_y = max(0, min(target_camera_y, max_camera_y))
        
        # Debug: Print camera and player position occasionally
        if hasattr(self, '_camera_debug_counter'):
            self._camera_debug_counter += 1
        else:
            self._camera_debug_counter = 0
            
        if self._camera_debug_counter % 120 == 0:  # Every 120 frames
            print(f"Player: ({self.player.x:.1f}, {self.player.y:.1f})")
            print(f"Camera: ({self.camera_x:.1f}, {self.camera_y:.1f})")
            print(f"Target Camera: ({target_camera_x:.1f}, {target_camera_y:.1f})")
            print(f"Max Camera: ({max_camera_x:.1f}, {max_camera_y:.1f})")
            print(f"Map: {map_width}x{map_height}, Screen: {self.screen_width}x{self.screen_height}")


if __name__ == "__main__":
    game = Game()
    game.run()
