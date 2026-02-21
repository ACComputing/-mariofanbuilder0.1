import pygame
import sys
import os
import json

# Constants
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 720
FPS = 60

# Editor grid settings
TILE_SIZE = 32
GRID_WIDTH = 100
GRID_HEIGHT = 30

# GUI dimensions
MENU_HEIGHT = 30
TOOLBAR_WIDTH = 80
PALETTE_WIDTH = 220
STATUS_HEIGHT = 25

# Calculate view area based on GUI dimensions
VIEW_WIDTH = (WINDOW_WIDTH - TOOLBAR_WIDTH - PALETTE_WIDTH) // TILE_SIZE
VIEW_HEIGHT = (WINDOW_HEIGHT - MENU_HEIGHT - STATUS_HEIGHT) // TILE_SIZE

# Colors
COLOR_BG = (30, 30, 30)
COLOR_PANEL = (50, 50, 50)
COLOR_PANEL_LIGHT = (70, 70, 70)
COLOR_TEXT = (255, 255, 255)
COLOR_HIGHLIGHT = (100, 100, 255)

# Tile types (expanded)
TILE_EMPTY = 0
TILE_GROUND = 1
TILE_BRICK = 2
TILE_QUESTION = 3
TILE_PIPE_TOP_LEFT = 4
TILE_PIPE_TOP_RIGHT = 5
TILE_PIPE_BOTTOM_LEFT = 6
TILE_PIPE_BOTTOM_RIGHT = 7
TILE_COIN = 8
TILE_GOOMBA = 9
TILE_KOOPA = 10
TILE_PIRANHA = 11
TILE_STAR = 12
TILE_MUSHROOM = 13
TILE_FLOWER = 14
TILE_BLOCK_COIN = 15
TILE_BLOCK_VINE = 16
TILE_BLOCK_PSWITCH = 17
TILE_BRIDGE = 18
TILE_CLOUD = 19
TILE_HILL = 20
TILE_FENCE = 21
TILE_WATER = 22
TILE_LAVA = 23

# Colors for tiles (for visualization)
TILE_COLORS = {
    TILE_EMPTY: (50, 50, 50),
    TILE_GROUND: (139, 69, 19),
    TILE_BRICK: (205, 133, 63),
    TILE_QUESTION: (255, 255, 0),
    TILE_PIPE_TOP_LEFT: (0, 255, 0),
    TILE_PIPE_TOP_RIGHT: (0, 200, 0),
    TILE_PIPE_BOTTOM_LEFT: (0, 150, 0),
    TILE_PIPE_BOTTOM_RIGHT: (0, 100, 0),
    TILE_COIN: (255, 215, 0),
    TILE_GOOMBA: (255, 0, 0),
    TILE_KOOPA: (255, 100, 0),
    TILE_PIRANHA: (0, 255, 100),
    TILE_STAR: (255, 255, 100),
    TILE_MUSHROOM: (255, 0, 255),
    TILE_FLOWER: (255, 100, 255),
    TILE_BLOCK_COIN: (200, 200, 0),
    TILE_BLOCK_VINE: (0, 200, 0),
    TILE_BLOCK_PSWITCH: (100, 100, 200),
    TILE_BRIDGE: (150, 75, 0),
    TILE_CLOUD: (240, 240, 240),
    TILE_HILL: (34, 139, 34),
    TILE_FENCE: (160, 82, 45),
    TILE_WATER: (0, 100, 255),
    TILE_LAVA: (255, 69, 0),
}

# Tile categories for palette
TILE_CATEGORIES = {
    "Terrain": [TILE_GROUND, TILE_BRICK, TILE_QUESTION, TILE_BRIDGE, TILE_CLOUD, TILE_HILL, TILE_FENCE],
    "Pipes": [TILE_PIPE_TOP_LEFT, TILE_PIPE_TOP_RIGHT, TILE_PIPE_BOTTOM_LEFT, TILE_PIPE_BOTTOM_RIGHT],
    "Items": [TILE_COIN, TILE_STAR, TILE_MUSHROOM, TILE_FLOWER, TILE_BLOCK_COIN, TILE_BLOCK_VINE, TILE_BLOCK_PSWITCH],
    "Enemies": [TILE_GOOMBA, TILE_KOOPA, TILE_PIRANHA],
    "Liquids": [TILE_WATER, TILE_LAVA],
}

