"""
MARIO FAN BUILDER (SMBX 1.3 Style Engine)
Engine: MARIO FAN BUILDER by CATSAN [C]. AC Holding
Features:
- SMBX 1.3 Authentic GUI Layout (Left Sidebar, Top Menus)
- 60 FPS Performance (Famicon Speed)
- Full Level Editor Functionality
"""

import pygame
import sys
import os
import json
import math
from collections import deque

# -------------------------
# CONSTANTS & CONFIG
# -------------------------
WINDOW_WIDTH, WINDOW_HEIGHT = 1024, 700
SIDEBAR_WIDTH = 200           # SMBX style left sidebar
MENU_HEIGHT = 24              # Top menu bar height
TOOLBAR_HEIGHT = 30           # Icon toolbar height below menu
STATUSBAR_HEIGHT = 24         # Bottom status bar
CANVAS_X = SIDEBAR_WIDTH      # Drawing area starts after sidebar
CANVAS_Y = MENU_HEIGHT + TOOLBAR_HEIGHT
CANVAS_WIDTH = WINDOW_WIDTH - SIDEBAR_WIDTH
CANVAS_HEIGHT = WINDOW_HEIGHT - CANVAS_Y - STATUSBAR_HEIGHT

GRID_SIZE = 32
FPS = 60  # Famicon Speed

# --- SMBX 1.3 "Windows Classic" Style Colors ---
# System Colors (Authentic SMBX Look)
SYS_BG         = (240, 240, 240) # Classic Window Background
SYS_BTN_FACE   = (212, 208, 200) # Button Color
SYS_BTN_LIGHT  = (255, 255, 255) # Highlight
SYS_BTN_DARK   = (128, 128, 128) # Shadow
SYS_BTN_DK_SHD = (64, 64, 64)    # Dark Shadow
SYS_MENU_BG    = (212, 208, 200)
SYS_HIGHLIGHT  = (0, 0, 128)     # Selected item background
SYS_TEXT       = (0, 0, 0)       # Text Color
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Game Colors
RED, GREEN, BLUE, YELLOW = (255,0,0),(0,255,0),(0,0,255),(255,255,0)
GRAY = (128, 128, 128)   # <-- Added missing GRAY definition
SMBX_BG, SMBX_GRID = BLACK, (50,50,50)

# Physics
GRAVITY, JUMP_STRENGTH, MOVE_SPEED, TERMINAL_VELOCITY = 0.5, -10, 4, 10

pygame.init()
pygame.display.set_caption("Mario Fan Builder - CATSAN [C]. AC Holding")

FONT = pygame.font.Font(None, 22)
FONT_SMALL = pygame.font.Font(None, 18)
FONT_TITLE = pygame.font.Font(None, 36)

# -------------------------
# THEMES
# -------------------------
themes = {
    'SMB1': {
        'background': (92, 148, 252), 'ground': (0, 128, 0), 'brick': (180, 80, 40),
        'question': (255, 200, 0), 'coin': (255, 255, 0), 'pipe': (0, 200, 0),
        'platform': (139, 69, 19), 'enemy': (255, 0, 0), 'powerup': (255, 255, 0),
        'water': (0, 0, 255), 'bgo': (200, 200, 200)
    },
    'SMB3': {
        'background': (0, 0, 0), 'ground': (160, 120, 80), 'brick': (180, 100, 60),
        'question': (255, 210, 0), 'coin': (255, 255, 100), 'pipe': (0, 180, 0),
        'platform': (100, 100, 100), 'enemy': (255, 50, 50), 'powerup': (255, 50, 50),
        'water': (30, 80, 200), 'bgo': (150, 150, 150)
    }
}
current_theme = 'SMB1'

# -------------------------
# HELPER FUNCTIONS
# -------------------------
def draw_3d_rect(surf, rect, color, pressed=False):
    """Draws a classic Windows 3D rectangle."""
    r = pygame.Rect(rect)
    c = color
    light = (min(c[0]+40, 255), min(c[1]+40, 255), min(c[2]+40, 255))
    dark = (max(c[0]-40, 0), max(c[1]-40, 0), max(c[2]-40, 0))
    
    pygame.draw.rect(surf, color, r)
    
    if not pressed:
        pygame.draw.line(surf, light, r.topleft, r.topright, 1)
        pygame.draw.line(surf, light, r.topleft, r.bottomleft, 1)
        pygame.draw.line(surf, dark, r.bottomleft, r.bottomright, 1)
        pygame.draw.line(surf, dark, r.topright, r.bottomright, 1)
    else:
        pygame.draw.line(surf, dark, r.topleft, r.topright, 1)
        pygame.draw.line(surf, dark, r.topleft, r.bottomleft, 1)
        pygame.draw.line(surf, light, r.bottomleft, r.bottomright, 1)
        pygame.draw.line(surf, light, r.topright, r.bottomright, 1)

