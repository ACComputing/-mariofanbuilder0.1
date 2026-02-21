import pygame
import json
import sys
import os
import random
import math
from collections import deque

pygame.init()

# --- Constants ---
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 700
SIDEBAR_WIDTH = 200
TOOLBAR_HEIGHT = 40
STATUSBAR_HEIGHT = 24
EDITOR_WIDTH = WINDOW_WIDTH - SIDEBAR_WIDTH
EDITOR_HEIGHT = WINDOW_HEIGHT - TOOLBAR_HEIGHT - STATUSBAR_HEIGHT
GRID_SIZE = 32
FPS = 60

# --- SMBX-inspired Colors ---
SMBX_BG_COLOR = (0, 0, 0)            # Black background for editor
SMBX_SIDEBAR_BG = (240, 240, 240)    # Light gray sidebar
SMBX_TOOLBAR_BG = (230, 230, 230)    # Light gray toolbar
SMBX_STATUSBAR_BG = (0, 0, 128)      # Dark Blue status bar
SMBX_GRID_COLOR = (50, 50, 50)       # Dark grid lines
SMBX_SELECTION_COLOR = (255, 255, 0) # Yellow selection box
SMBX_BUTTON_HOVER = (200, 200, 255)
SMBX_BUTTON_BORDER = (100, 100, 100)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# --- Themes (Mario Fan Builder style) ---
themes = {
    'SMB1': {
        'ground': (200, 100, 50), 'brick': (200, 80, 40), 'question': (255, 200, 0),
        'coin': (255, 255, 0), 'enemy': (255, 0, 0), 'water': (50, 50, 255),
        'background': (107, 136, 255), 'pipe': (0, 200, 0), 'powerup': (255, 0, 0),
    },
    'SMB3': {
        'ground': (160, 120, 80), 'brick': (180, 100, 60), 'question': (255, 210, 0),
        'coin': (255, 255, 100), 'enemy': (255, 50, 50), 'water': (30, 80, 200),
        'background': (0, 0, 0), 'pipe': (0, 180, 0), 'powerup': (255, 50, 50),
    }
}
current_theme = 'SMB1'

# --- Initialize Window ---
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Mario Fan Builder [SMBX Style] - Level Editor")
game_clock = pygame.time.Clock()
FONT = pygame.font.Font(None, 24)
FONT_SMALL = pygame.font.Font(None, 20)

# --- Physics Constants ---
GRAVITY = 0.5
TERMINAL_VELOCITY = 10
JUMP_STRENGTH = -10
MOVE_SPEED = 4

# --- Helper Classes ---
class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)

    def apply_rect(self, rect):
        return rect.move(self.camera.topleft)

    def update(self, target):
        x = -target.rect.centerx + int(EDITOR_WIDTH / 2)
        y = -target.rect.centery + int(EDITOR_HEIGHT / 2)
        # Limit scrolling to level bounds
        x = min(0, x) 
        y = min(0, y)
        y = max(-(self.height - EDITOR_HEIGHT), y)
        x = max(-(self.width - EDITOR_WIDTH), x)
        self.camera = pygame.Rect(x, y, self.width, self.height)