# ----------------------------------------------------------------------
# Level class
# ----------------------------------------------------------------------
class Level:
    def __init__(self, width=GRID_WIDTH, height=GRID_HEIGHT):
        self.width = width
        self.height = height
        self.tiles = [[TILE_EMPTY for _ in range(width)] for _ in range(height)]

    def get_tile(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x]
        return None

    def set_tile(self, x, y, tile_type):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.tiles[y][x] = tile_type

    def save(self, filename):
        data = {'width': self.width, 'height': self.height, 'tiles': self.tiles}
        try:
            with open(filename, 'w') as f:
                json.dump(data, f)
            return True
        except Exception as e:
            print(f"Error saving level: {e}")
            return False

    @staticmethod
    def load(filename):
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            level = Level(data['width'], data['height'])
            level.tiles = data['tiles']
            return level
        except Exception as e:
            print(f"Error loading level: {e}")
            return None

# ----------------------------------------------------------------------
# GUI Components
# ----------------------------------------------------------------------
class Dropdown:
    def __init__(self, x, y, items):
        self.width = 150
        self.item_height = 25
        self.height = len(items) * self.item_height
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.items = items  # List of (text, callback)
        self.hover_index = -1
        self.font = pygame.font.Font(None, 24)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            if self.rect.collidepoint(event.pos):
                self.hover_index = (event.pos[1] - self.rect.y) // self.item_height
            else:
                self.hover_index = -1
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                idx = (event.pos[1] - self.rect.y) // self.item_height
                if 0 <= idx < len(self.items):
                    name, callback = self.items[idx]
                    callback()
                    return "CLOSE"
            else:
                return "CLOSE"
        return None

    def draw(self, screen):
        pygame.draw.rect(screen, COLOR_PANEL, self.rect)
        pygame.draw.rect(screen, (100,100,100), self.rect, 2)
        
        for i, (text, _) in enumerate(self.items):
            item_rect = pygame.Rect(self.rect.x, self.rect.y + i * self.item_height, self.width, self.item_height)
            if i == self.hover_index:
                pygame.draw.rect(screen, COLOR_HIGHLIGHT, item_rect)
            
            text_surf = self.font.render(text, True, COLOR_TEXT)
            screen.blit(text_surf, (item_rect.x + 10, item_rect.y + 4))

class Button:
    def __init__(self, rect, text, callback, color=COLOR_PANEL, text_color=COLOR_TEXT):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.color = color
        self.text_color = text_color
        self.hovered = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered and self.callback:
                self.callback()

    def draw(self, screen, font):
        color = COLOR_HIGHLIGHT if self.hovered else self.color
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, (100,100,100), self.rect, 2)
        text_surf = font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

class MenuBar:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.buttons = []
        self.font = pygame.font.Font(None, 24)

    def add_button(self, text, callback):
        x = self.rect.x + len(self.buttons) * 80
        btn_rect = pygame.Rect(x, self.rect.y, 80, self.rect.height)
        self.buttons.append(Button(btn_rect, text, callback))

    def handle_event(self, event):
        for btn in self.buttons:
            btn.handle_event(event)

    def draw(self, screen):
        pygame.draw.rect(screen, COLOR_PANEL, self.rect)
        pygame.draw.line(screen, (100,100,100), (self.rect.x, self.rect.bottom), (self.rect.right, self.rect.bottom), 2)
        for btn in self.buttons:
            btn.draw(screen, self.font)

class Toolbar:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.buttons = []
        self.font = pygame.font.Font(None, 20)
        self.selected_tool = "pencil"

    def add_tool(self, name, icon_char):
        y = self.rect.y + len(self.buttons) * 50
        btn_rect = pygame.Rect(self.rect.x, y, self.rect.width, 40)
        self.buttons.append((name, icon_char, btn_rect))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for name, _, rect in self.buttons:
                if rect.collidepoint(event.pos):
                    self.selected_tool = name
                    return True
        return False

    def draw(self, screen):
        pygame.draw.rect(screen, COLOR_PANEL, self.rect)
        for name, icon_char, rect in self.buttons:
            color = COLOR_HIGHLIGHT if name == self.selected_tool else COLOR_PANEL_LIGHT
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, (100,100,100), rect, 2)
            text_surf = self.font.render(icon_char, True, COLOR_TEXT)
            text_rect = text_surf.get_rect(center=rect.center)
            screen.blit(text_surf, text_rect)