def draw_text(surf, text, pos, color=SYS_TEXT, font=FONT, center=False):
    t = font.render(text, True, color)
    r = t.get_rect(center=pos) if center else t.get_rect(topleft=pos)
    surf.blit(t, r)

# -------------------------
# SPRITE CLASSES
# -------------------------
class Tile(pygame.sprite.Sprite):
    def __init__(self, x, y, tile_type, layer=0):
        super().__init__()
        self.tile_type, self.layer = tile_type, layer
        self.rect = pygame.Rect(x, y, GRID_SIZE, GRID_SIZE)
        self.is_solid = tile_type in ['ground', 'brick', 'question', 'pipe', 'platform']
        self.is_platform = tile_type == 'platform'
        self.update_image()

    def update_image(self):
        self.image = pygame.Surface((GRID_SIZE, GRID_SIZE))
        color = themes[current_theme].get(self.tile_type, (128, 128, 128))
        self.image.fill(color)
        if self.tile_type == 'question':
            draw_text(self.image, '?', (GRID_SIZE//2, GRID_SIZE//2), BLACK, FONT_SMALL, True)
        elif self.tile_type == 'brick':
            pygame.draw.line(self.image, BLACK, (0, GRID_SIZE//2), (GRID_SIZE, GRID_SIZE//2), 2)
            pygame.draw.line(self.image, BLACK, (GRID_SIZE//2, 0), (GRID_SIZE//2, GRID_SIZE), 2)
        elif self.tile_type == 'coin':
            pygame.draw.circle(self.image, YELLOW, (GRID_SIZE//2, GRID_SIZE//2), GRID_SIZE//4)

class NPC(pygame.sprite.Sprite):
    def __init__(self, x, y, npc_type='goomba', layer=0):
        super().__init__()
        self.npc_type, self.layer = npc_type, layer
        self.rect = pygame.Rect(x, y, GRID_SIZE, GRID_SIZE)
        self.velocity = pygame.Vector2(1, 0)
        self.direction = 1
        self.update_image()

    def update_image(self):
        self.image = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
        if self.npc_type == 'goomba':
            pygame.draw.ellipse(self.image, themes[current_theme]['enemy'], (4, 4, GRID_SIZE-8, GRID_SIZE-4))
        elif self.npc_type == 'koopa':
            pygame.draw.rect(self.image, GREEN, (4, 4, GRID_SIZE-8, GRID_SIZE-4))
        elif self.npc_type == 'mushroom':
            pygame.draw.circle(self.image, RED, (GRID_SIZE//2, GRID_SIZE//2), GRID_SIZE//3)

    def update(self, solid_tiles):
        self.velocity.y += GRAVITY
        self.velocity.y = min(self.velocity.y, TERMINAL_VELOCITY)
        self.rect.x += self.velocity.x
        self.handle_collision(solid_tiles, 'x')
        self.rect.y += self.velocity.y
        self.handle_collision(solid_tiles, 'y')

    def handle_collision(self, tiles, axis):
        for t in tiles:
            if self.rect.colliderect(t.rect):
                if axis == 'x':
                    if self.velocity.x > 0: self.rect.right = t.rect.left
                    else: self.rect.left = t.rect.right
                    self.velocity.x *= -1
                elif axis == 'y':
                    if self.velocity.y > 0: self.rect.bottom = t.rect.top
                    elif self.velocity.y < 0: self.rect.top = t.rect.bottom
                    self.velocity.y = 0

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.rect = pygame.Rect(x, y, GRID_SIZE, GRID_SIZE)
        self.image = pygame.Surface((GRID_SIZE, GRID_SIZE)); self.image.fill(RED)
        self.velocity = pygame.Vector2(0, 0); self.on_ground=False
    def update(self, solid_tiles):
        keys=pygame.key.get_pressed(); self.velocity.x=0
        if keys[pygame.K_LEFT]: self.velocity.x=-MOVE_SPEED
        if keys[pygame.K_RIGHT]: self.velocity.x=MOVE_SPEED
        if keys[pygame.K_SPACE] and self.on_ground: self.velocity.y=JUMP_STRENGTH; self.on_ground=False
        self.velocity.y+=GRAVITY; self.velocity.y=min(self.velocity.y,TERMINAL_VELOCITY)
        self.rect.x+=self.velocity.x; self.collide(solid_tiles,'x')
        self.rect.y+=self.velocity.y; self.on_ground=False; self.collide(solid_tiles,'y')
    def collide(self, tiles, axis):
        for t in tiles:
            if self.rect.colliderect(t.rect):
                if axis=='x': self.rect.right=t.rect.left if self.velocity.x>0 else t.rect.right
                elif axis=='y':
                    if self.velocity.y>0: self.rect.bottom=t.rect.top; self.velocity.y=0; self.on_ground=True
                    elif self.velocity.y<0: self.rect.top=t.rect.bottom; self.velocity.y=0

# -------------------------
# CAMERA & LEVEL STRUCTURE
# -------------------------
class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width, self.height = width, height

    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)

    def update(self, target):
        x = -target.rect.centerx + CANVAS_WIDTH // 2
        y = -target.rect.centery + CANVAS_HEIGHT // 2
        x = min(0, x); y = min(0, y)
        x = max(-(self.width - CANVAS_WIDTH), x)
        y = max(-(self.height - CANVAS_HEIGHT), y)
        self.camera = pygame.Rect(x, y, self.width, self.height)

    def move(self, dx, dy):
        self.camera.x += dx; self.camera.y += dy
        self.camera.x = min(0, max(-(self.width - CANVAS_WIDTH), self.camera.x))
        self.camera.y = min(0, max(-(self.height - CANVAS_HEIGHT), self.camera.y))

class Layer:
    def __init__(self, name="Layer 1", visible=True):
        self.name = name; self.visible = visible
        self.tiles, self.npcs = pygame.sprite.Group(), pygame.sprite.Group()
        self.tile_map = {} 

    def all_sprites(self):
        g = pygame.sprite.Group()
        g.add(self.tiles.sprites())
        g.add(self.npcs.sprites())
        return g

class Section:
    def __init__(self, width=100, height=30):
        self.width = width * GRID_SIZE; self.height = height * GRID_SIZE
        self.layers = [Layer("Default")]; self.current_layer_idx = 0
    def current_layer(self): return self.layers[self.current_layer_idx]
    def all_sprites(self):
        group = pygame.sprite.Group()
        for l in self.layers:
            if l.visible: group.add(l.all_sprites().sprites())
        return group

class Level:
    def __init__(self):
        self.sections = [Section()]; self.current_section_idx = 0
        self.start_pos = (100, 500); self.name = "Untitled"
    def current_section(self): return self.sections[self.current_section_idx]
    def current_layer(self): return self.current_section().current_layer()

# -------------------------
# GUI ELEMENTS (SMBX Style)
# -------------------------
class ToolbarButton:
    def __init__(self, rect, text, callback=None, icon=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.hovered = False
        self.pressed = False
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION: 
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos) and self.callback:
                self.pressed = True
                return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.pressed and self.rect.collidepoint(event.pos) and self.callback:
                self.callback()
            self.pressed = False
        return False

    def draw(self, surf):
        draw_3d_rect(surf, self.rect, SYS_BTN_FACE, self.pressed)
        draw_text(surf, self.text, self.rect.center, SYS_TEXT, FONT_SMALL, True)

class Sidebar:
    def __init__(self):
        self.rect = pygame.Rect(0, CANVAS_Y, SIDEBAR_WIDTH, CANVAS_HEIGHT)
        self.categories = ["Blocks", "NPCs", "Layers"]
        self.current_category = "Blocks"
        self.items = {
            "Blocks": ['ground', 'brick', 'question', 'pipe', 'platform', 'coin'],
            "NPCs": ['goomba', 'koopa', 'mushroom'],
            "Layers": []
        }
        self.selected_item = 'ground'
        self.tab_h = 22
    
    def draw(self, surf, level):
        # Background
        pygame.draw.rect(surf, SYS_BG, self.rect)
        pygame.draw.rect(surf, SYS_BTN_DARK, self.rect, 1) # Border

        # Tabs
        tab_w = self.rect.width // len(self.categories)
        for i, cat in enumerate(self.categories):
            r = pygame.Rect(self.rect.x + i*tab_w, self.rect.y, tab_w, self.tab_h)
            is_sel = (cat == self.current_category)
            if is_sel:
                pygame.draw.rect(surf, WHITE, r) # Active tab page bg usually matches
                pygame.draw.rect(surf, SYS_BTN_FACE, r) 
                # Simulate tab connection to page
                pygame.draw.line(surf, WHITE, r.bottomleft, r.bottomright, 1) 
            else:
                draw_3d_rect(surf, r, SYS_BTN_FACE)
            
            draw_text(surf, cat, r.center, SYS_TEXT, FONT_SMALL, True)

        # Content Area
        content_rect = pygame.Rect(self.rect.x, self.rect.y + self.tab_h, self.rect.width, self.rect.height - self.tab_h)
        pygame.draw.rect(surf, WHITE, content_rect) # Page background
        
        if self.current_category == "Layers":
            self.draw_layers(surf, content_rect, level)
        else:
            self.draw_items(surf, content_rect)

    def draw_items(self, surf, area):
        items = self.items[self.current_category]
        x_off, y_off = 5, 5
        size = 34
        for i, item in enumerate(items):
            r = pygame.Rect(area.x + x_off + (i%5)*38, area.y + y_off + (i//5)*38, size, size)
            
            # Selection Highlight
            if item == self.selected_item:
                pygame.draw.rect(surf, SYS_HIGHLIGHT, r)
            
            # Icon
            color = themes[current_theme].get(item, GRAY)  # GRAY is now defined
            if item == 'goomba' or item == 'koopa': color = themes[current_theme]['enemy']
            elif item == 'mushroom': color = themes[current_theme]['powerup']
            
            pygame.draw.rect(surf, color, r.inflate(-4, -4))
            pygame.draw.rect(surf, BLACK, r.inflate(-4, -4), 1)

    def draw_layers(self, surf, area, level):
        y = area.y + 5
        section = level.current_section()
        for i, layer in enumerate(section.layers):
            r = pygame.Rect(area.x + 5, y, area.width - 10, 20)
            color = SYS_HIGHLIGHT if i == section.current_layer_idx else WHITE
            pygame.draw.rect(surf, color, r)
            draw_text(surf, layer.name, (r.x + 5, r.y + 2), WHITE if color == SYS_HIGHLIGHT else SYS_TEXT, FONT_SMALL)
            # Eye icon for visibility
            eye_color = GREEN if layer.visible else RED
            pygame.draw.circle(surf, eye_color, (r.right - 10, r.centery), 4)
            y += 25

    def handle_click(self, pos, level):
        # Tab Click
        tab_w = self.rect.width // len(self.categories)
        for i, cat in enumerate(self.categories):
            r = pygame.Rect(self.rect.x + i*tab_w, self.rect.y, tab_w, self.tab_h)
            if r.collidepoint(pos): self.current_category = cat; return True
        
        # Content Click
        content_rect = pygame.Rect(self.rect.x, self.rect.y + self.tab_h, self.rect.width, self.rect.height - self.tab_h)
        if self.current_category == "Layers":
            y = content_rect.y + 5
            section = level.current_section()
            for i, layer in enumerate(section.layers):
                r = pygame.Rect(content_rect.x + 5, y, content_rect.width - 10, 20)
                if r.collidepoint(pos):
                    # Toggle Visibility
                    if pos[0] > r.right - 20: layer.visible = not layer.visible
                    else: section.current_layer_idx = i
                    return True
                y += 25
        else:
            items = self.items[self.current_category]
            x_off, y_off = 5, 5
            for i, item in enumerate(items):
                r = pygame.Rect(content_rect.x + x_off + (i%5)*38, content_rect.y + y_off + (i//5)*38, 34, 34)
                if r.collidepoint(pos):
                    self.selected_item = item
                    return True
        return False

# -------------------------
# EDITOR CLASS
# -------------------------
class Editor:
    def __init__(self, level):
        self.level = level
        self.camera = Camera(level.current_section().width, level.current_section().height)
        self.playtest_mode = False
        self.player = None
        self.undo_stack = []
        self.redo_stack = []
        self.sidebar = Sidebar()
        self.setup_toolbar()
        self.drag_draw = False
        self.drag_erase = False

    def setup_toolbar(self):
        btns = [
            ("New", self.new_level), ("Open", self.load_level), 
            ("Save", self.save_level), ("|", None),
            ("Undo", self.undo), ("Redo", self.redo), ("|", None),
            ("Test", self.toggle_playtest)
        ]
        self.toolbar_btns = []
        x = 5
        for txt, cb in btns:
            if txt == "|": x += 10; continue
            self.toolbar_btns.append(ToolbarButton((x, 3, 50, 24), txt, cb))
            x += 55

    def new_level(self):
        self.level = Level()
        self.camera = Camera(self.level.current_section().width, self.level.current_section().height)

    def save_level(self):
        data = {"sections": [], "theme": current_theme}
        for sec in self.level.sections:
            sec_data = {"layers": []}
            for lay in sec.layers:
                lay_data = {"name": lay.name, "tiles": [], "npcs": []}
                for t in lay.tiles: lay_data["tiles"].append({"x": t.rect.x, "y": t.rect.y, "type": t.tile_type})
                for n in lay.npcs: lay_data["npcs"].append({"x": n.rect.x, "y": n.rect.y, "type": n.npc_type})
                sec_data["layers"].append(lay_data)
            data["sections"].append(sec_data)
        try:
            with open("mfb_level.json", "w") as f: json.dump(data, f)
            print("Level saved.")
        except Exception as e: print(f"Error saving: {e}")

    def load_level(self):
        try:
            with open("mfb_level.json", "r") as f: data = json.load(f)
            global current_theme
            current_theme = data.get("theme", "SMB1")
            self.level = Level(); self.level.sections = []
            for sec_data in data["sections"]:
                section = Section(); section.layers = []
                for lay_data in sec_data["layers"]:
                    layer = Layer(lay_data["name"])
                    for td in lay_data["tiles"]:
                        t = Tile(td["x"], td["y"], td["type"])
                        layer.tiles.add(t); layer.tile_map[(td["x"], td["y"])] = t
                    if "npcs" in lay_data:
                        for nd in lay_data["npcs"]:
                            n = NPC(nd["x"], nd["y"], nd["type"])
                            layer.npcs.add(n)
                    section.layers.append(layer)
                self.level.sections.append(section)
            self.camera = Camera(self.level.current_section().width, self.level.current_section().height)
        except: print("Load error.")

    def toggle_playtest(self):
        self.playtest_mode = not self.playtest_mode
        if self.playtest_mode:
            self.player = Player(self.level.start_pos[0], self.level.start_pos[1])
            self.camera.update(self.player)

    def push_undo(self, action): self.undo_stack.append(action); self.redo_stack.clear()
    def undo(self):
        if not self.undo_stack: return
        action = self.undo_stack.pop(); action['undo'](); self.redo_stack.append(action)
    def redo(self):
        if not self.redo_stack: return
        action = self.redo_stack.pop(); action['redo'](); self.undo_stack.append(action)

    def place_tile(self, x, y):
        layer = self.level.current_layer()
        key = (x, y)
        if key in layer.tile_map: return
        if self.sidebar.selected_item in ['goomba', 'koopa', 'mushroom']:
            npc = NPC(x, y, self.sidebar.selected_item)
            layer.npcs.add(npc)
            self.push_undo({'undo': lambda l=layer, n=npc: l.npcs.remove(n), 'redo': lambda l=layer, n=npc: l.npcs.add(n)})
        else:
            tile = Tile(x, y, self.sidebar.selected_item)
            layer.tiles.add(tile); layer.tile_map[key] = tile
            self.push_undo({'undo': lambda l=layer, k=key, t=tile: (l.tiles.remove(t), l.tile_map.pop(k)), 
                            'redo': lambda l=layer, k=key, t=tile: (l.tiles.add(t), l.tile_map.update({k:t}))})

    def remove_tile(self, x, y):
        layer = self.level.current_layer()
        key = (x, y)
        if key in layer.tile_map:
            tile = layer.tile_map[key]
            layer.tiles.remove(tile); del layer.tile_map[key]
            self.push_undo({'undo': lambda l=layer, k=key, t=tile: (l.tiles.add(t), l.tile_map.update({k:t})),
                            'redo': lambda l=layer, k=key: (l.tiles.remove(l.tile_map[k]), l.tile_map.pop(k)) if k in l.tile_map else None})
        else:
            for npc in layer.npcs:
                if npc.rect.collidepoint(x, y):
                    layer.npcs.remove(npc)
                    self.push_undo({'undo': lambda l=layer, n=npc: l.npcs.add(n), 'redo': lambda l=layer, n=npc: l.npcs.remove(n)})
                    break

    def handle_event(self, event):
        if event.type == pygame.QUIT: return False
        
        # Toolbar
        for btn in self.toolbar_btns: btn.handle_event(event)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.playtest_mode: self.toggle_playtest()
                else: return "MENU"
            if not self.playtest_mode:
                if event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_CTRL: self.undo()
                if event.key == pygame.K_y and pygame.key.get_mods() & pygame.KMOD_CTRL: self.redo()
                if event.key == pygame.K_LEFT: self.camera.move(GRID_SIZE, 0)
                if event.key == pygame.K_RIGHT: self.camera.move(-GRID_SIZE, 0)
                if event.key == pygame.K_UP: self.camera.move(0, GRID_SIZE)
                if event.key == pygame.K_DOWN: self.camera.move(0, -GRID_SIZE)

        if event.type == pygame.MOUSEBUTTONDOWN:
            # Sidebar
            if self.sidebar.rect.collidepoint(event.pos):
                self.sidebar.handle_click(event.pos, self.level)
            # Canvas
            elif event.pos[1] > CANVAS_Y and event.pos[0] > SIDEBAR_WIDTH:
                if not self.playtest_mode:
                    # Offset calculation for left sidebar
                    world_x = event.pos[0] - SIDEBAR_WIDTH - self.camera.camera.x
                    world_y = event.pos[1] - CANVAS_Y - self.camera.camera.y
                    grid_x, grid_y = (world_x // GRID_SIZE) * GRID_SIZE, (world_y // GRID_SIZE) * GRID_SIZE
                    if event.button == 1: self.drag_draw = True; self.place_tile(grid_x, grid_y)
                    elif event.button == 3: self.drag_erase = True; self.remove_tile(grid_x, grid_y)
        
        if event.type == pygame.MOUSEMOTION:
            if not self.playtest_mode and (self.drag_draw or self.drag_erase):
                world_x = event.pos[0] - SIDEBAR_WIDTH - self.camera.camera.x
                world_y = event.pos[1] - CANVAS_Y - self.camera.camera.y
                grid_x, grid_y = (world_x // GRID_SIZE) * GRID_SIZE, (world_y // GRID_SIZE) * GRID_SIZE
                if self.drag_draw: self.place_tile(grid_x, grid_y)
                elif self.drag_erase: self.remove_tile(grid_x, grid_y)

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1: self.drag_draw = False
            elif event.button == 3: self.drag_erase = False

        return True

    def update(self):
        if self.playtest_mode:
            solid_tiles = []
            for l in self.level.current_section().layers:
                solid_tiles.extend([t for t in l.tiles.sprites() if t.is_solid])
            self.player.update(solid_tiles)
            for l in self.level.current_section().layers:
                for npc in l.npcs: npc.update(solid_tiles)
            self.camera.update(self.player)

    def draw(self, surf):
        surf.fill(SYS_BTN_FACE) # Main background

        # 1. Draw Menu Bar (Placeholder look)
        pygame.draw.rect(surf, SYS_MENU_BG, (0, 0, WINDOW_WIDTH, MENU_HEIGHT))
        pygame.draw.line(surf, WHITE, (0, MENU_HEIGHT-1), (WINDOW_WIDTH, MENU_HEIGHT-1), 1) # Bottom highlight
        draw_text(surf, "File  Edit  Level  View  Help", (10, 6), SYS_TEXT, FONT)

        # 2. Draw Toolbar
        pygame.draw.rect(surf, SYS_BG, (0, MENU_HEIGHT, WINDOW_WIDTH, TOOLBAR_HEIGHT))
        pygame.draw.line(surf, SYS_BTN_DARK, (0, MENU_HEIGHT+TOOLBAR_HEIGHT-1), (WINDOW_WIDTH, MENU_HEIGHT+TOOLBAR_HEIGHT-1), 1)
        for btn in self.toolbar_btns: btn.draw(surf)

        # 3. Draw Sidebar
        self.sidebar.draw(surf, self.level)

        # 4. Draw Canvas
        canvas_rect = pygame.Rect(SIDEBAR_WIDTH, CANVAS_Y, CANVAS_WIDTH, CANVAS_HEIGHT)
        surf.set_clip(canvas_rect)
        surf.fill(themes[current_theme]['background'])
        
        # Grid
        if not self.playtest_mode:
            start_col = int(-self.camera.camera.x // GRID_SIZE)
            end_col = start_col + (CANVAS_WIDTH // GRID_SIZE) + 2
            start_row = int(-self.camera.camera.y // GRID_SIZE)
            end_row = start_row + (CANVAS_HEIGHT // GRID_SIZE) + 2
            for c in range(start_col, end_col):
                x = c * GRID_SIZE + self.camera.camera.x + SIDEBAR_WIDTH
                pygame.draw.line(surf, SMBX_GRID, (x, canvas_rect.y), (x, canvas_rect.bottom))
            for r in range(start_row, end_row):
                y = r * GRID_SIZE + self.camera.camera.y + CANVAS_Y
                pygame.draw.line(surf, SMBX_GRID, (canvas_rect.x, y), (canvas_rect.right, y))

        # Sprites
        for sprite in self.level.current_section().all_sprites():
            # Offset sprite drawing by sidebar/canvas position
            pos = self.camera.apply(sprite).move(SIDEBAR_WIDTH, CANVAS_Y)
            surf.blit(sprite.image, pos)
        
        if self.playtest_mode and self.player:
             pos = self.camera.apply(self.player).move(SIDEBAR_WIDTH, CANVAS_Y)
             surf.blit(self.player.image, pos)

        surf.set_clip(None)

        # 5. Draw Status Bar
        pygame.draw.rect(surf, SYS_MENU_BG, (0, WINDOW_HEIGHT - STATUSBAR_HEIGHT, WINDOW_WIDTH, STATUSBAR_HEIGHT))
        pygame.draw.line(surf, WHITE, (0, WINDOW_HEIGHT - STATUSBAR_HEIGHT), (WINDOW_WIDTH, WINDOW_HEIGHT - STATUSBAR_HEIGHT), 1)
        
        mode = "PLAYTEST" if self.playtest_mode else "EDITOR"
        status = f"Mode: {mode} | Layer: {self.level.current_layer().name} | Section: {self.level.current_section_idx}"
        draw_text(surf, status, (10, WINDOW_HEIGHT - STATUSBAR_HEIGHT + 6), SYS_TEXT, FONT_SMALL)
        
        return surf

# -------------------------
# MAIN MENU
# -------------------------
def main_menu(screen):
    buttons = [
        ToolbarButton((WINDOW_WIDTH//2 - 100, 350, 200, 40), "New Level", lambda: "NEW"),
        ToolbarButton((WINDOW_WIDTH//2 - 100, 420, 200, 40), "Quit", lambda: "QUIT")
    ]
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "QUIT"
            for btn in buttons:
                res = btn.handle_event(event)
                if res: return btn.callback()
        
        screen.fill(SYS_BTN_FACE)
        
        # Classic Banner
        pygame.draw.rect(screen, SYS_HIGHLIGHT, (0, 0, WINDOW_WIDTH, 120))
        draw_text(screen, "MARIO FAN BUILDER", (WINDOW_WIDTH//2, 40), WHITE, FONT_TITLE, True)
        draw_text(screen, "by CATSAN [C]. AC Holding", (WINDOW_WIDTH//2, 80), WHITE, FONT, True)

        # Border
        draw_3d_rect(screen, (50, 150, WINDOW_WIDTH-100, 200), SYS_BTN_FACE)
        draw_text(screen, "Engine Ver 1.0 - SMBX Style", (WINDOW_WIDTH//2, 200), SYS_TEXT, FONT, True)
        draw_text(screen, "60 FPS Famicon Speed", (WINDOW_WIDTH//2, 230), SYS_TEXT, FONT_SMALL, True)

        for btn in buttons: btn.draw(screen)
        
        pygame.display.flip()
        clock.tick(FPS)

# -------------------------
# MAIN EXECUTION
# -------------------------
def main():
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()
    
    while True:
        result = main_menu(screen)
        if result == "QUIT":
            pygame.quit()
            sys.exit()
        
        if result == "NEW":
            level = Level()
            editor = Editor(level)
            running = True
            while running:
                for event in pygame.event.get():
                    res = editor.handle_event(event)
                    if res == "MENU": running = False
                    elif res == False: running = False; pygame.quit(); sys.exit()
                
                editor.update()
                editor.draw(screen)
                pygame.display.flip()
                clock.tick(FPS)

if __name__ == "__main__":
    main()
