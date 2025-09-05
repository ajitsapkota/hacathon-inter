import pygame
import os
import math

class Item:
    def __init__(self, name, image_path, item_type, description=""):
        self.name = name
        self.item_type = item_type
        self.description = description
        self.quantity = 0
        
        # Load and scale image
        if os.path.exists(image_path):
            self.image = pygame.image.load(image_path).convert_alpha()
            self.image = pygame.transform.scale(self.image, (32, 32))
        else:
            # Create fallback image
            self.image = pygame.Surface((32, 32))
            self.image.fill((128, 128, 128))  # Gray color
        
        self.rect = pygame.Rect(0, 0, 32, 32)
    
    def use(self, player):
        """Use the item on the player"""
        if self.quantity > 0:
            self.quantity -= 1
            return True
        return False

class Soap(Item):
    def __init__(self):
        super().__init__("Soap", "game images/soap.jpeg", "cleaning", "Cleans dirt and germs")
    
    def use(self, player):
        """Use soap to clean the player"""
        if self.quantity > 0:
            self.quantity -= 1
            player.is_clean = True
            player.clean_timer = 30.0  # 30 seconds of cleanliness
            print("Used soap! You are now clean!")
            return True
        return False

class Water(Item):
    def __init__(self):
        super().__init__("Water", "game images/water.jpeg", "cleaning", "Washes away dirt")
    
    def use(self, player):
        """Use water to clean the player"""
        if self.quantity > 0:
            self.quantity -= 1
            player.is_clean = True
            player.clean_timer = 20.0  # 20 seconds of cleanliness
            print("Used water! You are now clean!")
            return True
        return False

class FirstAid(Item):
    def __init__(self):
        super().__init__("First Aid", "game images/first aid.jpeg", "healing", "Restores health")
    
    def use(self, player):
        """Use first aid to restore health"""
        if self.quantity > 0:
            self.quantity -= 1
            player.max_health = min(100, player.max_health + 30)
            print("Used first aid! Health restored!")
            return True
        return False

class TrashItem(Item):
    def __init__(self):
        super().__init__("Trash", "game images/trash.jpeg", "trash", "Dirty trash item")
    
    def use(self, player):
        """Trash cannot be used, only collected"""
        return False

class Inventory:
    def __init__(self):
        self.items = {
            "soap": Soap(),
            "water": Water(),
            "first_aid": FirstAid(),
            "trash": TrashItem()
        }
        self.is_open = False
        self.selected_item = None
        self.menu_x = 50
        self.menu_y = 50
        self.item_spacing = 80
        
    def add_item(self, item_name, quantity=1):
        """Add item to inventory"""
        if item_name in self.items:
            self.items[item_name].quantity += quantity
            print(f"Added {quantity} {item_name} to inventory")
    
    def use_item(self, item_name, player):
        """Use an item from inventory"""
        if item_name in self.items:
            return self.items[item_name].use(player)
        return False
    
    def draw(self, screen, camera_x, camera_y):
        """Draw inventory menu"""
        if not self.is_open:
            return
        
        # Get screen dimensions
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        
        # Calculate center position for inventory
        menu_width = 400
        menu_height = 300
        self.menu_x = (screen_width - menu_width) // 2
        self.menu_y = (screen_height - menu_height) // 2
        
        # Draw background
        menu_surface = pygame.Surface((menu_width, menu_height))
        menu_surface.fill((50, 50, 50))
        menu_surface.set_alpha(200)
        screen.blit(menu_surface, (self.menu_x, self.menu_y))
        
        # Draw border
        pygame.draw.rect(screen, (255, 255, 255), 
                        (self.menu_x, self.menu_y, menu_width, menu_height), 3)
        
        # Draw title
        font = pygame.font.Font(None, 36)
        title = font.render("INVENTORY", True, (255, 255, 255))
        title_x = self.menu_x + (menu_width - title.get_width()) // 2
        screen.blit(title, (title_x, self.menu_y + 20))
        
        # Draw items
        font = pygame.font.Font(None, 24)
        y_offset = 80
        
        for i, (item_name, item) in enumerate(self.items.items()):
            x = self.menu_x + 30 + (i % 2) * 180
            y = self.menu_y + y_offset + (i // 2) * 80
            
            # Draw item image
            screen.blit(item.image, (x, y))
            
            # Draw item name and quantity
            name_text = font.render(f"{item.name}: {item.quantity}", True, (255, 255, 255))
            screen.blit(name_text, (x + 40, y))
            
            # Draw description
            desc_font = pygame.font.Font(None, 18)
            desc_text = desc_font.render(item.description, True, (200, 200, 200))
            screen.blit(desc_text, (x + 40, y + 20))
            
            # Highlight selected item
            if self.selected_item == item_name:
                pygame.draw.rect(screen, (255, 255, 0), (x-5, y-5, 170, 60), 3)
        
        # Draw instructions
        instruction_font = pygame.font.Font(None, 20)
        instructions = [
            "Press 1-4 to use items",
            "Press I to close inventory"
        ]
        for i, instruction in enumerate(instructions):
            text = instruction_font.render(instruction, True, (255, 255, 255))
            text_x = self.menu_x + (menu_width - text.get_width()) // 2
            screen.blit(text, (text_x, self.menu_y + 250 + i * 20))
    
    def handle_input(self, keys, player):
        """Handle inventory input"""
        if not self.is_open:
            return
        
        # Use items with number keys
        if keys[pygame.K_1]:
            self.use_item("soap", player)
        elif keys[pygame.K_2]:
            self.use_item("water", player)
        elif keys[pygame.K_3]:
            self.use_item("first_aid", player)
        elif keys[pygame.K_4]:
            self.use_item("trash", player)
    
    def toggle(self):
        """Toggle inventory visibility"""
        self.is_open = not self.is_open
        if self.is_open:
            print("Inventory opened")
        else:
            print("Inventory closed") 