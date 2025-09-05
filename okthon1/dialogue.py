import pygame

class DialogueBox:
    def __init__(self, screen_width, screen_height, lines, display_time=2.5):
        self.lines = lines  # List of (name, text) tuples
        self.display_time = display_time
        self.index = 0
        self.timer = 0
        self.active = True
        self.screen_width = screen_width
        self.screen_height = screen_height

    def update(self, dt):
        if not self.active:
            return
        self.timer += dt
        if self.timer > self.display_time:
            self.timer = 0
            self.index += 1
            if self.index >= len(self.lines):
                self.active = False

    def next_line(self):
        """Advance to the next line of dialogue"""
        self.timer = 0
        self.index += 1
        if self.index >= len(self.lines):
            self.active = False

    def draw(self, screen):
        if not self.active or self.index >= len(self.lines):
            return
        # Draw a semi-transparent rectangle as dialogue background
        overlay = pygame.Surface((700, 120), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        center_x = self.screen_width // 2
        y = self.screen_height - 180
        screen.blit(overlay, (center_x - 350, y))
        # Use a clear, distinct font
        try:
            name_font = pygame.font.SysFont('Arial', 32, bold=True)
            text_font = pygame.font.SysFont('Comic Sans MS', 32)
        except:
            name_font = pygame.font.SysFont(None, 32, bold=True)
            text_font = pygame.font.SysFont(None, 32)
        name, line = self.lines[self.index]
        name_text = name_font.render(name + ':', True, (255, 255, 0) if name == 'Player' else (255, 80, 80))
        line_text = text_font.render(line, True, (255, 255, 255))
        screen.blit(name_text, (center_x - 320, y + 20))
        screen.blit(line_text, (center_x - 320 + name_text.get_width() + 20, y + 20))

    def is_active(self):
        return self.active 