class Palette:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.categories = list(TILE_CATEGORIES.keys())
        self.current_category = 0
        self.scroll_offset = 0
        self.max_visible = (self.rect.height - 30) // (TILE_SIZE + 5)
        self.selected_tile = TILE_GROUND
        self.tile_rects = []
        self.font = pygame.font.Font(None, 20)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                tab_width = self.rect.width // len(self.categories)
                for i, cat in enumerate(self.categories):
                    tab_rect = pygame.Rect(self.rect.x + i*tab_width, self.rect.y, tab_width, 25)
                    if tab_rect.collidepoint(event.pos):
                        self.current_category = i
                        self.scroll_offset = 0
                        return True
                for tile_type, rect in self.tile_rects:
                    if rect.collidepoint(event.pos):
                        self.selected_tile = tile_type
                        return True
            elif event.button == 4:
                self.scroll_offset = max(0, self.scroll_offset - 1)
            elif event.button == 5:
                max_scroll = max(0, len(self.get_current_tiles()) // 4 - self.max_visible)
                self.scroll_offset = min(max_scroll, self.scroll_offset + 1)
        return False

    def get_current_tiles(self):
        cat = self.categories[self.current_category]
        return TILE_CATEGORIES[cat]

    def draw(self, screen):
        pygame.draw.rect(screen, COLOR_PANEL, self.rect)
        tab_width = self.rect.width // len(self.categories)
        for i, cat in enumerate(self.categories):
            tab_rect = pygame.Rect(self.rect.x + i*tab_width, self.rect.y, tab_width, 25)
            color = COLOR_HIGHLIGHT if i == self.current_category else COLOR_PANEL_LIGHT
            pygame.draw.rect(screen, color, tab_rect)
            pygame.draw.rect(screen, (100,100,100), tab_rect, 2)
            text_surf = self.font.render(cat[:3], True, COLOR_TEXT)
            text_rect = text_surf.get_rect(center=tab_rect.center)
            screen.blit(text_surf, text_rect)

        tiles = self.get_current_tiles()
        cols = 4
        cell_size = TILE_SIZE + 5
        start_x = self.rect.x + 5
        start_y = self.rect.y + 30 - self.scroll_offset * cell_size
        self.tile_rects = []
        for idx, tile_type in enumerate(tiles):
            col = idx % cols
            row = idx // cols
            x = start_x + col * cell_size
            y = start_y + row * cell_size
            rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
            if y + TILE_SIZE > self.rect.y + 30 and y < self.rect.bottom:
                color = TILE_COLORS[tile_type]
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, (100,100,100), rect, 1)
                if tile_type == self.selected_tile:
                    pygame.draw.rect(screen, COLOR_HIGHLIGHT, rect, 3)
                self.tile_rects.append((tile_type, rect))

class StatusBar:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.font = pygame.font.Font(None, 20)
        self.text = "Ready"

    def set_text(self, text):
        self.text = text

    def draw(self, screen):
        pygame.draw.rect(screen, COLOR_PANEL, self.rect)
        pygame.draw.line(screen, (100,100,100), (self.rect.x, self.rect.y), (self.rect.right, self.rect.y), 2)
        text_surf = self.font.render(self.text, True, COLOR_TEXT)
        screen.blit(text_surf, (self.rect.x + 5, self.rect.y + 5))

