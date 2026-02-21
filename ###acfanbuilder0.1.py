import pygame
import sys
import os
import math
import struct
import random
from collections import deque, defaultdict

# -------------------------
# CONSTANTS & CONFIG
# -------------------------
WINDOW_WIDTH, WINDOW_HEIGHT = 1024, 700
SIDEBAR_WIDTH = 200
MENU_HEIGHT = 20
TOOLBAR_HEIGHT = 26
STATUSBAR_HEIGHT = 24
CANVAS_X = SIDEBAR_WIDTH
CANVAS_Y = MENU_HEIGHT + TOOLBAR_HEIGHT
CANVAS_WIDTH = WINDOW_WIDTH - SIDEBAR_WIDTH
CANVAS_HEIGHT = WINDOW_HEIGHT - CANVAS_Y - STATUSBAR_HEIGHT

GRID_SIZE = 32
FPS = 60  # Famicom Speed
ZOOM_MIN, ZOOM_MAX = 0.5, 2.0
ZOOM_STEP = 0.25

# --- SMBX 1.3 "Windows Classic" Style Colors ---
SYS_BG         = (212, 208, 200) # Button Face / App Workspace
SYS_BTN_FACE   = (212, 208, 200)
SYS_BTN_LIGHT  = (255, 255, 255) # Highlight
SYS_BTN_DARK   = (128, 128, 128) # Shadow
SYS_BTN_DK_SHD = (64, 64, 64)    # Dark Shadow
SYS_WINDOW     = (255, 255, 255) # Window Background (white)
SYS_HIGHLIGHT  = (0, 0, 128)     # Selected item background
SYS_TEXT       = (0, 0, 0)       # Text Color
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128)
SMBX_BG = (0, 0, 0)
SMBX_GRID = (50, 50, 50)

# Physics
GRAVITY = 0.5
JUMP_STRENGTH = -10
MOVE_SPEED = 4
TERMINAL_VELOCITY = 10

pygame.init()
pygame.display.set_caption("Mario Fan Builder - CATSAN [C] AC Holding")

FONT = pygame.font.Font(None, 20)
FONT_MENU = pygame.font.Font(None, 20)
FONT_SMALL = pygame.font.Font(None, 16)
FONT_TITLE = pygame.font.Font(None, 28)

# -------------------------
# SMBX ID MAPPINGS (Blocks, BGOs, NPCs)
# -------------------------
TILE_SMBX_IDS = {
    'ground': 1, 'grass': 2, 'sand': 3, 'dirt': 4,
    'brick': 45, 'question': 34, 'pipe_vertical': 112, 'pipe_horizontal': 113,
    'platform': 159, 'coin': 10, 'bridge': 47,
    'stone': 48, 'ice': 55, 'mushroom_platform': 91, 'pswitch': 60,
}
SMBX_TO_TILE = {v: k for k, v in TILE_SMBX_IDS.items()}

BGO_SMBX_IDS = {
    'cloud': 5, 'bush': 6, 'hill': 7, 'fence': 8, 'bush_3': 9,
    'tree': 10, 'castle': 11, 'waterfall': 12, 'sign': 13,
}
SMBX_TO_BGO = {v: k for k, v in BGO_SMBX_IDS.items()}

NPC_SMBX_IDS = {
    'goomba': 1, 'koopa_green': 2, 'koopa_red': 3, 'paratroopa_green': 4,
    'paratroopa_red': 5, 'piranha': 6, 'hammer_bro': 7, 'lakitu': 8,
    'mushroom': 9, 'flower': 10, 'star': 11, '1up': 12,
    'buzzy': 13, 'spiny': 14, 'cheep': 15, 'blooper': 16,
    'thwomp': 17, 'bowser': 18, 'boo': 19,
}
SMBX_TO_NPC = {v: k for k, v in NPC_SMBX_IDS.items()}

TILE_ID_TO_NAME = {v: k for k, v in TILE_SMBX_IDS.items()}
BGO_ID_TO_NAME = {v: k for k, v in BGO_SMBX_IDS.items()}
NPC_ID_TO_NAME = {v: k for k, v in NPC_SMBX_IDS.items()}

# -------------------------
# THEMES (visual representation)
# -------------------------
themes = {
    'SMB1': {
        'background': (92, 148, 252),
        'ground': (0, 128, 0),
        'brick': (180, 80, 40),
        'question': (255, 200, 0),
        'coin': (255, 255, 0),
        'pipe_vertical': (0, 200, 0),
        'platform': (139, 69, 19),
        'goomba': (255, 0, 0),
        'koopa_green': (0, 255, 0),
        'mushroom': (255, 0, 255),
        'flower': (255, 100, 255),
        'star': (255, 255, 0),
        'bgo_cloud': (200, 200, 200),
        'bgo_bush': (0, 150, 0),
    },
    'SMB3': {
        'background': (0, 0, 0),
        'ground': (160, 120, 80),
        'brick': (180, 100, 60),
        'question': (255, 210, 0),
        'coin': (255, 255, 100),
        'pipe_vertical': (0, 180, 0),
        'platform': (100, 100, 100),
        'goomba': (255, 50, 50),
        'koopa_green': (0, 200, 0),
        'mushroom': (255, 100, 255),
        'flower': (255, 150, 255),
        'star': (255, 255, 0),
        'bgo_cloud': (150, 150, 150),
        'bgo_bush': (0, 100, 0),
    }
}
current_theme = 'SMB1'

# -------------------------
# HELPER FUNCTIONS (GUI DRAWING)
# -------------------------
def draw_edge(surf, rect, raised=True):
    r = pygame.Rect(rect)
    tl_color = SYS_BTN_LIGHT if raised else SYS_BTN_DK_SHD
    br_color = SYS_BTN_DK_SHD if raised else SYS_BTN_LIGHT
    tl_inner = SYS_BTN_FACE if raised else SYS_BTN_DARK
    br_inner = SYS_BTN_DARK if raised else SYS_BTN_FACE

    pygame.draw.line(surf, tl_color, r.topleft, r.topright)
    pygame.draw.line(surf, tl_color, r.topleft, r.bottomleft)
    pygame.draw.line(surf, br_color, r.bottomleft, r.bottomright)
    pygame.draw.line(surf, br_color, r.topright, r.bottomright)

    pygame.draw.line(surf, tl_inner, (r.left+1, r.top+1), (r.right-1, r.top+1))
    pygame.draw.line(surf, tl_inner, (r.left+1, r.top+1), (r.left+1, r.bottom-1))
    pygame.draw.line(surf, br_inner, (r.left+1, r.bottom-1), (r.right-1, r.bottom-1))
    pygame.draw.line(surf, br_inner, (r.right-1, r.top+1), (r.right-1, r.bottom-1))

def draw_text(surf, text, pos, color=SYS_TEXT, font=FONT, center=False):
    t = font.render(text, True, color)
    r = t.get_rect(center=pos) if center else t.get_rect(topleft=pos)
    surf.blit(t, r)

def get_theme_color(name):
    theme = themes[current_theme]
    return theme.get(name, (128, 128, 128))

