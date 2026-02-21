"""
MARIO FAN BUILDER (SMBX 1.3 Style Engine)
Engine: MARIO FAN BUILDER by CATSAN [C]. AC Holding
Features:
- 60 FPS Performance
- NPC & Tile Management
- Layer System
- Undo/Redo & Playtest
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
EDITOR_WIDTH, SIDEBAR_WIDTH = 800, 224
TOOLBAR_HEIGHT, STATUSBAR_HEIGHT = 40, 24
GRID_SIZE = 32
FPS = 60  # Locked to 60 FPS as requested

# Colors (Famicon/NES Inspired Palette)
BLACK, WHITE, RED, GREEN, BLUE, YELLOW = (0,0,0),(255,255,255),(255,0,0),(0,255,0),(0,0,255),(255,255,0)
LIGHT_GRAY, DARK_GRAY, GRAY = (200,200,200),(64,64,64),(128,128,128)
SMBX_BG, SMBX_SIDEBAR, SMBX_TOOLBAR, SMBX_STATUSBAR, SMBX_GRID = BLACK, LIGHT_GRAY, LIGHT_GRAY, (0,0,128), (50,50,50)
SMBX_SELECTION, SMBX_BUTTON_HOVER, SMBX_BUTTON_BORDER = YELLOW, (200,200,255), (100,100,100)

# Physics
GRAVITY, JUMP_STRENGTH, MOVE_SPEED, TERMINAL_VELOCITY = 0.5, -10, 4, 10

pygame.init()
pygame.display.set_caption("MARIO FAN BUILDER by CATSAN [C]. AC Holding")

FONT = pygame.font.Font(None, 24)
FONT_SMALL = pygame.font.Font(None, 20)
FONT_TITLE = pygame.font.Font(None, 48)

# Game States
STATE_MAIN_MENU, STATE_EDITOR, STATE_OPTIONS = 0, 1, 2

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
def draw_text(surf, text, pos, color=WHITE, font=FONT, center=False):
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

    def copy(self):
        return Tile(self.rect.x, self.rect.y, self.tile_type, self.layer)

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

    def copy(self): 
        return NPC(self.rect.x, self.rect.y, self.npc_type, self.layer)

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
        x = -target.rect.centerx + EDITOR_WIDTH // 2
        y = -target.rect.centery + (WINDOW_HEIGHT - TOOLBAR_HEIGHT - STATUSBAR_HEIGHT) // 2
        x = min(0, x); y = min(0, y)
        x = max(-(self.width - EDITOR_WIDTH), x)
        y = max(-(self.height - (WINDOW_HEIGHT - TOOLBAR_HEIGHT - STATUSBAR_HEIGHT)), y)
        self.camera = pygame.Rect(x, y, self.width, self.height)

    def move(self, dx, dy):
        self.camera.x += dx; self.camera.y += dy
        self.camera.x = min(0, max(-(self.width - EDITOR_WIDTH), self.camera.x))
        self.camera.y = min(0, max(-(self.height - (WINDOW_HEIGHT - TOOLBAR_HEIGHT - STATUSBAR_HEIGHT)), self.camera.y))

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
# GUI ELEMENTS
# -------------------------
class Button:
    def __init__(self, rect, text, callback=None):
        self.rect = pygame.Rect(rect); self.text = text; self.callback = callback; self.hovered = False
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION: self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos) and self.callback: self.callback(); return True
        return False
    def draw(self, surf):
        color = SMBX_BUTTON_HOVER if self.hovered else SMBX_TOOLBAR
        pygame.draw.rect(surf, color, self.rect); pygame.draw.rect(surf, SMBX_BUTTON_BORDER, self.rect, 1)
        draw_text(surf, self.text, self.rect.center, BLACK, FONT_SMALL, True)

class Sidebar:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.categories = ["Blocks", "NPCs", "Layers"]
        self.current_category = "Blocks"
        self.items = {
            "Blocks": ['ground', 'brick', 'question', 'pipe', 'platform', 'coin'],
            "NPCs": ['goomba', 'koopa', 'mushroom'],
            "Layers": []
        }
        self.selected_item = 'ground'
    def draw(self, surf, level):
        pygame.draw.rect(surf, SMBX_SIDEBAR, self.rect)
        tab_w = self.rect.width // len(self.categories)
        for i, cat in enumerate(self.categories):
            r = pygame.Rect(self.rect.x + i*tab_w, self.rect.y, tab_w, 25)
            pygame.draw.rect(surf, WHITE if cat == self.current_category else SMBX_TOOLBAR, r)
            pygame.draw.rect(surf, BLACK, r, 1)
            draw_text(surf, cat, r.center, BLACK, FONT_SMALL, True)
        if self.current_category == "Layers": self.draw_layers(surf, level)
        else: self.draw_items(surf)

    def draw_items(self, surf):
        items = self.items[self.current_category]; cols = 5; cell_size = 38
        for i, item in enumerate(items):
            col, row = i % cols, i // cols
            x, y = self.rect.x + 5 + col * cell_size, self.rect.y + 30 + row * cell_size
            icon_rect = pygame.Rect(x, y, 32, 32)
            pygame.draw.rect(surf, WHITE, icon_rect)
            if item in themes[current_theme]: color = themes[current_theme][item]
            elif item == 'goomba' or item == 'koopa': color = themes[current_theme]['enemy']
            elif item == 'mushroom': color = themes[current_theme]['powerup']
            else: color = GRAY
            pygame.draw.rect(surf, color, icon_rect.inflate(-4, -4))
            pygame.draw.rect(surf, BLACK, icon_rect, 1)
            if item == self.selected_item: pygame.draw.rect(surf, SMBX_SELECTION, icon_rect, 2)

    def draw_layers(self, surf, level):
        y = self.rect.y + 30; section = level.current_section()
        add_btn_rect = pygame.Rect(self.rect.x + 5, y, self.rect.width - 10, 25)
        pygame.draw.rect(surf, GREEN, add_btn_rect)
        draw_text(surf, "+ Add Layer", add_btn_rect.center, WHITE, FONT_SMALL, True)
        y += 30
        for i, layer in enumerate(section.layers):
            lr = pygame.Rect(self.rect.x + 5, y, self.rect.width - 10, 25)
            bg_color = LIGHT_GRAY if i == section.current_layer_idx else WHITE
            pygame.draw.rect(surf, bg_color, lr); pygame.draw.rect(surf, BLACK, lr, 1)
            draw_text(surf, layer.name, (lr.x + 5, lr.y + 5), BLACK)
            vis_rect = pygame.Rect(lr.right - 30, lr.y + 5, 20, 15)
            pygame.draw.rect(surf, GREEN if layer.visible else RED, vis_rect)
            y += 30

    def handle_click(self, pos, level):
        tab_w = self.rect.width // len(self.categories)
        for i, cat in enumerate(self.categories):
            r = pygame.Rect(self.rect.x + i*tab_w, self.rect.y, tab_w, 25)
            if r.collidepoint(pos): self.current_category = cat; return True
        if self.current_category == "Layers":
            add_btn_rect = pygame.Rect(self.rect.x + 5, self.rect.y + 30, self.rect.width - 10, 25)
            if add_btn_rect.collidepoint(pos):
                section = level.current_section()
                new_idx = len(section.layers)
                section.layers.append(Layer(f"Layer {new_idx + 1}"))
                section.current_layer_idx = new_idx
                return True
            y = self.rect.y + 60; section = level.current_section()
            for i, layer in enumerate(section.layers):
                lr = pygame.Rect(self.rect.x + 5, y, self.rect.width - 10, 25)
                if lr.collidepoint(pos):
                    if pos[0] > lr.right - 30: layer.visible = not layer.visible
                    else: section.current_layer_idx = i
                    return True
                y += 30
        else:
            items = self.items[self.current_category]; cols = 5; cell_size = 38
            for i, item in enumerate(items):
                col, row = i % cols, i // cols
                x, y = self.rect.x + 5 + col * cell_size, self.rect.y + 30 + row * cell_size
                if pygame.Rect(x, y, 32, 32).collidepoint(pos): self.selected_item = item; return True
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
        self.tool = 'pencil'
        self.undo_stack = []; self.redo_stack = []
        self.sidebar = Sidebar(EDITOR_WIDTH, TOOLBAR_HEIGHT, SIDEBAR_WIDTH, WINDOW_HEIGHT - TOOLBAR_HEIGHT - STATUSBAR_HEIGHT)
        self.setup_toolbar()
        self.drag_draw = False
        self.drag_erase = False

    def setup_toolbar(self):
        self.buttons = [
            Button((5, 5, 60, 30), "Save", self.save_level),
            Button((70, 5, 60, 30), "Load", self.load_level),
            Button((135, 5, 60, 30), "Test", self.toggle_playtest),
            Button((200, 5, 60, 30), "Undo", self.undo),
            Button((265, 5, 60, 30), "Redo", self.redo),
        ]

    def save_level(self):
        data = {"sections": [], "theme": current_theme}
        for sec in self.level.sections:
            sec_data = {"layers": []}
            for lay in sec.layers:
                lay_data = {"name": lay.name, "tiles": [], "npcs": []}
                for t in lay.tiles:
                    lay_data["tiles"].append({"x": t.rect.x, "y": t.rect.y, "type": t.tile_type})
                for n in lay.npcs:
                    lay_data["npcs"].append({"x": n.rect.x, "y": n.rect.y, "type": n.npc_type})
                sec_data["layers"].append(lay_data)
            data["sections"].append(sec_data)
        try:
            with open("mfb_level.json", "w") as f: json.dump(data, f)
            print("Level saved to mfb_level.json")
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
            print("Level loaded.")
        except FileNotFoundError: print("No save file found.")
        except Exception as e: print(f"Error loading: {e}")

    def toggle_playtest(self):
        self.playtest_mode = not self.playtest_mode
        if self.playtest_mode:
            self.player = Player(self.level.start_pos[0], self.level.start_pos[1])
            self.camera.update(self.player)
            print("Entered Playtest Mode")
        else: print("Exited Playtest Mode")

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
            def undo_npc(l=layer, n_pc=npc): l.npcs.remove(n_pc)
            def redo_npc(l=layer, n_pc=npc): l.npcs.add(n_pc)
            self.push_undo({'undo': undo_npc, 'redo': redo_npc})
        else:
            tile = Tile(x, y, self.sidebar.selected_item)
            layer.tiles.add(tile); layer.tile_map[key] = tile
            def undo_tile(l=layer, k=key, t=tile): l.tiles.remove(t); del l.tile_map[k]
            def redo_tile(l=layer, k=key, t=tile): l.tiles.add(t); l.tile_map[k] = t
            self.push_undo({'undo': undo_tile, 'redo': redo_tile})

    def remove_tile(self, x, y):
        layer = self.level.current_layer()
        key = (x, y)
        if key in layer.tile_map:
            tile = layer.tile_map[key]
            layer.tiles.remove(tile); del layer.tile_map[key]
            def undo(l=layer, k=key, t=tile): l.tiles.add(t); l.tile_map[k] = t
            def redo(l=layer, k=key): 
                if k in l.tile_map: t = l.tile_map[k]; l.tiles.remove(t); del l.tile_map[k]
            self.push_undo({'undo': undo, 'redo': redo})
        else:
            for npc in layer.npcs:
                if npc.rect.collidepoint(x, y):
                    layer.npcs.remove(npc)
                    def undo_npc(l=layer, n=npc): l.npcs.add(n)
                    def redo_npc(l=layer, n=npc): l.npcs.remove(n)
                    self.push_undo({'undo': undo_npc, 'redo': redo_npc})
                    break

    def handle_event(self, event):
        if event.type == pygame.QUIT: return False
        for btn in self.buttons: btn.handle_event(event)

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
            if self.sidebar.rect.collidepoint(event.pos):
                self.sidebar.handle_click(event.pos, self.level)
            elif event.pos[1] > TOOLBAR_HEIGHT and event.pos[0] < EDITOR_WIDTH:
                if not self.playtest_mode:
                    world_x, world_y = event.pos[0] - self.camera.camera.x, event.pos[1] - self.camera.camera.y
                    grid_x, grid_y = (world_x // GRID_SIZE) * GRID_SIZE, (world_y // GRID_SIZE) * GRID_SIZE
                    if event.button == 1: 
                        self.drag_draw = True
                        self.place_tile(grid_x, grid_y)
                    elif event.button == 3: 
                        self.drag_erase = True
                        self.remove_tile(grid_x, grid_y)
        
        if event.type == pygame.MOUSEMOTION:
            if not self.playtest_mode:
                world_x, world_y = event.pos[0] - self.camera.camera.x, event.pos[1] - self.camera.camera.y
                grid_x, grid_y = (world_x // GRID_SIZE) * GRID_SIZE, (world_y // GRID_SIZE) * GRID_SIZE
                
                if self.drag_draw:
                    self.place_tile(grid_x, grid_y)
                elif self.drag_erase:
                    self.remove_tile(grid_x, grid_y)

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
        surf.fill(SMBX_BG)
        clip_rect = pygame.Rect(0, TOOLBAR_HEIGHT, EDITOR_WIDTH, WINDOW_HEIGHT - TOOLBAR_HEIGHT - STATUSBAR_HEIGHT)
        surf.set_clip(clip_rect)
        surf.fill(themes[current_theme]['background'])
        if not self.playtest_mode:
            start_col = int(-self.camera.camera.x // GRID_SIZE)
            end_col = start_col + (EDITOR_WIDTH // GRID_SIZE) + 2
            start_row = int(-self.camera.camera.y // GRID_SIZE)
            end_row = start_row + (clip_rect.height // GRID_SIZE) + 2
            for c in range(start_col, end_col):
                x = c * GRID_SIZE + self.camera.camera.x
                pygame.draw.line(surf, SMBX_GRID, (x, clip_rect.y), (x, clip_rect.y + clip_rect.height))
            for r in range(start_row, end_row):
                y = r * GRID_SIZE + self.camera.camera.y
                pygame.draw.line(surf, SMBX_GRID, (0, y), (EDITOR_WIDTH, y))
        sprites = self.level.current_section().all_sprites()
        for sprite in sprites: surf.blit(sprite.image, self.camera.apply(sprite))
        if self.playtest_mode and self.player: surf.blit(self.player.image, self.camera.apply(self.player))
        surf.set_clip(None)
        pygame.draw.rect(surf, SMBX_TOOLBAR, (0, 0, EDITOR_WIDTH, TOOLBAR_HEIGHT))
        for btn in self.buttons: btn.draw(surf)
        self.sidebar.draw(surf, self.level)
        pygame.draw.rect(surf, SMBX_STATUSBAR, (0, WINDOW_HEIGHT - STATUSBAR_HEIGHT, WINDOW_WIDTH, STATUSBAR_HEIGHT))
        mode = "PLAYTEST" if self.playtest_mode else "EDITOR"
        status = f"MARIO FAN BUILDER | Mode: {mode} | Layer: {self.level.current_layer().name}"
        draw_text(surf, status, (10, WINDOW_HEIGHT - STATUSBAR_HEIGHT + 5), WHITE, FONT_SMALL)
        return surf

# -------------------------
# MAIN MENU
# -------------------------
def main_menu(screen):
    buttons = [
        Button((WINDOW_WIDTH//2 - 100, 350, 200, 50), "New Level", lambda: "NEW"),
        Button((WINDOW_WIDTH//2 - 100, 420, 200, 50), "Quit", lambda: "QUIT")
    ]
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "QUIT"
            for btn in buttons:
                res = btn.handle_event(event)
                if res: return btn.callback()
        
        # Drawing
        screen.fill(BLACK)
        # Famicon Style Header
        pygame.draw.rect(screen, RED, (0, 0, WINDOW_WIDTH, 100))
        pygame.draw.rect(screen, (150, 0, 0), (0, 100, WINDOW_WIDTH, 10))
        
        draw_text(screen, "MARIO FAN BUILDER", (WINDOW_WIDTH//2, 40), WHITE, FONT_TITLE, True)
        draw_text(screen, "by CATSAN [C]. AC Holding", (WINDOW_WIDTH//2, 80), LIGHT_GRAY, FONT_SMALL, True)

        # Decorative Famicon Style Border
        pygame.draw.rect(screen, BLUE, (50, 150, WINDOW_WIDTH-100, 180), 3)
        draw_text(screen, "SELECT OPTION", (WINDOW_WIDTH//2, 200), WHITE, FONT, True)
        draw_text(screen, "Engine Ver 1.0", (WINDOW_WIDTH//2, 250), LIGHT_GRAY, FONT_SMALL, True)

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