# ----------------------------------------------------------------------
# Editor class
# ----------------------------------------------------------------------
class Editor:
    def __init__(self, level, screen):
        self.level = level
        self.screen = screen
        self.camera_x = 0
        self.camera_y = 0
        self.dragging = False
        self.last_mouse_grid = None
        self.tool = "pencil"
        self.active_dropdown = None
        self.next_action = None
        
        # Popup state
        self.show_popup = False
        self.popup_text = []

        self.menu_bar = MenuBar((0, 0, WINDOW_WIDTH, MENU_HEIGHT))
        self.setup_menu()

        self.toolbar = Toolbar((0, MENU_HEIGHT, TOOLBAR_WIDTH, WINDOW_HEIGHT - MENU_HEIGHT - STATUS_HEIGHT))
        self.setup_toolbar()

        self.palette = Palette((WINDOW_WIDTH - PALETTE_WIDTH, MENU_HEIGHT, PALETTE_WIDTH, WINDOW_HEIGHT - MENU_HEIGHT - STATUS_HEIGHT))

        self.status_bar = StatusBar((0, WINDOW_HEIGHT - STATUS_HEIGHT, WINDOW_WIDTH, STATUS_HEIGHT))
        self.font = pygame.font.Font(None, 24)

    def setup_menu(self):
        # Menu structure
        self.menu_items = {
            "File": [
                ("New Level", self.cmd_new),
                ("Load Level", self.cmd_load),
                ("Save Level", self.cmd_save),
                ("Quit to Menu", self.cmd_quit)
            ],
            "Edit": [
                ("Clear Level", self.cmd_clear)
            ],
            "View": [
                ("Reset Camera", self.cmd_reset_camera)
            ],
            "Help": [
                ("About", self.cmd_about)
            ]
        }

        # Add buttons to menu bar
        self.menu_bar.add_button("File", lambda: self.show_dropdown("File"))
        self.menu_bar.add_button("Edit", lambda: self.show_dropdown("Edit"))
        self.menu_bar.add_button("View", lambda: self.show_dropdown("View"))
        self.menu_bar.add_button("Help", lambda: self.show_dropdown("Help"))

    def show_dropdown(self, name):
        # Calculate position
        idx = list(self.menu_items.keys()).index(name)
        x = idx * 80
        y = MENU_HEIGHT
        items = self.menu_items[name]
        self.active_dropdown = Dropdown(x, y, items)

    def setup_toolbar(self):
        self.toolbar.add_tool("pencil", "P")
        self.toolbar.add_tool("eraser", "E")
        self.toolbar.add_tool("fill", "F")
        self.toolbar.add_tool("select", "S")

    # --- Menu Commands ---
    def cmd_new(self):
        self.level = Level()
        self.camera_x = 0
        self.camera_y = 0
        self.status_bar.set_text("New level created")

    def cmd_load(self):
        loaded = Level.load("level.json")
        if loaded:
            self.level = loaded
            self.camera_x = 0
            self.camera_y = 0
            self.status_bar.set_text("Level loaded from level.json")
        else:
            self.status_bar.set_text("Error loading level.json")

    def cmd_save(self):
        if self.level.save("level.json"):
            self.status_bar.set_text("Level saved to level.json")
        else:
            self.status_bar.set_text("Error saving level")

    def cmd_quit(self):
        self.next_action = "MENU"

    def cmd_clear(self):
        self.level = Level()
        self.status_bar.set_text("Level cleared")

    def cmd_reset_camera(self):
        self.camera_x = 0
        self.camera_y = 0
        self.status_bar.set_text("Camera reset")

    def cmd_about(self):
        self.show_popup = True
        self.popup_text = [
            "AC Holdings [C] 1999-2026",
            "Catsans's Mario ! Fan Builder 0.1",
            "",
            "[C] 1985-2026 Nintendo",
            "[C] 1999-2026 A.C Holdings"
        ]

    def handle_event(self, event):
        # 0. Handle Popup (Global Overlay)
        if self.show_popup:
            if event.type == pygame.MOUSEBUTTONDOWN or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.show_popup = False
            return

        # 1. Handle Dropdown if open
        if self.active_dropdown:
            result = self.active_dropdown.handle_event(event)
            if result == "CLOSE":
                self.active_dropdown = None
                # Check if we need to switch menus (click on menu bar)
                if event.type == pygame.MOUSEBUTTONDOWN and self.menu_bar.rect.collidepoint(event.pos):
                    self.menu_bar.handle_event(event)
            return

        # 2. Handle Menu Bar
        self.menu_bar.handle_event(event)

        # 3. Handle Toolbar
        if self.toolbar.handle_event(event):
            self.tool = self.toolbar.selected_tool
        
        # 4. Handle Palette
        if self.palette.handle_event(event):
            pass

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "MENU"
            elif event.key == pygame.K_LEFT:
                self.camera_x = max(0, self.camera_x - 1)
            elif event.key == pygame.K_RIGHT:
                self.camera_x = min(self.level.width - VIEW_WIDTH, self.camera_x + 1)
            elif event.key == pygame.K_UP:
                self.camera_y = max(0, self.camera_y - 1)
            elif event.key == pygame.K_DOWN:
                self.camera_y = min(self.level.height - VIEW_HEIGHT, self.camera_y + 1)
            elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                self.cmd_save()
            elif event.key == pygame.K_l and pygame.key.get_mods() & pygame.KMOD_CTRL:
                self.cmd_load()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            edit_area = pygame.Rect(TOOLBAR_WIDTH, MENU_HEIGHT, WINDOW_WIDTH - TOOLBAR_WIDTH - PALETTE_WIDTH, WINDOW_HEIGHT - MENU_HEIGHT - STATUS_HEIGHT)
            if edit_area.collidepoint(event.pos):
                if event.button == 1:
                    self.dragging = True
                    self.place_tile_at_mouse(event.pos)
                elif event.button == 3:
                    self.place_tile_at_mouse(event.pos, TILE_EMPTY)
                elif event.button == 4:
                    self.camera_y = max(0, self.camera_y - 1)
                elif event.button == 5:
                    self.camera_y = min(self.level.height - VIEW_HEIGHT, self.camera_y + 1)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False
                self.last_mouse_grid = None

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                edit_area = pygame.Rect(TOOLBAR_WIDTH, MENU_HEIGHT, WINDOW_WIDTH - TOOLBAR_WIDTH - PALETTE_WIDTH, WINDOW_HEIGHT - MENU_HEIGHT - STATUS_HEIGHT)
                if edit_area.collidepoint(event.pos):
                    self.place_tile_at_mouse(event.pos)

        mouse_pos = pygame.mouse.get_pos()
        edit_area = pygame.Rect(TOOLBAR_WIDTH, MENU_HEIGHT, WINDOW_WIDTH - TOOLBAR_WIDTH - PALETTE_WIDTH, WINDOW_HEIGHT - MENU_HEIGHT - STATUS_HEIGHT)
        if edit_area.collidepoint(mouse_pos):
            grid_x = (mouse_pos[0] - TOOLBAR_WIDTH) // TILE_SIZE + self.camera_x
            grid_y = (mouse_pos[1] - MENU_HEIGHT) // TILE_SIZE + self.camera_y
            tile = self.level.get_tile(grid_x, grid_y)
            self.status_bar.set_text(f"Grid: ({grid_x}, {grid_y})  Tile: {tile}  Tool: {self.tool}")
        else:
            self.status_bar.set_text(f"Tool: {self.tool}  Selected Tile: {self.palette.selected_tile}")

        if self.next_action:
            action = self.next_action
            self.next_action = None
            return action
            
        return None

    def place_tile_at_mouse(self, mouse_pos, tile_type=None):
        if tile_type is None:
            if self.tool == "eraser":
                tile_type = TILE_EMPTY
            else:
                tile_type = self.palette.selected_tile
        grid_x = ((mouse_pos[0] - TOOLBAR_WIDTH) // TILE_SIZE) + self.camera_x
        grid_y = ((mouse_pos[1] - MENU_HEIGHT) // TILE_SIZE) + self.camera_y
        if (grid_x, grid_y) != self.last_mouse_grid:
            self.level.set_tile(grid_x, grid_y, tile_type)
            self.last_mouse_grid = (grid_x, grid_y)

    def update(self):
        pass

    def draw(self, screen):
        edit_rect = pygame.Rect(TOOLBAR_WIDTH, MENU_HEIGHT, WINDOW_WIDTH - TOOLBAR_WIDTH - PALETTE_WIDTH, WINDOW_HEIGHT - MENU_HEIGHT - STATUS_HEIGHT)
        screen.fill(COLOR_BG, edit_rect)

        for y in range(VIEW_HEIGHT):
            for x in range(VIEW_WIDTH):
                world_x = x + self.camera_x
                world_y = y + self.camera_y
                tile = self.level.get_tile(world_x, world_y)
                if tile is not None:
                    color = TILE_COLORS.get(tile, (255,255,255))
                    rect = pygame.Rect(TOOLBAR_WIDTH + x * TILE_SIZE, MENU_HEIGHT + y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    pygame.draw.rect(screen, color, rect)
                    pygame.draw.rect(screen, (100,100,100), rect, 1)

        for y in range(VIEW_HEIGHT+1):
            pygame.draw.line(screen, (80,80,80), (TOOLBAR_WIDTH, MENU_HEIGHT + y*TILE_SIZE), (WINDOW_WIDTH - PALETTE_WIDTH, MENU_HEIGHT + y*TILE_SIZE), 1)
        for x in range(VIEW_WIDTH+1):
            pygame.draw.line(screen, (80,80,80), (TOOLBAR_WIDTH + x*TILE_SIZE, MENU_HEIGHT), (TOOLBAR_WIDTH + x*TILE_SIZE, WINDOW_HEIGHT - STATUS_HEIGHT), 1)

        self.menu_bar.draw(screen)
        self.toolbar.draw(screen)
        self.palette.draw(screen)
        self.status_bar.draw(screen)
        
        if self.active_dropdown:
            self.active_dropdown.draw(screen)

        info = f"Camera: ({self.camera_x}, {self.camera_y})"
        text = self.font.render(info, True, COLOR_TEXT)
        screen.blit(text, (TOOLBAR_WIDTH + 10, MENU_HEIGHT + 10))
        
        # Draw Popup if active
        if self.show_popup:
            self.draw_popup(screen)

    def draw_popup(self, screen):
        # Create overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        # Draw Box
        box_w, box_h = 400, 200
        box_x = (WINDOW_WIDTH - box_w) // 2
        box_y = (WINDOW_HEIGHT - box_h) // 2
        box_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        
        pygame.draw.rect(screen, COLOR_PANEL, box_rect)
        pygame.draw.rect(screen, COLOR_HIGHLIGHT, box_rect, 3)
        
        # Draw Title
        title_font = pygame.font.Font(None, 30)
        title_surf = title_font.render("About", True, COLOR_HIGHLIGHT)
        screen.blit(title_surf, (box_x + 10, box_y + 10))
        
        # Draw Lines
        line_font = pygame.font.Font(None, 24)
        for i, line in enumerate(self.popup_text):
            line_surf = line_font.render(line, True, COLOR_TEXT)
            line_rect = line_surf.get_rect(center=(box_rect.centerx, box_y + 50 + i * 25))
            screen.blit(line_surf, line_rect)
            
        # Draw Close Instruction
        close_surf = line_font.render("Click or Press ESC to close", True, (150, 150, 150))
        close_rect = close_surf.get_rect(center=(box_rect.centerx, box_rect.bottom - 20))
        screen.blit(close_surf, close_rect)

# ----------------------------------------------------------------------
# Main menu
# ----------------------------------------------------------------------
def main_menu(screen):
    font = pygame.font.Font(None, 48)
    small_font = pygame.font.Font(None, 36)
    options = ["New Level", "Load Level", "Quit"]
    selected = 0

    clock = pygame.time.Clock()
    while True:
        screen.fill((0, 0, 128))
        for i, opt in enumerate(options):
            color = (255, 255, 255) if i == selected else (150, 150, 150)
            text = font.render(opt, True, color)
            rect = text.get_rect(center=(WINDOW_WIDTH//2, 200 + i*80))
            screen.blit(text, rect)

        instr = small_font.render("Use UP/DOWN arrows, ENTER to select", True, (200, 200, 200))
        screen.blit(instr, (WINDOW_WIDTH//2 - instr.get_width()//2, 500))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "QUIT"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    if selected == 0:
                        return ("NEW", None)
                    elif selected == 1:
                        return ("LOAD", "level.json")
                    elif selected == 2:
                        return "QUIT"
        clock.tick(30)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("AC Holdings [C] 1999-2026 Catsans's Mario ! Fan Builder 0.1")
    clock = pygame.time.Clock()

    while True:
        result = main_menu(screen)
        if result == "QUIT":
            pygame.quit()
            sys.exit()#