# -------------------------
# ICON DRAWING HELPERS
# -------------------------
def draw_icon_select(surf, rect, color=SYS_TEXT):
    """Dashed selection rectangle icon"""
    r = rect.inflate(-6, -6)
    for i in range(0, r.width, 4):
        if (i // 4) % 2 == 0:
            pygame.draw.line(surf, color, (r.x + i, r.y), (min(r.x + i + 3, r.right), r.y))
            pygame.draw.line(surf, color, (r.x + i, r.bottom), (min(r.x + i + 3, r.right), r.bottom))
    for i in range(0, r.height, 4):
        if (i // 4) % 2 == 0:
            pygame.draw.line(surf, color, (r.x, r.y + i), (r.x, min(r.y + i + 3, r.bottom)))
            pygame.draw.line(surf, color, (r.right, r.y + i), (r.right, min(r.y + i + 3, r.bottom)))

def draw_icon_pencil(surf, rect, color=SYS_TEXT):
    """Pencil icon"""
    cx, cy = rect.center
    pts = [(cx-1, cy+6), (cx+5, cy-3), (cx+3, cy-5), (cx-3, cy+4)]
    pygame.draw.polygon(surf, color, pts, 1)
    pygame.draw.line(surf, color, (cx-1, cy+6), (cx-4, cy+8))
    pygame.draw.line(surf, color, (cx-4, cy+8), (cx-2, cy+5))

def draw_icon_eraser(surf, rect, color=SYS_TEXT):
    """Eraser icon"""
    r = rect.inflate(-8, -8)
    pygame.draw.rect(surf, color, (r.x, r.centery-3, r.width, 7), 1)
    pygame.draw.line(surf, color, (r.x + r.width//2, r.centery-3), (r.x + r.width//2, r.centery+4))

def draw_icon_fill(surf, rect, color=SYS_TEXT):
    """Paint bucket icon - small filled square + drop"""
    cx, cy = rect.center
    pygame.draw.rect(surf, color, (cx-5, cy-4, 8, 8), 1)
    pygame.draw.rect(surf, color, (cx-4, cy-3, 6, 6))
    pygame.draw.circle(surf, color, (cx+5, cy+4), 2)

def draw_icon_new(surf, rect, color=SYS_TEXT):
    """New file - blank page with folded corner"""
    r = rect.inflate(-8, -6)
    fold = 5
    pts = [(r.x, r.y), (r.right-fold, r.y), (r.right, r.y+fold), (r.right, r.bottom), (r.x, r.bottom)]
    pygame.draw.polygon(surf, color, pts, 1)
    pygame.draw.line(surf, color, (r.right-fold, r.y), (r.right-fold, r.y+fold))
    pygame.draw.line(surf, color, (r.right-fold, r.y+fold), (r.right, r.y+fold))

def draw_icon_open(surf, rect, color=SYS_TEXT):
    """Open folder icon"""
    cx, cy = rect.center
    # Folder body
    pygame.draw.rect(surf, color, (cx-7, cy-2, 14, 9), 1)
    # Tab
    pygame.draw.rect(surf, color, (cx-7, cy-5, 6, 4), 1)

def draw_icon_save(surf, rect, color=SYS_TEXT):
    """Floppy disk icon"""
    r = rect.inflate(-8, -6)
    pygame.draw.rect(surf, color, r, 1)
    # Label area
    pygame.draw.rect(surf, color, (r.x+2, r.y+2, r.width-4, r.height//2-2))
    # Shutter
    pygame.draw.rect(surf, SYS_BTN_FACE, (r.x+2, r.y+2, r.width-4, r.height//2-2))
    pygame.draw.rect(surf, color, (r.x+5, r.y+2, r.width-10, r.height//2-2), 1)
    # Bottom notch
    pygame.draw.rect(surf, color, (r.x+r.width//3, r.bottom-5, r.width//3, 5))

def draw_icon_undo(surf, rect, color=SYS_TEXT):
    """Undo arrow"""
    cx, cy = rect.center
    pygame.draw.arc(surf, color, (cx-6, cy-4, 12, 10), math.pi*0.3, math.pi*1.1, 2)
    # Arrow head
    pygame.draw.polygon(surf, color, [(cx-6, cy-4), (cx-9, cy), (cx-3, cy-1)])

def draw_icon_redo(surf, rect, color=SYS_TEXT):
    """Redo arrow"""
    cx, cy = rect.center
    pygame.draw.arc(surf, color, (cx-6, cy-4, 12, 10), math.pi*1.9, math.pi*0.7+math.pi*2, 2)
    pygame.draw.polygon(surf, color, [(cx+6, cy-4), (cx+9, cy), (cx+3, cy-1)])

def draw_icon_play(surf, rect, color=SYS_TEXT):
    """Play/test triangle"""
    cx, cy = rect.center
    pygame.draw.polygon(surf, color, [(cx-4, cy-6), (cx-4, cy+6), (cx+6, cy)])

def draw_icon_props(surf, rect, color=SYS_TEXT):
    """Properties - gear/info i"""
    cx, cy = rect.center
    draw_text(surf, "i", (cx, cy), color, FONT_SMALL, True)
    pygame.draw.circle(surf, color, (cx, cy-5), 2)

# Map tool names to icon draw functions
ICON_DRAW_FNS = {
    'select': draw_icon_select,
    'pencil': draw_icon_pencil,
    'eraser': draw_icon_eraser,
    'fill':   draw_icon_fill,
    'new':    draw_icon_new,
    'open':   draw_icon_open,
    'save':   draw_icon_save,
    'undo':   draw_icon_undo,
    'redo':   draw_icon_redo,
    'play':   draw_icon_play,
    'props':  draw_icon_props,
}

# -------------------------
# SPRITE CLASSES
# -------------------------
class GameObject(pygame.sprite.Sprite):
    def __init__(self, x, y, obj_type, layer=0):
        super().__init__()
        self.rect = pygame.Rect(x, y, GRID_SIZE, GRID_SIZE)
        self.layer = layer
        self.obj_type = obj_type

    def update_image(self):
        raise NotImplementedError

class Tile(GameObject):
    def __init__(self, x, y, tile_type, layer=0):
        super().__init__(x, y, tile_type, layer)
        self.tile_type = tile_type
        self.is_solid = tile_type not in ['coin']
        self.update_image()

    def update_image(self):
        self.image = pygame.Surface((GRID_SIZE, GRID_SIZE))
        self.image.fill(get_theme_color(self.tile_type))
        if self.tile_type == 'question':
            draw_text(self.image, '?', (GRID_SIZE//2, GRID_SIZE//2), BLACK, FONT_SMALL, True)
        elif self.tile_type == 'brick':
            pygame.draw.line(self.image, BLACK, (0, GRID_SIZE//2), (GRID_SIZE, GRID_SIZE//2), 2)
            pygame.draw.line(self.image, BLACK, (GRID_SIZE//2, 0), (GRID_SIZE//2, GRID_SIZE), 2)
        elif self.tile_type == 'coin':
            pygame.draw.circle(self.image, YELLOW, (GRID_SIZE//2, GRID_SIZE//2), GRID_SIZE//3)

class BGO(GameObject):
    def __init__(self, x, y, bgo_type, layer=0):
        super().__init__(x, y, bgo_type, layer)
        self.bgo_type = bgo_type
        self.update_image()

    def update_image(self):
        self.image = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
        if self.bgo_type.startswith('bgo_'):
            color = get_theme_color(self.bgo_type)
        else:
            color = (150, 150, 150)
        pygame.draw.rect(self.image, color, self.image.get_rect(), 2)

class NPC(GameObject):
    def __init__(self, x, y, npc_type, layer=0):
        super().__init__(x, y, npc_type, layer)
        self.npc_type = npc_type
        self.velocity = pygame.Vector2(random.choice([-1,1]), 0)
        self.direction = 1 if self.velocity.x > 0 else -1
        self.state = 'normal'
        self.frame = 0
        self.update_image()

    def update_image(self):
        self.image = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
        color = get_theme_color(self.npc_type)
        if self.npc_type == 'goomba':
            pygame.draw.ellipse(self.image, color, (4, 4, GRID_SIZE-8, GRID_SIZE-4))
        elif self.npc_type.startswith('koopa'):
            pygame.draw.rect(self.image, color, (4, 4, GRID_SIZE-8, GRID_SIZE-4))
            if self.state == 'shell':
                pygame.draw.circle(self.image, (200,100,0), (GRID_SIZE//2, GRID_SIZE//2), GRID_SIZE//3)
        elif self.npc_type == 'mushroom':
            pygame.draw.ellipse(self.image, color, (4, 4, GRID_SIZE-8, GRID_SIZE-8))
        else:
            pygame.draw.rect(self.image, color, (4, 4, GRID_SIZE-8, GRID_SIZE-4))

    def update(self, solid_tiles, player=None):
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
                    if self.velocity.x > 0:
                        self.rect.right = t.rect.left
                    else:
                        self.rect.left = t.rect.right
                    self.velocity.x *= -1
                elif axis == 'y':
                    if self.velocity.y > 0:
                        self.rect.bottom = t.rect.top
                        self.velocity.y = 0
                    else:
                        self.rect.top = t.rect.bottom
                        self.velocity.y = 0

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.rect = pygame.Rect(x, y, GRID_SIZE, GRID_SIZE)
        self.image = pygame.Surface((GRID_SIZE, GRID_SIZE))
        self.image.fill(RED)
        self.velocity = pygame.Vector2(0, 0)
        self.on_ground = False
        self.powerup_state = 0
        self.invincible = 0
        self.coins = 0
        self.score = 0

    def update(self, solid_tiles, npc_group):
        keys = pygame.key.get_pressed()
        self.velocity.x = 0
        if keys[pygame.K_LEFT]:
            self.velocity.x = -MOVE_SPEED
        if keys[pygame.K_RIGHT]:
            self.velocity.x = MOVE_SPEED
        if keys[pygame.K_SPACE] and self.on_ground:
            self.velocity.y = JUMP_STRENGTH
            self.on_ground = False

        self.velocity.y += GRAVITY
        self.velocity.y = min(self.velocity.y, TERMINAL_VELOCITY)

        self.rect.x += self.velocity.x
        self.collide(solid_tiles, 'x')
        self.rect.y += self.velocity.y
        self.on_ground = False
        self.collide(solid_tiles, 'y')

        hits = pygame.sprite.spritecollide(self, npc_group, False)
        for npc in hits:
            if self.velocity.y > 0 and self.rect.bottom <= npc.rect.centery:
                npc.kill()
                self.velocity.y = JUMP_STRENGTH * 0.7
                self.score += 100
            else:
                if self.invincible <= 0:
                    if self.powerup_state > 0:
                        self.powerup_state = 0
                        self.invincible = 120
                        self.rect.height = GRID_SIZE
                    else:
                        self.rect.x, self.rect.y = 100, 500
                        self.score = 0
                        self.coins = 0

        if self.invincible > 0:
            self.invincible -= 1

    def collide(self, tiles, axis):
        for t in tiles:
            if self.rect.colliderect(t.rect):
                if axis == 'x':
                    if self.velocity.x > 0:
                        self.rect.right = t.rect.left
                    else:
                        self.rect.left = t.rect.right
                    self.velocity.x = 0
                elif axis == 'y':
                    if self.velocity.y > 0:
                        self.rect.bottom = t.rect.top
                        self.velocity.y = 0
                        self.on_ground = True
                    else:
                        self.rect.top = t.rect.bottom
                        self.velocity.y = 0

    def draw(self, surf, camera_offset):
        if self.invincible > 0 and (self.invincible // 5) % 2 == 0:
            return
        pos = self.rect.move(camera_offset)
        surf.blit(self.image, pos)

# -------------------------
# CAMERA & LEVEL STRUCTURE
# -------------------------
class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width, self.height = width, height
        self.zoom = 1.0

    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)

    def apply_rect(self, rect):
        return pygame.Rect(rect.x + self.camera.x, rect.y + self.camera.y, rect.w, rect.h)

    def update(self, target):
        x = -target.rect.centerx + (CANVAS_WIDTH // 2) / self.zoom
        y = -target.rect.centery + (CANVAS_HEIGHT // 2) / self.zoom
        x = min(0, x)
        y = min(0, y)
        x = max(-(self.width - CANVAS_WIDTH / self.zoom), x)
        y = max(-(self.height - CANVAS_HEIGHT / self.zoom), y)
        self.camera = pygame.Rect(x, y, self.width, self.height)

    def move(self, dx, dy):
        self.camera.x += dx / self.zoom
        self.camera.y += dy / self.zoom
        self.camera.x = max(-(self.width - CANVAS_WIDTH / self.zoom), min(0, self.camera.x))
        self.camera.y = max(-(self.height - CANVAS_HEIGHT / self.zoom), min(0, self.camera.y))

class Layer:
    def __init__(self, name="Layer 1", visible=True, locked=False):
        self.name = name
        self.visible = visible
        self.locked = locked
        self.tiles = pygame.sprite.Group()
        self.bgos = pygame.sprite.Group()
        self.npcs = pygame.sprite.Group()
        self.tile_map = {}

    def all_sprites(self, sorted_by_layer=True):
        g = pygame.sprite.Group()
        g.add(self.bgos.sprites())
        g.add(self.tiles.sprites())
        g.add(self.npcs.sprites())
        return g

    def add_tile(self, tile):
        self.tiles.add(tile)
        self.tile_map[(tile.rect.x, tile.rect.y)] = tile

    def remove_tile(self, tile):
        self.tiles.remove(tile)
        key = (tile.rect.x, tile.rect.y)
        if key in self.tile_map:
            del self.tile_map[key]

class Section:
    def __init__(self, width=100, height=30):
        self.width = width * GRID_SIZE
        self.height = height * GRID_SIZE
        self.layers = [Layer("Layer 1")]
        self.current_layer_idx = 0
        self.bg_color = (92, 148, 252)
        self.music = 1

    def current_layer(self):
        return self.layers[self.current_layer_idx]

    def all_sprites(self, visible_only=True):
        group = pygame.sprite.Group()
        for layer in self.layers:
            if not visible_only or layer.visible:
                group.add(layer.all_sprites().sprites())
        return group

    def get_solid_tiles(self):
        solids = []
        for layer in self.layers:
            if layer.visible:
                for tile in layer.tiles:
                    if tile.is_solid:
                        solids.append(tile)
        return solids

class Level:
    def __init__(self):
        self.sections = [Section()]
        self.current_section_idx = 0
        self.start_pos = (100, 500)
        self.name = "Untitled"
        self.author = "Unknown"

    def current_section(self):
        return self.sections[self.current_section_idx]

    def current_layer(self):
        return self.current_section().current_layer()

# -------------------------
# GUI ELEMENTS
# -------------------------
class ClassicButton:
    def __init__(self, rect, text, callback=None):
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
        draw_edge(surf, self.rect, raised=not self.pressed)
        fill_rect = self.rect.inflate(-4, -4)
        pygame.draw.rect(surf, SYS_BTN_FACE, fill_rect)
        txt_pos = (self.rect.centerx + (1 if self.pressed else 0), self.rect.centery + (1 if self.pressed else 0))
        draw_text(surf, self.text, txt_pos, SYS_TEXT, FONT, True)

class ToolbarButton:
    """Icon-only toolbar button with 3D popup on hover"""
    def __init__(self, rect, icon_key, callback=None, tooltip=""):
        self.rect = pygame.Rect(rect)
        self.icon_key = icon_key   # key into ICON_DRAW_FNS
        self.callback = callback
        self.hovered = False
        self.pressed = False
        self.tooltip = tooltip

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
        if self.pressed:
            pygame.draw.rect(surf, SYS_BTN_FACE, self.rect)
            pygame.draw.line(surf, SYS_BTN_DARK, self.rect.topleft, self.rect.topright)
            pygame.draw.line(surf, SYS_BTN_DARK, self.rect.topleft, self.rect.bottomleft)
        elif self.hovered:
            pygame.draw.rect(surf, SYS_BTN_FACE, self.rect)
            pygame.draw.line(surf, SYS_BTN_LIGHT, self.rect.topleft, self.rect.topright)
            pygame.draw.line(surf, SYS_BTN_LIGHT, self.rect.topleft, self.rect.bottomleft)
            pygame.draw.line(surf, SYS_BTN_DARK, self.rect.bottomleft, self.rect.bottomright)
            pygame.draw.line(surf, SYS_BTN_DARK, self.rect.topright, self.rect.bottomright)
        else:
            pygame.draw.rect(surf, SYS_BTN_FACE, self.rect)

        # Draw icon
        draw_fn = ICON_DRAW_FNS.get(self.icon_key)
        if draw_fn:
            offset = (1, 1) if self.pressed else (0, 0)
            icon_rect = self.rect.move(offset[0], offset[1])
            draw_fn(surf, icon_rect)

class Sidebar:
    def __init__(self):
        self.rect = pygame.Rect(0, CANVAS_Y, SIDEBAR_WIDTH, CANVAS_HEIGHT)
        self.categories = ["Tiles", "BGOs", "NPCs", "Layers"]
        self.current_category = "Tiles"
        self.items = {
            "Tiles": list(TILE_SMBX_IDS.keys()),
            "BGOs": list(BGO_SMBX_IDS.keys()),
            "NPCs": list(NPC_SMBX_IDS.keys()),
            "Layers": []
        }
        self.selected_item = 'ground'
        self.tab_h = 20
        self.title_h = 18

    def draw(self, surf, level):
        pygame.draw.rect(surf, SYS_BTN_FACE, self.rect)
        draw_edge(surf, self.rect, raised=False)

        title_rect = pygame.Rect(self.rect.x+2, self.rect.y+2, self.rect.width-4, self.title_h)
        pygame.draw.rect(surf, SYS_HIGHLIGHT, title_rect)
        draw_text(surf, "Item Selection", (title_rect.x + 3, title_rect.y + 2), WHITE, FONT_SMALL)

        tab_y = self.rect.y + self.title_h + 2
        tab_w = self.rect.width // len(self.categories)
        for i, cat in enumerate(self.categories):
            r = pygame.Rect(self.rect.x + 2 + i*tab_w, tab_y, tab_w-2, self.tab_h)
            is_sel = (cat == self.current_category)
            if is_sel:
                pygame.draw.rect(surf, SYS_WINDOW, r)
                pygame.draw.line(surf, SYS_BTN_LIGHT, r.topleft, r.topright)
                pygame.draw.line(surf, SYS_BTN_LIGHT, r.topleft, r.bottomleft)
                pygame.draw.line(surf, SYS_BTN_DARK, r.topright, r.bottomright)
                pygame.draw.line(surf, SYS_BTN_DARK, r.bottomleft, r.bottomright)
            else:
                pygame.draw.rect(surf, SYS_BTN_FACE, r)
                draw_edge(surf, r, raised=True)
            draw_text(surf, cat, r.center, SYS_TEXT, FONT_SMALL, True)

        content_rect = pygame.Rect(self.rect.x + 2, tab_y + self.tab_h, self.rect.width - 4,
                                   self.rect.height - self.title_h - self.tab_h - 4)
        pygame.draw.rect(surf, SYS_WINDOW, content_rect)

        if self.current_category == "Layers":
            self.draw_layers(surf, content_rect, level)
        else:
            self.draw_items(surf, content_rect)

    def draw_items(self, surf, area):
        items = self.items[self.current_category]
        x_off, y_off = 4, 4
        size = 32
        for i, item in enumerate(items):
            r = pygame.Rect(area.x + x_off + (i%5)*36, area.y + y_off + (i//5)*36, size, size)
            if item == self.selected_item:
                pygame.draw.rect(surf, SYS_HIGHLIGHT, r)
            if self.current_category == "Tiles":
                color = get_theme_color(item)
            elif self.current_category == "BGOs":
                color = get_theme_color('bgo_' + item if not item.startswith('bgo_') else item)
            else:
                color = get_theme_color(item)
            pygame.draw.rect(surf, color, r.inflate(-2, -2))
            pygame.draw.rect(surf, BLACK, r.inflate(-2, -2), 1)

    def draw_layers(self, surf, area, level):
        y = area.y + 5
        section = level.current_section()
        for i, layer in enumerate(section.layers):
            r = pygame.Rect(area.x + 2, y, area.width - 4, 18)
            color = SYS_HIGHLIGHT if i == section.current_layer_idx else SYS_WINDOW
            pygame.draw.rect(surf, color, r)
            draw_text(surf, layer.name, (r.x + 5, r.y + 1),
                      WHITE if color == SYS_HIGHLIGHT else SYS_TEXT, FONT_SMALL)
            eye_color = GREEN if layer.visible else RED
            pygame.draw.circle(surf, eye_color, (r.right - 8, r.centery), 4)
            lock_color = GRAY if layer.locked else SYS_BTN_FACE
            pygame.draw.rect(surf, lock_color, (r.right - 20, r.y + 2, 8, 8))
            y += 22

    def handle_click(self, pos, level):
        tab_y = self.rect.y + self.title_h + 2
        tab_w = self.rect.width // len(self.categories)
        for i, cat in enumerate(self.categories):
            r = pygame.Rect(self.rect.x + 2 + i*tab_w, tab_y, tab_w-2, self.tab_h)
            if r.collidepoint(pos):
                self.current_category = cat
                return True
        content_rect = pygame.Rect(self.rect.x + 2, tab_y + self.tab_h, self.rect.width - 4,
                                   self.rect.height - self.title_h - self.tab_h - 4)
        if self.current_category == "Layers":
            y = content_rect.y + 5
            section = level.current_section()
            for i, layer in enumerate(section.layers):
                r = pygame.Rect(content_rect.x + 2, y, content_rect.width - 4, 18)
                if r.collidepoint(pos):
                    if pos[0] > r.right - 20:
                        layer.locked = not layer.locked
                    elif pos[0] > r.right - 35:
                        layer.visible = not layer.visible
                    else:
                        section.current_layer_idx = i
                    return True
                y += 22
        else:
            items = self.items[self.current_category]
            x_off, y_off = 4, 4
            for i, item in enumerate(items):
                r = pygame.Rect(content_rect.x + x_off + (i%5)*36, content_rect.y + y_off + (i//5)*36, 32, 32)
                if r.collidepoint(pos):
                    self.selected_item = item
                    return True
        return False

# -------------------------
# FILE HANDLING
# -------------------------
def read_lvl(filename):
    level = Level()
    section = level.current_section()
    try:
        with open(filename, 'rb') as f:
            num_blocks = struct.unpack('<I', f.read(4))[0]
            num_bgos = struct.unpack('<I', f.read(4))[0]
            num_npcs = struct.unpack('<I', f.read(4))[0]
            for _ in range(num_blocks):
                data = f.read(20)
                x, y, sid, layer, event = struct.unpack('<IIIII', data)
                if sid in TILE_ID_TO_NAME:
                    tile = Tile(x, y, TILE_ID_TO_NAME[sid], layer)
                    section.layers[layer].add_tile(tile)
            for _ in range(num_bgos):
                data = f.read(20)
                x, y, sid, layer, event = struct.unpack('<IIIII', data)
                if sid in BGO_ID_TO_NAME:
                    bgo = BGO(x, y, BGO_ID_TO_NAME[sid], layer)
                    section.layers[layer].bgos.add(bgo)
            for _ in range(num_npcs):
                data = f.read(20)
                x, y, sid, layer, event = struct.unpack('<IIIII', data)
                if sid in NPC_ID_TO_NAME:
                    npc = NPC(x, y, NPC_ID_TO_NAME[sid], layer)
                    section.layers[layer].npcs.add(npc)
        return level
    except Exception as e:
        print("Error loading level:", e)
        return Level()

def write_lvl(filename, level):
    section = level.current_section()
    blocks, bgos, npcs = [], [], []
    for layer_idx, layer in enumerate(section.layers):
        for tile in layer.tiles:
            sid = TILE_SMBX_IDS.get(tile.tile_type, 1)
            blocks.append((tile.rect.x, tile.rect.y, sid, layer_idx, 0))
        for bgo in layer.bgos:
            sid = BGO_SMBX_IDS.get(bgo.bgo_type, 5)
            bgos.append((bgo.rect.x, bgo.rect.y, sid, layer_idx, 0))
        for npc in layer.npcs:
            sid = NPC_SMBX_IDS.get(npc.npc_type, 1)
            npcs.append((npc.rect.x, npc.rect.y, sid, layer_idx, 0))
    with open(filename, 'wb') as f:
        f.write(struct.pack('<III', len(blocks), len(bgos), len(npcs)))
        for x, y, sid, layer, event in blocks:
            f.write(struct.pack('<IIIII', x, y, sid, layer, event))
        for x, y, sid, layer, event in bgos:
            f.write(struct.pack('<IIIII', x, y, sid, layer, event))
        for x, y, sid, layer, event in npcs:
            f.write(struct.pack('<IIIII', x, y, sid, layer, event))

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
        self.current_file = None
        self.selection = []
        self.tool = 'pencil'
        self.clipboard = []
        self.grid_enabled = True
        self.mouse_pos = (0, 0)
        self.tooltip_text = ""
        self.tooltip_timer = 0

    def setup_toolbar(self):
        # (icon_key, callback, tooltip)
        tools = [
            ("select", self.set_tool_select, "Select [S]"),
            ("pencil", self.set_tool_pencil, "Pencil [P]"),
            ("eraser", self.set_tool_erase, "Eraser [E]"),
            ("fill",   self.set_tool_fill,   "Fill [F]"),
            None,  # separator
            ("new",  self.new_level,        "New Level"),
            ("open", self.load_lvl,         "Open Level"),
            ("save", self.save_lvl,         "Save Level"),
            None,  # separator
            ("undo", self.undo,             "Undo [Ctrl+Z]"),
            ("redo", self.redo,             "Redo [Ctrl+Y]"),
            None,  # separator
            ("play",  self.toggle_playtest, "Playtest [T]"),
            ("props", self.show_properties, "Level Properties"),
        ]
        self.toolbar_btns = []
        x = SIDEBAR_WIDTH + 4
        for item in tools:
            if item is None:
                x += 8
                continue
            icon_key, cb, tooltip = item
            self.toolbar_btns.append(ToolbarButton((x, MENU_HEIGHT + 2, 22, 22), icon_key, cb, tooltip))
            x += 24

    def set_tool_select(self): self.tool = 'select'
    def set_tool_pencil(self): self.tool = 'pencil'
    def set_tool_erase(self):  self.tool = 'erase'
    def set_tool_fill(self):   self.tool = 'fill'

    def new_level(self):
        self.level = Level()
        self.camera = Camera(self.level.current_section().width, self.level.current_section().height)
        self.current_file = None
        self.selection.clear()

    def save_lvl(self):
        if not self.current_file:
            self.current_file = "untitled.lvl"
        write_lvl(self.current_file, self.level)
        print(f"Saved to {self.current_file}")

    def load_lvl(self):
        filename = "test.lvl"
        if os.path.exists(filename):
            self.level = read_lvl(filename)
            self.camera = Camera(self.level.current_section().width, self.level.current_section().height)
            self.current_file = filename
            print(f"Loaded {filename}")
        else:
            print("File not found.")

    def show_properties(self):
        print("Level Properties: Not implemented in this demo.")

    def toggle_playtest(self):
        self.playtest_mode = not self.playtest_mode
        if self.playtest_mode:
            self.player = Player(self.level.start_pos[0], self.level.start_pos[1])
            self.camera.update(self.player)
        else:
            self.player = None

    def push_undo(self, action):
        self.undo_stack.append(action)
        self.redo_stack.clear()

    def undo(self):
        if not self.undo_stack:
            return
        action = self.undo_stack.pop()
        action['undo']()
        self.redo_stack.append(action)

    def redo(self):
        if not self.redo_stack:
            return
        action = self.redo_stack.pop()
        action['redo']()
        self.undo_stack.append(action)

    def world_to_grid(self, world_x, world_y):
        gx = (int(world_x) // GRID_SIZE) * GRID_SIZE
        gy = (int(world_y) // GRID_SIZE) * GRID_SIZE
        return gx, gy

    def get_layer_at(self):
        return self.level.current_layer()

    def place_object(self, grid_x, grid_y):
        layer = self.get_layer_at()
        if layer.locked:
            return
        key = (grid_x, grid_y)
        if key in layer.tile_map:
            return
        if self.sidebar.current_category == "NPCs":
            npc = NPC(grid_x, grid_y, self.sidebar.selected_item, layer=layer)
            layer.npcs.add(npc)
            self.push_undo({'undo': lambda l=layer, n=npc: l.npcs.remove(n),
                            'redo': lambda l=layer, n=npc: l.npcs.add(n)})
        elif self.sidebar.current_category == "BGOs":
            bgo = BGO(grid_x, grid_y, self.sidebar.selected_item, layer=layer)
            layer.bgos.add(bgo)
            self.push_undo({'undo': lambda l=layer, b=bgo: l.bgos.remove(b),
                            'redo': lambda l=layer, b=bgo: l.bgos.add(b)})
        else:
            tile = Tile(grid_x, grid_y, self.sidebar.selected_item, layer=layer)
            layer.add_tile(tile)
            self.push_undo({'undo': lambda l=layer, k=key, t=tile: l.remove_tile(t),
                            'redo': lambda l=layer, k=key, t=tile: l.add_tile(t)})

    def erase_object(self, grid_x, grid_y):
        layer = self.get_layer_at()
        if layer.locked:
            return
        key = (grid_x, grid_y)
        if key in layer.tile_map:
            tile = layer.tile_map[key]
            layer.remove_tile(tile)
            self.push_undo({'undo': lambda l=layer, t=tile: l.add_tile(t),
                            'redo': lambda l=layer, k=key: l.remove_tile(l.tile_map[k]) if k in l.tile_map else None})
            return
        for npc in layer.npcs:
            if npc.rect.x == grid_x and npc.rect.y == grid_y:
                layer.npcs.remove(npc)
                self.push_undo({'undo': lambda l=layer, n=npc: l.npcs.add(n),
                                'redo': lambda l=layer, n=npc: l.npcs.remove(n)})
                return
        for bgo in layer.bgos:
            if bgo.rect.x == grid_x and bgo.rect.y == grid_y:
                layer.bgos.remove(bgo)
                self.push_undo({'undo': lambda l=layer, b=bgo: l.bgos.add(b),
                                'redo': lambda l=layer, b=bgo: l.bgos.remove(b)})
                return

    def fill_area(self, start_x, start_y):
        layer = self.get_layer_at()
        if layer.locked:
            return
        target_type = self.sidebar.selected_item
        start_key = (start_x, start_y)
        if start_key in layer.tile_map and layer.tile_map[start_key].tile_type == target_type:
            return
        old_type = layer.tile_map[start_key].tile_type if start_key in layer.tile_map else None
        queue = deque([start_key])
        visited = set()
        new_tiles = []
        while queue:
            x, y = queue.popleft()
            if (x, y) in visited:
                continue
            visited.add((x, y))
            if old_type is None:
                if (x, y) in layer.tile_map:
                    continue
            else:
                if (x, y) not in layer.tile_map or layer.tile_map[(x, y)].tile_type != old_type:
                    continue
            if (x, y) in layer.tile_map:
                old_tile = layer.tile_map[(x, y)]
                layer.remove_tile(old_tile)
            new_tile = Tile(x, y, target_type, layer=layer)
            layer.add_tile(new_tile)
            new_tiles.append(new_tile)
            for dx, dy in [(GRID_SIZE, 0), (-GRID_SIZE, 0), (0, GRID_SIZE), (0, -GRID_SIZE)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.level.current_section().width and 0 <= ny < self.level.current_section().height:
                    queue.append((nx, ny))
        if new_tiles:
            self.push_undo({'undo': lambda l=layer, nt=new_tiles: [l.remove_tile(t) for t in nt],
                            'redo': lambda l=layer, nt=new_tiles: [l.add_tile(t) for t in nt]})

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return False

        for btn in self.toolbar_btns:
            btn.handle_event(event)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.playtest_mode:
                    self.toggle_playtest()
                else:
                    return "MENU"
            if not self.playtest_mode:
                if event.key == pygame.K_EQUALS and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    self.camera.zoom = min(ZOOM_MAX, self.camera.zoom + ZOOM_STEP)
                if event.key == pygame.K_MINUS and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    self.camera.zoom = max(ZOOM_MIN, self.camera.zoom - ZOOM_STEP)
                if event.key == pygame.K_LEFT:
                    self.camera.move(GRID_SIZE, 0)
                if event.key == pygame.K_RIGHT:
                    self.camera.move(-GRID_SIZE, 0)
                if event.key == pygame.K_UP:
                    self.camera.move(0, GRID_SIZE)
                if event.key == pygame.K_DOWN:
                    self.camera.move(0, -GRID_SIZE)
                if event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    self.undo()
                if event.key == pygame.K_y and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    self.redo()
                if event.key == pygame.K_c and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    self.copy_selection()
                if event.key == pygame.K_v and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    self.paste_clipboard()
                if event.key == pygame.K_x and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    self.cut_selection()

        if event.type == pygame.MOUSEMOTION:
            self.mouse_pos = event.pos
            # Update tooltip
            self.tooltip_text = ""
            for btn in self.toolbar_btns:
                if btn.rect.collidepoint(event.pos):
                    self.tooltip_text = btn.tooltip

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.sidebar.rect.collidepoint(event.pos):
                self.sidebar.handle_click(event.pos, self.level)
            elif event.pos[1] > CANVAS_Y and event.pos[0] > SIDEBAR_WIDTH:
                if not self.playtest_mode:
                    world_x = (event.pos[0] - SIDEBAR_WIDTH) / self.camera.zoom - self.camera.camera.x
                    world_y = (event.pos[1] - CANVAS_Y) / self.camera.zoom - self.camera.camera.y
                    grid_x, grid_y = self.world_to_grid(world_x, world_y)
                    if event.button == 1:
                        if self.tool == 'pencil':
                            self.drag_draw = True
                            self.place_object(grid_x, grid_y)
                        elif self.tool == 'erase':
                            self.drag_erase = True
                            self.erase_object(grid_x, grid_y)
                        elif self.tool == 'select':
                            self.handle_select(grid_x, grid_y, event)
                        elif self.tool == 'fill':
                            self.fill_area(grid_x, grid_y)
                    elif event.button == 3:
                        self.drag_erase = True
                        self.erase_object(grid_x, grid_y)

        if event.type == pygame.MOUSEMOTION:
            if not self.playtest_mode and (self.drag_draw or self.drag_erase):
                world_x = (event.pos[0] - SIDEBAR_WIDTH) / self.camera.zoom - self.camera.camera.x
                world_y = (event.pos[1] - CANVAS_Y) / self.camera.zoom - self.camera.camera.y
                grid_x, grid_y = self.world_to_grid(world_x, world_y)
                if self.drag_draw:
                    self.place_object(grid_x, grid_y)
                elif self.drag_erase:
                    self.erase_object(grid_x, grid_y)

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.drag_draw = False
                self.drag_erase = False
            elif event.button == 3:
                self.drag_erase = False

        return True

    def handle_select(self, grid_x, grid_y, event):
        layer = self.get_layer_at()
        obj = None
        if (grid_x, grid_y) in layer.tile_map:
            obj = layer.tile_map[(grid_x, grid_y)]
        else:
            for npc in layer.npcs:
                if npc.rect.x == grid_x and npc.rect.y == grid_y:
                    obj = npc
                    break
            if not obj:
                for bgo in layer.bgos:
                    if bgo.rect.x == grid_x and bgo.rect.y == grid_y:
                        obj = bgo
                        break
        if obj:
            if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                if obj in self.selection:
                    self.selection.remove(obj)
                else:
                    self.selection.append(obj)
            else:
                self.selection = [obj]

    def copy_selection(self):
        self.clipboard = [(obj.rect.x, obj.rect.y, obj.obj_type, obj.layer) for obj in self.selection]

    def cut_selection(self):
        self.copy_selection()
        for obj in self.selection:
            self.delete_object(obj)
        self.selection.clear()

    def paste_clipboard(self):
        if not self.clipboard:
            return
        mouse_world = self.get_mouse_world()
        base_x, base_y = self.world_to_grid(mouse_world[0], mouse_world[1])
        for (x, y, obj_type, layer_idx) in self.clipboard:
            new_x = base_x + (x - self.clipboard[0][0])
            new_y = base_y + (y - self.clipboard[0][1])
            if obj_type in TILE_SMBX_IDS:
                tile = Tile(new_x, new_y, obj_type, layer_idx)
                self.level.current_section().layers[layer_idx].add_tile(tile)
            elif obj_type in BGO_SMBX_IDS:
                bgo = BGO(new_x, new_y, obj_type, layer_idx)
                self.level.current_section().layers[layer_idx].bgos.add(bgo)
            elif obj_type in NPC_SMBX_IDS:
                npc = NPC(new_x, new_y, obj_type, layer_idx)
                self.level.current_section().layers[layer_idx].npcs.add(npc)

    def delete_object(self, obj):
        layer = self.level.current_section().layers[obj.layer]
        if isinstance(obj, Tile):
            layer.remove_tile(obj)
        elif isinstance(obj, BGO):
            layer.bgos.remove(obj)
        elif isinstance(obj, NPC):
            layer.npcs.remove(obj)

    def get_mouse_world(self):
        mx, my = self.mouse_pos
        world_x = (mx - SIDEBAR_WIDTH) / self.camera.zoom - self.camera.camera.x
        world_y = (my - CANVAS_Y) / self.camera.zoom - self.camera.camera.y
        return world_x, world_y

    def update(self):
        if self.playtest_mode:
            section = self.level.current_section()
            solid_tiles = section.get_solid_tiles()
            npcs = pygame.sprite.Group()
            for layer in section.layers:
                if layer.visible:
                    npcs.add(layer.npcs.sprites())
            self.player.update(solid_tiles, npcs)
            for npc in npcs:
                npc.update(solid_tiles, self.player)
            self.camera.update(self.player)

    def draw(self, surf):
        surf.fill(SYS_BTN_FACE)

        # 1. Menu Bar
        pygame.draw.rect(surf, SYS_BTN_FACE, (0, 0, WINDOW_WIDTH, MENU_HEIGHT))
        pygame.draw.line(surf, SYS_BTN_DARK, (0, MENU_HEIGHT-1), (WINDOW_WIDTH, MENU_HEIGHT-1))
        draw_text(surf, "File  Edit  View  Level  Test  Help", (5, 4), SYS_TEXT, FONT_MENU)

        # 2. Toolbar
        pygame.draw.rect(surf, SYS_BTN_FACE, (0, MENU_HEIGHT, WINDOW_WIDTH, TOOLBAR_HEIGHT))
        for btn in self.toolbar_btns:
            btn.draw(surf)

        # Active tool indicator - sunken look
        tool_to_icon = {'select': 0, 'pencil': 1, 'erase': 2, 'fill': 3}
        active_idx = tool_to_icon.get(self.tool, -1)
        if 0 <= active_idx < len(self.toolbar_btns):
            r = self.toolbar_btns[active_idx].rect
            pygame.draw.line(surf, SYS_BTN_DARK, r.topleft, r.topright)
            pygame.draw.line(surf, SYS_BTN_DARK, r.topleft, r.bottomleft)

        # 3. Sidebar
        self.sidebar.draw(surf, self.level)

        # 4. Canvas
        canvas_rect = pygame.Rect(SIDEBAR_WIDTH, CANVAS_Y, CANVAS_WIDTH, CANVAS_HEIGHT)
        pygame.draw.rect(surf, SYS_WINDOW, canvas_rect)
        draw_edge(surf, canvas_rect, raised=False)

        surf.set_clip(canvas_rect)
        bg_color = self.level.current_section().bg_color
        surf.fill(bg_color)

        if self.grid_enabled:
            zoom = self.camera.zoom
            cam = self.camera.camera
            start_col = int(-cam.x // GRID_SIZE)
            end_col = start_col + int(CANVAS_WIDTH // (GRID_SIZE * zoom)) + 2
            start_row = int(-cam.y // GRID_SIZE)
            end_row = start_row + int(CANVAS_HEIGHT // (GRID_SIZE * zoom)) + 2
            for c in range(start_col, end_col):
                x = c * GRID_SIZE + cam.x + SIDEBAR_WIDTH
                if canvas_rect.left < x < canvas_rect.right:
                    pygame.draw.line(surf, SMBX_GRID, (x, canvas_rect.y), (x, canvas_rect.bottom))
            for r in range(start_row, end_row):
                y = r * GRID_SIZE + cam.y + CANVAS_Y
                if canvas_rect.top < y < canvas_rect.bottom:
                    pygame.draw.line(surf, SMBX_GRID, (canvas_rect.x, y), (canvas_rect.right, y))

        section = self.level.current_section()
        for layer in section.layers:
            if not layer.visible:
                continue
            for bgo in layer.bgos:
                pos = bgo.rect.move(self.camera.camera.topleft)
                pos.x += SIDEBAR_WIDTH
                pos.y += CANVAS_Y
                surf.blit(bgo.image, pos)
            for tile in layer.tiles:
                pos = tile.rect.move(self.camera.camera.topleft)
                pos.x += SIDEBAR_WIDTH
                pos.y += CANVAS_Y
                surf.blit(tile.image, pos)
            for npc in layer.npcs:
                pos = npc.rect.move(self.camera.camera.topleft)
                pos.x += SIDEBAR_WIDTH
                pos.y += CANVAS_Y
                surf.blit(npc.image, pos)

        if not self.playtest_mode and self.selection:
            for obj in self.selection:
                pos = obj.rect.move(self.camera.camera.topleft)
                pos.x += SIDEBAR_WIDTH
                pos.y += CANVAS_Y
                pygame.draw.rect(surf, YELLOW, pos, 2)

        if self.playtest_mode and self.player:
            self.player.draw(surf, (self.camera.camera.x + SIDEBAR_WIDTH, self.camera.camera.y + CANVAS_Y))

        surf.set_clip(None)

        # 5. Status Bar
        pygame.draw.rect(surf, SYS_BTN_FACE, (0, WINDOW_HEIGHT - STATUSBAR_HEIGHT, WINDOW_WIDTH, STATUSBAR_HEIGHT))
        pygame.draw.line(surf, SYS_BTN_LIGHT, (0, WINDOW_HEIGHT - STATUSBAR_HEIGHT), (WINDOW_WIDTH, WINDOW_HEIGHT - STATUSBAR_HEIGHT), 1)

        panel_w = 200
        p1 = (2, WINDOW_HEIGHT - STATUSBAR_HEIGHT + 2, panel_w, STATUSBAR_HEIGHT-4)
        pygame.draw.rect(surf, SYS_BTN_FACE, p1)
        draw_edge(surf, p1, raised=False)
        mode_text = f"Mode: {'PLAYTEST' if self.playtest_mode else self.tool.upper()}"
        draw_text(surf, mode_text, (p1[0]+4, p1[1]+2), SYS_TEXT, FONT_SMALL)

        p2 = (panel_w+6, WINDOW_HEIGHT - STATUSBAR_HEIGHT + 2, panel_w, STATUSBAR_HEIGHT-4)
        pygame.draw.rect(surf, SYS_BTN_FACE, p2)
        draw_edge(surf, p2, raised=False)
        layer_name = self.level.current_layer().name
        draw_text(surf, f"Layer: {layer_name}", (p2[0]+4, p2[1]+2), SYS_TEXT, FONT_SMALL)

        p3 = (panel_w*2+10, WINDOW_HEIGHT - STATUSBAR_HEIGHT + 2, panel_w, STATUSBAR_HEIGHT-4)
        pygame.draw.rect(surf, SYS_BTN_FACE, p3)
        draw_edge(surf, p3, raised=False)
        world_x, world_y = self.get_mouse_world()
        grid_x, grid_y = self.world_to_grid(world_x, world_y)
        draw_text(surf, f"X:{int(grid_x)} Y:{int(grid_y)}", (p3[0]+4, p3[1]+2), SYS_TEXT, FONT_SMALL)

        if self.playtest_mode and self.player:
            p4 = (panel_w*3+14, WINDOW_HEIGHT - STATUSBAR_HEIGHT + 2, panel_w, STATUSBAR_HEIGHT-4)
            pygame.draw.rect(surf, SYS_BTN_FACE, p4)
            draw_edge(surf, p4, raised=False)
            draw_text(surf, f"Coins:{self.player.coins} Score:{self.player.score}", (p4[0]+4, p4[1]+2), SYS_TEXT, FONT_SMALL)

        # Tooltip
        if self.tooltip_text:
            tx, ty = self.mouse_pos
            ty -= 18
            tw = FONT_SMALL.size(self.tooltip_text)[0] + 8
            tip_rect = pygame.Rect(tx, ty, tw, 16)
            pygame.draw.rect(surf, (255, 255, 225), tip_rect)
            draw_edge(surf, tip_rect, raised=True)
            draw_text(surf, self.tooltip_text, (tip_rect.x + 4, tip_rect.y + 2), BLACK, FONT_SMALL)

        return surf

# -------------------------
# MAIN MENU
# -------------------------
def main_menu(screen):
    buttons = [
        ClassicButton((WINDOW_WIDTH//2 - 100, 320, 200, 35), "New Level", lambda: "NEW"),
        ClassicButton((WINDOW_WIDTH//2 - 100, 360, 200, 35), "Open Level", lambda: "LOAD"),
        ClassicButton((WINDOW_WIDTH//2 - 100, 400, 200, 35), "Quit", lambda: "QUIT")
    ]
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "QUIT"
            for btn in buttons:
                res = btn.handle_event(event)
                if res:
                    if btn.text == "Open Level":
                        return "LOAD"
                    return btn.callback()

        screen.fill(SYS_BTN_FACE)
        win_rect = (WINDOW_WIDTH//2 - 250, 100, 500, 380)
        pygame.draw.rect(screen, SYS_BTN_FACE, win_rect)
        draw_edge(screen, win_rect, raised=False)

        title_rect = pygame.Rect(win_rect[0], win_rect[1], win_rect[2], 22)
        pygame.draw.rect(screen, SYS_HIGHLIGHT, title_rect)
        draw_text(screen, "Mario Fan Builder - CATSAN [C] AC Holding", (title_rect.x + 3, title_rect.y + 4), WHITE, FONT_SMALL)

        close_rect = pygame.Rect(title_rect.right - 20, title_rect.top + 2, 18, 18)
        pygame.draw.rect(screen, SYS_BTN_FACE, close_rect)
        draw_edge(screen, close_rect, raised=True)
        draw_text(screen, "X", close_rect.center, BLACK, FONT_SMALL, True)

        content_rect = pygame.Rect(win_rect[0]+5, title_rect.bottom+5, win_rect[2]-10, win_rect[3]-27-title_rect.height)
        pygame.draw.rect(screen, SYS_WINDOW, content_rect)

        draw_text(screen, "Welcome to Mario Fan Builder!", (content_rect.centerx, content_rect.y + 40), SYS_HIGHLIGHT, FONT_TITLE, True)
        draw_text(screen, "SMBX 1.3 Engine Recreation", (content_rect.centerx, content_rect.y + 70), SYS_TEXT, FONT, True)

        recent_rect = pygame.Rect(content_rect.x + 20, content_rect.y + 120, content_rect.width - 40, 100)
        pygame.draw.rect(screen, SYS_WINDOW, recent_rect)
        draw_edge(screen, recent_rect, raised=False)
        draw_text(screen, "Recent Files:", (recent_rect.x + 2, recent_rect.y - 15), SYS_TEXT, FONT_SMALL)

        for btn in buttons:
            btn.draw(screen)

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

        if result in ("NEW", "LOAD"):
            level = Level()
            if result == "LOAD":
                if os.path.exists("test.lvl"):
                    level = read_lvl("test.lvl")

            editor = Editor(level)
            running = True
            while running:
                for event in pygame.event.get():
                    res = editor.handle_event(event)
                    if res == "MENU":
                        running = False
                    elif res is False:
                        running = False
                        pygame.quit()
                        sys.exit()

                editor.update()
                editor.draw(screen)
                pygame.display.flip()
                clock.tick(FPS)

if __name__ == "__main__":
    main()