class Tile(pygame.sprite.Sprite):
    def __init__(self, pos, tile_type):
        super().__init__()
        self.tile_type = tile_type
        self.image = pygame.Surface((GRID_SIZE, GRID_SIZE))
        self.rect = self.image.get_rect(topleft=pos)
        self.is_solid = tile_type in ['ground', 'brick', 'question', 'pipe']
        self.is_platform = tile_type == 'platform'
        self.contains_item = 'coin' if tile_type == 'question' else None
        self.update_image()

    def update_image(self):
        theme_colors = themes[current_theme]
        color = theme_colors.get(self.tile_type, WHITE)
        self.image.fill(color)
        
        # Simple decorations
        if self.tile_type == 'question':
            pygame.draw.rect(self.image, BLACK, (2, 2, GRID_SIZE-4, GRID_SIZE-4), 2)
            q_text = FONT_SMALL.render("?", True, BLACK)
            self.image.blit(q_text, (GRID_SIZE//2 - 4, GRID_SIZE//2 - 8))
        elif self.tile_type == 'brick':
            pygame.draw.line(self.image, BLACK, (0, GRID_SIZE//2), (GRID_SIZE, GRID_SIZE//2), 1)
            pygame.draw.line(self.image, BLACK, (GRID_SIZE//2, 0), (GRID_SIZE//2, GRID_SIZE//2), 1)
        elif self.tile_type == 'coin':
            pygame.draw.circle(self.image, theme_colors['coin'], (GRID_SIZE//2, GRID_SIZE//2), GRID_SIZE//4)

class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos, enemy_type='goomba'):
        super().__init__()
        self.enemy_type = enemy_type
        self.image = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=pos)
        self.velocity = pygame.Vector2(1, 0)
        self.update_image()

    def update_image(self):
        color = themes[current_theme]['enemy']
        self.image.fill((0,0,0,0))
        # Draw a simple goomba shape
        pygame.draw.ellipse(self.image, color, (4, 4, GRID_SIZE-8, GRID_SIZE-4))
        pygame.draw.circle(self.image, WHITE, (12, 12), 3)
        pygame.draw.circle(self.image, WHITE, (GRID_SIZE-12, 12), 3)

    def update(self, solid_tiles, platforms=None):
        self.velocity.y += GRAVITY
        self.rect.x += self.velocity.x
        self.handle_collision(solid_tiles, 'x')
        self.rect.y += self.velocity.y
        self.handle_collision(solid_tiles, 'y')

    def handle_collision(self, tiles, axis):
        for tile in tiles:
            if self.rect.colliderect(tile.rect):
                if axis == 'x':
                    if self.velocity.x > 0: self.rect.right = tile.rect.left
                    elif self.velocity.x < 0: self.rect.left = tile.rect.right
                    self.velocity.x *= -1
                elif axis == 'y':
                    if self.velocity.y > 0: self.rect.bottom = tile.rect.top
                    elif self.velocity.y < 0: self.rect.top = tile.rect.bottom
                    self.velocity.y = 0

class Player(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface((GRID_SIZE, GRID_SIZE))
        self.image.fill(themes[current_theme].get('powerup', RED)) # Use powerup color for player
        self.rect = self.image.get_rect(topleft=pos)
        self.velocity = pygame.Vector2(0, 0)
        self.on_ground = False

    def update(self, solid_tiles):
        keys = pygame.key.get_pressed()
        
        # Movement
        self.velocity.x = 0
        if keys[pygame.K_LEFT]: self.velocity.x = -MOVE_SPEED
        if keys[pygame.K_RIGHT]: self.velocity.x = MOVE_SPEED
        
        # Jump
        if keys[pygame.K_SPACE] and self.on_ground:
            self.velocity.y = JUMP_STRENGTH
            self.on_ground = False

        # Gravity
        self.velocity.y += GRAVITY
        
        # Move X
        self.rect.x += self.velocity.x
        self.check_collision(solid_tiles, 'x')
        
        # Move Y
        self.rect.y += self.velocity.y
        self.on_ground = False
        self.check_collision(solid_tiles, 'y')

    def check_collision(self, tiles, axis):
        for tile in tiles:
            if self.rect.colliderect(tile.rect):
                if axis == 'x':
                    if self.velocity.x > 0: self.rect.right = tile.rect.left
                    elif self.velocity.x < 0: self.rect.left = tile.rect.right
                elif axis == 'y':
                    if self.velocity.y > 0:
                        self.rect.bottom = tile.rect.top
                        self.velocity.y = 0
                        self.on_ground = True
                    elif self.velocity.y < 0:
                        self.rect.top = tile.rect.bottom
                        self.velocity.y = 0

# --- GUI Classes ---
class Button:
    def __init__(self, rect, text, action=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.action = action
        self.hovered = False

    def draw(self, surface):
        color = SMBX_BUTTON_HOVER if self.hovered else SMBX_TOOLBAR_BG
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, SMBX_BUTTON_BORDER, self.rect, 1)
        text_surf = FONT_SMALL.render(self.text, True, BLACK)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def check_hover(self, pos):
        self.hovered = self.rect.collidepoint(pos)

    def check_click(self, pos):
        if self.rect.collidepoint(pos):
            if self.action: self.action()
            return True
        return False

class Sidebar:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.categories = ["Blocks", "NPCs", "Misc"]
        self.items = {
            "Blocks": ['ground', 'brick', 'question', 'pipe', 'platform'],
            "NPCs": ['enemy'],
            "Misc": ['coin', 'water']
        }
        self.current_category = "Blocks"
        self.scroll_y = 0
        self.selected_item = 'ground'
        self.tile_rects = [] # Store rects for clicking

    def draw(self, surface):
        # Background
        pygame.draw.rect(surface, SMBX_SIDEBAR_BG, self.rect)
        
        # Category Tabs
        tab_w = self.rect.width // len(self.categories)
        for i, cat in enumerate(self.categories):
            tab_rect = pygame.Rect(self.rect.x + i*tab_w, self.rect.y, tab_w, 25)
            color = WHITE if cat == self.current_category else SMBX_TOOLBAR_BG
            pygame.draw.rect(surface, color, tab_rect)
            pygame.draw.rect(surface, BLACK, tab_rect, 1)
            txt = FONT_SMALL.render(cat, True, BLACK)
            surface.blit(txt, (tab_rect.centerx - txt.get_width()//2, tab_rect.y + 5))
        
        # Item Grid
        self.tile_rects = []
        items = self.items.get(self.current_category, [])
        grid_x = self.rect.x + 5
        grid_y = self.rect.y + 35
        cols = 5
        
        for i, item in enumerate(items):
            col = i % cols
            row = i // cols
            x = grid_x + col * 38
            y = grid_y + row * 38
            
            icon_rect = pygame.Rect(x, y, 32, 32)
            self.tile_rects.append((icon_rect, item))
            
            # Draw Icon
            if item in themes[current_theme]:
                color = themes[current_theme][item]
                pygame.draw.rect(surface, color, icon_rect)
            else:
                pygame.draw.rect(surface, (150, 150, 150), icon_rect)
            
            pygame.draw.rect(surface, BLACK, icon_rect, 1)
            
            # Selection Highlight
            if item == self.selected_item:
                pygame.draw.rect(surface, SMBX_SELECTION_COLOR, icon_rect, 2)

        # Title
        title_surf = FONT.render("Item Box", True, BLACK)
        surface.blit(title_surf, (self.rect.x + 10, self.rect.bottom - 20))

    def handle_click(self, pos):
        # Check Category Tabs
        tab_w = self.rect.width // len(self.categories)
        for i, cat in enumerate(self.categories):
            tab_rect = pygame.Rect(self.rect.x + i*tab_w, self.rect.y, tab_w, 25)
            if tab_rect.collidepoint(pos):
                self.current_category = cat
                return

        # Check Item Click
        for rect, item in self.tile_rects:
            if rect.collidepoint(pos):
                self.selected_item = item
                return

# --- Global State ---
tiles_group = pygame.sprite.Group()
enemies_group = pygame.sprite.Group()
all_sprites = pygame.sprite.Group()
player = Player((100, 500))
camera = Camera(3000, 1000) # Large level size

playtest_mode = False
selected_tool = 'pencil' # pencil, eraser, fill

# Buttons actions
def action_save():
    print("Save triggered (Placeholder)")

def action_load():
    print("Load triggered (Placeholder)")

def action_play():
    global playtest_mode
    playtest_mode = not playtest_mode
    if playtest_mode:
        # Reset player position to a valid start or current view
        player.rect.topleft = camera.apply_rect(pygame.Rect(100, 500, 32, 32)).topleft
        # Convert screen pos back to world pos is tricky, simplified here
        player.rect.x = 100
        player.rect.y = 500
        player.velocity = pygame.Vector2(0,0)
        print("Entered Playtest Mode")
    else:
        print("Exited Playtest Mode")

def set_tool_pencil(): global selected_tool; selected_tool = 'pencil'
def set_tool_eraser(): global selected_tool; selected_tool = 'eraser'

# Setup Buttons
toolbar_buttons = [
    Button((5, 5, 60, 30), "New", None),
    Button((70, 5, 60, 30), "Save", action_save),
    Button((135, 5, 60, 30), "Load", action_load),
    Button((250, 5, 60, 30), "Pencil", set_tool_pencil),
    Button((315, 5, 60, 30), "Eraser", set_tool_eraser),
    Button((EDITOR_WIDTH - 100, 5, 90, 30), "Play/Test", action_play),
]

sidebar = Sidebar(EDITOR_WIDTH, TOOLBAR_HEIGHT, SIDEBAR_WIDTH, EDITOR_HEIGHT)

# --- Main Loop ---
running = True
mouse_held = False # For drawing drag
right_mouse_held = False # For eraser drag

while running:
    mouse_pos = pygame.mouse.get_pos()
    
    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            # --- Left Click (Place / UI) ---
            if event.button == 1: 
                mouse_held = True
                # Check GUI interactions first
                clicked_ui = False
                
                # Toolbar Buttons
                for btn in toolbar_buttons:
                    if btn.check_click(mouse_pos):
                        clicked_ui = True
                        break
                
                # Sidebar
                if sidebar.rect.collidepoint(mouse_pos):
                    sidebar.handle_click(mouse_pos)
                    clicked_ui = True
                
                # Editor Area Interaction
                if not clicked_ui and not playtest_mode:
                    # Convert screen mouse pos to world pos
                    # World X = Mouse X - Camera X Offset
                    world_x = mouse_pos[0] - camera.camera.x
                    world_y = mouse_pos[1] - camera.camera.y
                    
                    # Snap to grid
                    grid_x = (world_x // GRID_SIZE) * GRID_SIZE
                    grid_y = (world_y // GRID_SIZE) * GRID_SIZE
                    
                    if selected_tool == 'pencil':
                        # Check if tile exists, if not create
                        exists = False
                        for t in tiles_group:
                            if t.rect.topleft == (grid_x, grid_y):
                                exists = True
                                break
                        if not exists:
                            new_tile = Tile((grid_x, grid_y), sidebar.selected_item)
                            tiles_group.add(new_tile)
                            all_sprites.add(new_tile)
                            
                    elif selected_tool == 'eraser':
                        for t in tiles_group:
                            if t.rect.collidepoint(world_x, world_y):
                                t.kill()

            # --- Right Click (Erase) ---
            elif event.button == 3:
                right_mouse_held = True
                if not playtest_mode:
                    # Check if not over UI
                    if not sidebar.rect.collidepoint(mouse_pos) and mouse_pos[1] > TOOLBAR_HEIGHT:
                        world_x = mouse_pos[0] - camera.camera.x
                        world_y = mouse_pos[1] - camera.camera.y
                        
                        for t in tiles_group:
                            if t.rect.collidepoint(world_x, world_y):
                                t.kill()

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                mouse_held = False
            elif event.button == 3:
                right_mouse_held = False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if playtest_mode: action_play() # Exit playtest
            # Camera scrolling in Editor mode
            if not playtest_mode:
                if event.key == pygame.K_LEFT:
                    camera.camera.x += GRID_SIZE
                if event.key == pygame.K_RIGHT:
                    camera.camera.x -= GRID_SIZE
                if event.key == pygame.K_UP:
                    camera.camera.y += GRID_SIZE
                if event.key == pygame.K_DOWN:
                    camera.camera.y -= GRID_SIZE

    # --- Continuous Drawing (Drag) ---
    if not playtest_mode and not sidebar.rect.collidepoint(mouse_pos):
        world_x = mouse_pos[0] - camera.camera.x
        world_y = mouse_pos[1] - camera.camera.y
        grid_x = (world_x // GRID_SIZE) * GRID_SIZE
        grid_y = (world_y // GRID_SIZE) * GRID_SIZE

        # Left Drag (Pencil)
        if mouse_held:
            if selected_tool == 'pencil':
                exists = any(t.rect.topleft == (grid_x, grid_y) for t in tiles_group)
                if not exists:
                    new_tile = Tile((grid_x, grid_y), sidebar.selected_item)
                    tiles_group.add(new_tile)
                    all_sprites.add(new_tile)
            elif selected_tool == 'eraser':
                for t in tiles_group:
                    if t.rect.collidepoint(world_x, world_y):
                        t.kill()
        
        # Right Drag (Eraser Shortcut)
        elif right_mouse_held:
             for t in tiles_group:
                if t.rect.collidepoint(world_x, world_y):
                    t.kill()

    # --- Updates ---
    if playtest_mode:
        solid_tiles = [t for t in tiles_group if t.is_solid]
        player.update(solid_tiles)
        enemies_group.update(solid_tiles)
        camera.update(player)
    else:
        # Hover effects for buttons
        for btn in toolbar_buttons:
            btn.check_hover(mouse_pos)

    # --- Drawing ---
    window.fill(SMBX_BG_COLOR)

    # 1. Draw Editor Area (World)
    # Create a subsurface or clip rect for the editor area to prevent drawing over GUI
    editor_rect = pygame.Rect(0, TOOLBAR_HEIGHT, EDITOR_WIDTH, EDITOR_HEIGHT)
    window.set_clip(editor_rect)
    
    # Background Color
    window.fill(themes[current_theme]['background'])

    # Grid (Optimized: only draw visible)
    start_col = int(-camera.camera.x // GRID_SIZE)
    end_col = start_col + (EDITOR_WIDTH // GRID_SIZE) + 2
    start_row = int(-camera.camera.y // GRID_SIZE)
    end_row = start_row + (EDITOR_HEIGHT // GRID_SIZE) + 2

    for c in range(start_col, end_col):
        x = c * GRID_SIZE + camera.camera.x
        pygame.draw.line(window, SMBX_GRID_COLOR, (x, 0), (x, WINDOW_HEIGHT))
    for r in range(start_row, end_row):
        y = r * GRID_SIZE + camera.camera.y
        pygame.draw.line(window, SMBX_GRID_COLOR, (0, y), (WINDOW_WIDTH, y))

    # Sprites
    for sprite in all_sprites:
        window.blit(sprite.image, camera.apply(sprite))
    
    # Player
    if playtest_mode:
        window.blit(player.image, camera.apply(player))

    # Reset Clip for GUI
    window.set_clip(None)

    # 2. Draw Toolbar
    pygame.draw.rect(window, SMBX_TOOLBAR_BG, (0, 0, EDITOR_WIDTH, TOOLBAR_HEIGHT))
    pygame.draw.line(window, BLACK, (0, TOOLBAR_HEIGHT-1), (EDITOR_WIDTH, TOOLBAR_HEIGHT-1))
    for btn in toolbar_buttons:
        btn.draw(window)

    # 3. Draw Sidebar
    sidebar.draw(window)

    # 4. Draw Status Bar
    status_rect = pygame.Rect(0, WINDOW_HEIGHT - STATUSBAR_HEIGHT, WINDOW_WIDTH, STATUSBAR_HEIGHT)
    pygame.draw.rect(window, SMBX_STATUSBAR_BG, status_rect)
    
    # Status Text
    mode_text = "PLAYTEST" if playtest_mode else "EDITOR"
    pos_text = f"Mouse: {mouse_pos[0]},{mouse_pos[1]}"
    tool_text = f"Tool: {selected_tool.capitalize()}"
    
    status_render = FONT_SMALL.render(f"{mode_text} | {tool_text} | {pos_text}", True, WHITE)
    window.blit(status_render, (10, WINDOW_HEIGHT - STATUSBAR_HEIGHT + 5))

    pygame.display.update()
    game_clock.tick(FPS)

pygame.quit()
sys.exit()
