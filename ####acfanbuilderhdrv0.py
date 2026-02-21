import pygame
import sys
import os
import math
import struct
import random
import json
from collections import deque

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
FPS = 60
ZOOM_MIN, ZOOM_MAX = 0.25, 4.0
ZOOM_STEP = 0.25

SYS_BG         = (212, 208, 200)
SYS_BTN_FACE   = (212, 208, 200)
SYS_BTN_LIGHT  = (255, 255, 255)
SYS_BTN_DARK   = (128, 128, 128)
SYS_BTN_DK_SHD = (64,  64,  64)
SYS_WINDOW     = (255, 255, 255)
SYS_HIGHLIGHT  = (0,   0,   128)
SYS_HIGHLIGHT2 = (51, 153, 255)
SYS_TEXT       = (0,   0,   0)
WHITE  = (255, 255, 255)
BLACK  = (0,   0,   0)
RED    = (255, 0,   0)
GREEN  = (0,   200, 0)
BLUE   = (0,   0,   255)
YELLOW = (255, 255, 0)
GRAY   = (128, 128, 128)
SMBX_GRID = (40, 40, 40)

GRAVITY           = 0.5
JUMP_STRENGTH     = -10
MOVE_SPEED        = 4
TERMINAL_VELOCITY = 10

pygame.init()
pygame.display.set_caption("Mario Fan Builder - CATSAN [C] AC Holding")

FONT       = pygame.font.Font(None, 20)
FONT_MENU  = pygame.font.Font(None, 20)
FONT_SMALL = pygame.font.Font(None, 16)
FONT_TITLE = pygame.font.Font(None, 28)

# -------------------------
# SMBX ID MAPPINGS
# -------------------------
TILE_SMBX_IDS = {
    'ground':1,'grass':2,'sand':3,'dirt':4,
    'brick':45,'question':34,'pipe_vertical':112,'pipe_horizontal':113,
    'platform':159,'coin':10,'bridge':47,
    'stone':48,'ice':55,'mushroom_platform':91,'pswitch':60,
}
BGO_SMBX_IDS  = {'cloud':5,'bush':6,'hill':7,'fence':8,'bush_3':9,'tree':10,'castle':11,'waterfall':12,'sign':13}
NPC_SMBX_IDS  = {
    'goomba':1,'koopa_green':2,'koopa_red':3,'paratroopa_green':4,
    'paratroopa_red':5,'piranha':6,'hammer_bro':7,'lakitu':8,
    'mushroom':9,'flower':10,'star':11,'1up':12,
    'buzzy':13,'spiny':14,'cheep':15,'blooper':16,'thwomp':17,'bowser':18,'boo':19,
}
TILE_ID_TO_NAME = {v:k for k,v in TILE_SMBX_IDS.items()}
BGO_ID_TO_NAME  = {v:k for k,v in BGO_SMBX_IDS.items()}
NPC_ID_TO_NAME  = {v:k for k,v in NPC_SMBX_IDS.items()}

# -------------------------
# THEMES
# -------------------------
themes = {
    'SMB1': {
        'background':(92,148,252),'ground':(0,128,0),'brick':(180,80,40),
        'question':(255,200,0),'coin':(255,255,0),'pipe_vertical':(0,200,0),
        'pipe_horizontal':(0,180,0),'platform':(139,69,19),'goomba':(200,100,0),
        'koopa_green':(0,200,50),'koopa_red':(200,50,50),'mushroom':(255,0,200),
        'flower':(255,140,0),'star':(255,230,0),'bgo_cloud':(220,220,220),
        'bgo_bush':(0,160,0),'bgo_hill':(100,200,100),'bgo_tree':(0,120,0),
        'grass':(60,180,60),'sand':(220,200,100),'dirt':(150,100,60),
        'stone':(140,140,140),'ice':(160,220,255),'bridge':(160,100,40),
        'mushroom_platform':(200,100,200),'pswitch':(80,80,200),
    },
    'SMB3': {
        'background':(0,0,0),'ground':(160,120,80),'brick':(180,100,60),
        'question':(255,210,0),'coin':(255,255,100),'pipe_vertical':(0,180,0),
        'pipe_horizontal':(0,160,0),'platform':(100,100,100),'goomba':(255,50,50),
        'koopa_green':(0,200,0),'koopa_red':(200,0,0),'mushroom':(255,100,200),
        'flower':(255,150,0),'star':(255,255,0),'bgo_cloud':(150,150,150),
        'bgo_bush':(0,100,0),'bgo_hill':(80,160,80),'bgo_tree':(0,80,0),
        'grass':(130,100,60),'sand':(200,170,80),'dirt':(120,80,40),
        'stone':(110,110,110),'ice':(130,190,230),'bridge':(130,80,30),
        'mushroom_platform':(170,80,170),'pswitch':(60,60,170),
    },
    'SMW': {
        'background':(110,200,255),'ground':(200,160,100),'brick':(210,120,70),
        'question':(255,220,0),'coin':(255,240,0),'pipe_vertical':(0,220,80),
        'pipe_horizontal':(0,200,70),'platform':(180,130,70),'goomba':(210,120,0),
        'koopa_green':(0,220,80),'koopa_red':(220,60,60),'mushroom':(255,50,200),
        'flower':(255,160,0),'star':(255,240,0),'bgo_cloud':(240,240,240),
        'bgo_bush':(0,200,80),'bgo_hill':(120,220,120),'bgo_tree':(0,160,60),
        'grass':(80,200,80),'sand':(230,210,120),'dirt':(170,120,70),
        'stone':(160,160,160),'ice':(180,230,255),'bridge':(180,120,50),
        'mushroom_platform':(220,120,220),'pswitch':(100,100,220),
    }
}
current_theme = 'SMB1'

BG_PRESETS = {
    'SMB1 Sky':(92,148,252), 'Night':(0,0,40), 'Underground':(0,0,0),
    'Sunset':(255,140,60),   'Cave':(30,20,10),'Water':(0,80,160),
}

# -------------------------
# HELPERS
# -------------------------
def draw_edge(surf, rect, raised=True):
    r = pygame.Rect(rect)
    tl  = SYS_BTN_LIGHT  if raised else SYS_BTN_DK_SHD
    br  = SYS_BTN_DK_SHD if raised else SYS_BTN_LIGHT
    tli = SYS_BTN_FACE    if raised else SYS_BTN_DARK
    bri = SYS_BTN_DARK    if raised else SYS_BTN_FACE
    pygame.draw.line(surf, tl,  r.topleft,    r.topright)
    pygame.draw.line(surf, tl,  r.topleft,    r.bottomleft)
    pygame.draw.line(surf, br,  r.bottomleft, r.bottomright)
    pygame.draw.line(surf, br,  r.topright,   r.bottomright)
    pygame.draw.line(surf, tli, (r.left+1,r.top+1),    (r.right-1,r.top+1))
    pygame.draw.line(surf, tli, (r.left+1,r.top+1),    (r.left+1,r.bottom-1))
    pygame.draw.line(surf, bri, (r.left+1,r.bottom-1), (r.right-1,r.bottom-1))
    pygame.draw.line(surf, bri, (r.right-1,r.top+1),   (r.right-1,r.bottom-1))

def draw_text(surf, text, pos, color=SYS_TEXT, font=FONT, center=False):
    t = font.render(text, True, color)
    r = t.get_rect(center=pos) if center else t.get_rect(topleft=pos)
    surf.blit(t, r)

def get_theme_color(name):
    return themes[current_theme].get(name, (128,128,128))

# -------------------------
# ICON DRAWING
# -------------------------
def draw_icon_select(surf, rect, color=SYS_TEXT):
    r = rect.inflate(-6,-6)
    for i in range(0, r.width, 4):
        if (i//4)%2==0:
            pygame.draw.line(surf,color,(r.x+i,r.y),(min(r.x+i+3,r.right),r.y))
            pygame.draw.line(surf,color,(r.x+i,r.bottom),(min(r.x+i+3,r.right),r.bottom))
    for i in range(0, r.height, 4):
        if (i//4)%2==0:
            pygame.draw.line(surf,color,(r.x,r.y+i),(r.x,min(r.y+i+3,r.bottom)))
            pygame.draw.line(surf,color,(r.right,r.y+i),(r.right,min(r.y+i+3,r.bottom)))

def draw_icon_pencil(surf, rect, color=SYS_TEXT):
    cx,cy=rect.center
    pts=[(cx-1,cy+6),(cx+5,cy-3),(cx+3,cy-5),(cx-3,cy+4)]
    pygame.draw.polygon(surf,color,pts,1)
    pygame.draw.line(surf,color,(cx-1,cy+6),(cx-4,cy+8))
    pygame.draw.line(surf,color,(cx-4,cy+8),(cx-2,cy+5))

def draw_icon_eraser(surf, rect, color=SYS_TEXT):
    r=rect.inflate(-8,-8)
    pygame.draw.rect(surf,color,(r.x,r.centery-3,r.width,7),1)
    pygame.draw.line(surf,color,(r.x+r.width//2,r.centery-3),(r.x+r.width//2,r.centery+4))

def draw_icon_fill(surf, rect, color=SYS_TEXT):
    cx,cy=rect.center
    pygame.draw.rect(surf,color,(cx-5,cy-4,8,8),1)
    pygame.draw.rect(surf,color,(cx-4,cy-3,6,6))
    pygame.draw.circle(surf,color,(cx+5,cy+4),2)

def draw_icon_new(surf, rect, color=SYS_TEXT):
    r=rect.inflate(-8,-6); fold=5
    pts=[(r.x,r.y),(r.right-fold,r.y),(r.right,r.y+fold),(r.right,r.bottom),(r.x,r.bottom)]
    pygame.draw.polygon(surf,color,pts,1)
    pygame.draw.line(surf,color,(r.right-fold,r.y),(r.right-fold,r.y+fold))
    pygame.draw.line(surf,color,(r.right-fold,r.y+fold),(r.right,r.y+fold))

def draw_icon_open(surf, rect, color=SYS_TEXT):
    cx,cy=rect.center
    pygame.draw.rect(surf,color,(cx-7,cy-2,14,9),1)
    pygame.draw.rect(surf,color,(cx-7,cy-5,6,4),1)

def draw_icon_save(surf, rect, color=SYS_TEXT):
    r=rect.inflate(-8,-6)
    pygame.draw.rect(surf,color,r,1)
    pygame.draw.rect(surf,SYS_BTN_FACE,(r.x+2,r.y+2,r.width-4,r.height//2-2))
    pygame.draw.rect(surf,color,(r.x+5,r.y+2,r.width-10,r.height//2-2),1)
    pygame.draw.rect(surf,color,(r.x+r.width//3,r.bottom-5,r.width//3,5))

def draw_icon_undo(surf, rect, color=SYS_TEXT):
    cx,cy=rect.center
    pygame.draw.arc(surf,color,(cx-6,cy-4,12,10),math.pi*0.3,math.pi*1.1,2)
    pygame.draw.polygon(surf,color,[(cx-6,cy-4),(cx-9,cy),(cx-3,cy-1)])

def draw_icon_redo(surf, rect, color=SYS_TEXT):
    cx,cy=rect.center
    pygame.draw.arc(surf,color,(cx-6,cy-4,12,10),math.pi*1.9,math.pi*0.7+math.pi*2,2)
    pygame.draw.polygon(surf,color,[(cx+6,cy-4),(cx+9,cy),(cx+3,cy-1)])

def draw_icon_play(surf, rect, color=SYS_TEXT):
    cx,cy=rect.center
    pygame.draw.polygon(surf,color,[(cx-4,cy-6),(cx-4,cy+6),(cx+6,cy)])

def draw_icon_props(surf, rect, color=SYS_TEXT):
    cx,cy=rect.center
    draw_text(surf,"i",(cx,cy),color,FONT_SMALL,True)
    pygame.draw.circle(surf,color,(cx,cy-5),2)

def draw_icon_grid(surf, rect, color=SYS_TEXT):
    r=rect.inflate(-6,-6)
    for i in range(0,r.width+1,r.width//2):
        pygame.draw.line(surf,color,(r.x+i,r.y),(r.x+i,r.bottom))
    for i in range(0,r.height+1,r.height//2):
        pygame.draw.line(surf,color,(r.x,r.y+i),(r.right,r.y+i))

def draw_icon_zoom_in(surf, rect, color=SYS_TEXT):
    cx,cy=rect.center
    pygame.draw.circle(surf,color,(cx-2,cy-2),5,1)
    pygame.draw.line(surf,color,(cx+2,cy+2),(cx+6,cy+6),2)
    pygame.draw.line(surf,color,(cx-4,cy-2),(cx,cy-2),1)
    pygame.draw.line(surf,color,(cx-2,cy-4),(cx-2,cy),1)

def draw_icon_zoom_out(surf, rect, color=SYS_TEXT):
    cx,cy=rect.center
    pygame.draw.circle(surf,color,(cx-2,cy-2),5,1)
    pygame.draw.line(surf,color,(cx+2,cy+2),(cx+6,cy+6),2)
    pygame.draw.line(surf,color,(cx-4,cy-2),(cx,cy-2),1)

def draw_icon_layer(surf, rect, color=SYS_TEXT):
    r=rect.inflate(-6,-6)
    for i in range(3):
        y=r.y+i*4
        pygame.draw.rect(surf,color,(r.x,y,r.width,4),1)

ICON_FNS = {
    'select':draw_icon_select,'pencil':draw_icon_pencil,'eraser':draw_icon_eraser,
    'fill':draw_icon_fill,'new':draw_icon_new,'open':draw_icon_open,'save':draw_icon_save,
    'undo':draw_icon_undo,'redo':draw_icon_redo,'play':draw_icon_play,'props':draw_icon_props,
    'grid':draw_icon_grid,'zoom_in':draw_icon_zoom_in,'zoom_out':draw_icon_zoom_out,
    'layer':draw_icon_layer,
}

# -------------------------
# DIALOG HELPERS
# -------------------------
class Dialog:
    """Base blocking modal dialog."""
    def __init__(self, screen, title, w, h):
        self.screen = screen
        self.title  = title
        self.w, self.h = w, h
        self.x = (WINDOW_WIDTH - w)  // 2
        self.y = (WINDOW_HEIGHT - h) // 2
        self.rect = pygame.Rect(self.x, self.y, w, h)
        self.done = False
        self.result = None
        self._overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        self._overlay.fill((0,0,0,100))

    def _draw_frame(self):
        self.screen.blit(self._overlay,(0,0))
        pygame.draw.rect(self.screen, SYS_BTN_FACE, self.rect)
        draw_edge(self.screen, self.rect, raised=True)
        title_r = pygame.Rect(self.x+2, self.y+2, self.w-4, 20)
        pygame.draw.rect(self.screen, SYS_HIGHLIGHT, title_r)
        draw_text(self.screen, self.title, (title_r.x+4, title_r.y+3), WHITE, FONT_SMALL)
        # X button
        xr = pygame.Rect(title_r.right-18, title_r.y+1, 16, 16)
        pygame.draw.rect(self.screen, SYS_BTN_FACE, xr)
        draw_edge(self.screen, xr, raised=True)
        draw_text(self.screen, "X", xr.center, BLACK, FONT_SMALL, True)
        return title_r, xr

    def _btn(self, label, bx, by, bw=80, bh=22):
        r = pygame.Rect(self.x+bx, self.y+by, bw, bh)
        pygame.draw.rect(self.screen, SYS_BTN_FACE, r)
        draw_edge(self.screen, r, raised=True)
        draw_text(self.screen, label, r.center, SYS_TEXT, FONT_SMALL, True)
        return r

    def run(self):
        clock = pygame.time.Clock()
        while not self.done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.done=True; self.result=None
                self.handle_event(event)
            self.draw()
            pygame.display.flip()
            clock.tick(60)
        return self.result

    def handle_event(self, event): pass
    def draw(self): self._draw_frame()


class MessageBox(Dialog):
    """Simple OK/Cancel message box."""
    def __init__(self, screen, title, message, buttons=("OK",)):
        lines = message.split('\n')
        w = max(300, max(FONT_SMALL.size(l)[0] for l in lines)+60)
        h = 80 + len(lines)*18 + 40
        super().__init__(screen, title, w, h)
        self.message = message
        self.buttons = buttons

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button==1:
            lines = self.message.split('\n')
            by = self.h - 40
            bw = 70; gap = 10
            total = len(self.buttons)*(bw+gap)-gap
            bstart = (self.w - total)//2
            for i,b in enumerate(self.buttons):
                r = pygame.Rect(self.x+bstart+i*(bw+gap), self.y+by, bw, 24)
                if r.collidepoint(event.pos):
                    self.result=b; self.done=True

    def draw(self):
        _, xr = self._draw_frame()
        lines = self.message.split('\n')
        for i,l in enumerate(lines):
            draw_text(self.screen, l, (self.x+20, self.y+34+i*18), SYS_TEXT, FONT_SMALL)
        by=self.h-40; bw=70; gap=10
        total=len(self.buttons)*(bw+gap)-gap
        bstart=(self.w-total)//2
        for i,b in enumerate(self.buttons):
            r=pygame.Rect(self.x+bstart+i*(bw+gap),self.y+by,bw,24)
            pygame.draw.rect(self.screen,SYS_BTN_FACE,r)
            draw_edge(self.screen,r,raised=True)
            draw_text(self.screen,b,r.center,SYS_TEXT,FONT_SMALL,True)


class InputDialog(Dialog):
    """Single-line text input dialog."""
    def __init__(self, screen, title, prompt, default=""):
        super().__init__(screen, title, 340, 120)
        self.prompt  = prompt
        self.value   = default
        self.cursor  = len(default)
        self.active  = True

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.result=self.value; self.done=True
            elif event.key == pygame.K_ESCAPE:
                self.done=True
            elif event.key == pygame.K_BACKSPACE:
                if self.cursor>0:
                    self.value=self.value[:self.cursor-1]+self.value[self.cursor:]
                    self.cursor-=1
            elif event.key == pygame.K_DELETE:
                self.value=self.value[:self.cursor]+self.value[self.cursor+1:]
            elif event.key == pygame.K_LEFT:
                self.cursor=max(0,self.cursor-1)
            elif event.key == pygame.K_RIGHT:
                self.cursor=min(len(self.value),self.cursor+1)
            else:
                ch=event.unicode
                if ch and ch.isprintable():
                    self.value=self.value[:self.cursor]+ch+self.value[self.cursor:]
                    self.cursor+=1
        if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
            ok=pygame.Rect(self.x+self.w-170,self.y+86,70,24)
            cn=pygame.Rect(self.x+self.w-90, self.y+86,70,24)
            if ok.collidepoint(event.pos): self.result=self.value; self.done=True
            if cn.collidepoint(event.pos): self.done=True

    def draw(self):
        self._draw_frame()
        draw_text(self.screen, self.prompt, (self.x+14,self.y+34), SYS_TEXT, FONT_SMALL)
        ir=pygame.Rect(self.x+14,self.y+52,self.w-28,22)
        pygame.draw.rect(self.screen,SYS_WINDOW,ir)
        draw_edge(self.screen,ir,raised=False)
        draw_text(self.screen,self.value,(ir.x+4,ir.y+4),SYS_TEXT,FONT_SMALL)
        # Cursor blink
        if pygame.time.get_ticks()%1000<500:
            cx=ir.x+4+FONT_SMALL.size(self.value[:self.cursor])[0]
            pygame.draw.line(self.screen,BLACK,(cx,ir.y+3),(cx,ir.y+18),1)
        for i,(lbl,bx) in enumerate([("OK",self.w-170),("Cancel",self.w-90)]):
            r=pygame.Rect(self.x+bx,self.y+86,70,24)
            pygame.draw.rect(self.screen,SYS_BTN_FACE,r)
            draw_edge(self.screen,r,raised=True)
            draw_text(self.screen,lbl,r.center,SYS_TEXT,FONT_SMALL,True)


class PropertiesDialog(Dialog):
    """Level properties editor."""
    def __init__(self, screen, level):
        super().__init__(screen, "Level Properties", 400, 320)
        self.level   = level
        self.section = level.current_section()
        self.fields  = {
            'name':   level.name,
            'author': level.author,
            'width':  str(self.section.width // GRID_SIZE),
            'height': str(self.section.height // GRID_SIZE),
        }
        self.active_field = None
        self.cursors = {k:len(v) for k,v in self.fields.items()}
        self.bg_selected = None
        self.theme_sel   = current_theme

    def _field_rect(self, fy):
        return pygame.Rect(self.x+160, self.y+fy, 210, 20)

    def handle_event(self, event):
        labels = [('name','Level Name:',50),('author','Author:',76),
                  ('width','Width (tiles):',102),('height','Height (tiles):',128)]
        if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
            self.active_field=None
            for key,_,fy in labels:
                if self._field_rect(fy).collidepoint(event.pos):
                    self.active_field=key
            # BG colour buttons
            bgs=list(BG_PRESETS.items())
            for i,(name,col) in enumerate(bgs):
                r=pygame.Rect(self.x+10+i*62,self.y+180,58,18)
                if r.collidepoint(event.pos):
                    self.section.bg_color=col
            # Theme buttons
            th_names=list(themes.keys())
            for i,tn in enumerate(th_names):
                r=pygame.Rect(self.x+10+i*90,self.y+230,84,20)
                if r.collidepoint(event.pos):
                    self.theme_sel=tn
            # OK / Cancel
            ok=pygame.Rect(self.x+self.w-170,self.y+self.h-40,70,26)
            cn=pygame.Rect(self.x+self.w-90, self.y+self.h-40,70,26)
            if ok.collidepoint(event.pos):
                self._apply(); self.result='ok'; self.done=True
            if cn.collidepoint(event.pos):
                self.done=True

        if event.type==pygame.KEYDOWN and self.active_field:
            k=self.active_field
            v=self.fields[k]; c=self.cursors[k]
            if event.key==pygame.K_RETURN: self.active_field=None
            elif event.key==pygame.K_BACKSPACE and c>0:
                self.fields[k]=v[:c-1]+v[c:]; self.cursors[k]=c-1
            elif event.key==pygame.K_LEFT: self.cursors[k]=max(0,c-1)
            elif event.key==pygame.K_RIGHT: self.cursors[k]=min(len(v),c+1)
            elif event.unicode and event.unicode.isprintable():
                self.fields[k]=v[:c]+event.unicode+v[c:]; self.cursors[k]=c+1

    def _apply(self):
        global current_theme
        self.level.name   = self.fields['name']
        self.level.author = self.fields['author']
        try:
            nw=max(20,int(self.fields['width']))
            nh=max(10,int(self.fields['height']))
            self.section.width  = nw*GRID_SIZE
            self.section.height = nh*GRID_SIZE
        except: pass
        current_theme = self.theme_sel

    def draw(self):
        self._draw_frame()
        labels=[('name','Level Name:',50),('author','Author:',76),
                ('width','Width (tiles):',102),('height','Height (tiles):',128)]
        for key,lbl,fy in labels:
            draw_text(self.screen,lbl,(self.x+14,self.y+fy+2),SYS_TEXT,FONT_SMALL)
            ir=self._field_rect(fy)
            pygame.draw.rect(self.screen,SYS_WINDOW,ir)
            draw_edge(self.screen,ir,raised=False)
            v=self.fields[key]
            draw_text(self.screen,v,(ir.x+4,ir.y+3),SYS_TEXT,FONT_SMALL)
            if self.active_field==key and pygame.time.get_ticks()%1000<500:
                cx=ir.x+4+FONT_SMALL.size(v[:self.cursors[key]])[0]
                pygame.draw.line(self.screen,BLACK,(cx,ir.y+2),(cx,ir.y+17))

        draw_text(self.screen,"Background:",(self.x+14,self.y+162),SYS_TEXT,FONT_SMALL)
        bgs=list(BG_PRESETS.items())
        for i,(name,col) in enumerate(bgs):
            r=pygame.Rect(self.x+10+i*62,self.y+178,58,18)
            pygame.draw.rect(self.screen,col,r)
            draw_edge(self.screen,r,raised=self.section.bg_color!=col)
            draw_text(self.screen,name[:7],(r.x+2,r.y+3),(255,255,255) if sum(col)<300 else BLACK,FONT_SMALL)

        draw_text(self.screen,"Theme:",(self.x+14,self.y+214),SYS_TEXT,FONT_SMALL)
        for i,tn in enumerate(themes.keys()):
            r=pygame.Rect(self.x+10+i*90,self.y+228,84,20)
            sel=(tn==self.theme_sel)
            pygame.draw.rect(self.screen,SYS_HIGHLIGHT if sel else SYS_BTN_FACE,r)
            draw_edge(self.screen,r,raised=not sel)
            draw_text(self.screen,tn,r.center,WHITE if sel else SYS_TEXT,FONT_SMALL,True)

        for i,(lbl,bx) in enumerate([("OK",self.w-170),("Cancel",self.w-90)]):
            r=pygame.Rect(self.x+bx,self.y+self.h-40,70,26)
            pygame.draw.rect(self.screen,SYS_BTN_FACE,r)
            draw_edge(self.screen,r,raised=True)
            draw_text(self.screen,lbl,r.center,SYS_TEXT,FONT_SMALL,True)


class LayerDialog(Dialog):
    """Add / rename / delete layers."""
    def __init__(self, screen, section):
        super().__init__(screen, "Layer Manager", 320, 280)
        self.section=section
        self.sel=section.current_layer_idx
        self.new_name=section.layers[self.sel].name if section.layers else ""
        self.cursor=len(self.new_name)

    def handle_event(self,event):
        if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
            # List
            for i,layer in enumerate(self.section.layers):
                r=pygame.Rect(self.x+10,self.y+36+i*22,self.w-20,20)
                if r.collidepoint(event.pos):
                    self.sel=i
                    self.new_name=layer.name
                    self.cursor=len(self.new_name)
            # Buttons
            add_r=pygame.Rect(self.x+10,     self.y+self.h-80,90,24)
            del_r=pygame.Rect(self.x+110,    self.y+self.h-80,90,24)
            ren_r=pygame.Rect(self.x+210,    self.y+self.h-80,90,24)
            ok_r =pygame.Rect(self.x+self.w-170,self.y+self.h-44,70,26)
            cl_r =pygame.Rect(self.x+self.w-90, self.y+self.h-44,70,26)
            if add_r.collidepoint(event.pos):
                self.section.layers.append(Layer(f"Layer {len(self.section.layers)+1}"))
            if del_r.collidepoint(event.pos) and len(self.section.layers)>1:
                self.section.layers.pop(self.sel)
                self.sel=max(0,self.sel-1)
                self.section.current_layer_idx=self.sel
            if ren_r.collidepoint(event.pos) and self.section.layers:
                self.section.layers[self.sel].name=self.new_name
            if ok_r.collidepoint(event.pos):
                self.section.current_layer_idx=self.sel; self.result='ok'; self.done=True
            if cl_r.collidepoint(event.pos):
                self.done=True

        if event.type==pygame.KEYDOWN:
            v=self.new_name; c=self.cursor
            if event.key==pygame.K_BACKSPACE and c>0:
                self.new_name=v[:c-1]+v[c:]; self.cursor=c-1
            elif event.key==pygame.K_LEFT: self.cursor=max(0,c-1)
            elif event.key==pygame.K_RIGHT: self.cursor=min(len(v),c+1)
            elif event.unicode and event.unicode.isprintable():
                self.new_name=v[:c]+event.unicode+v[c:]; self.cursor=c+1

    def draw(self):
        self._draw_frame()
        draw_text(self.screen,"Layers:",(self.x+14,self.y+24),SYS_TEXT,FONT_SMALL)
        for i,layer in enumerate(self.section.layers):
            r=pygame.Rect(self.x+10,self.y+36+i*22,self.w-20,20)
            bg=SYS_HIGHLIGHT if i==self.sel else SYS_WINDOW
            pygame.draw.rect(self.screen,bg,r)
            draw_edge(self.screen,r,raised=False)
            draw_text(self.screen,layer.name,(r.x+4,r.y+3),WHITE if i==self.sel else SYS_TEXT,FONT_SMALL)
            eye=GREEN if layer.visible else GRAY
            pygame.draw.circle(self.screen,eye,(r.right-10,r.centery),4)

        draw_text(self.screen,"Name:",(self.x+10,self.y+self.h-108),SYS_TEXT,FONT_SMALL)
        ir=pygame.Rect(self.x+56,self.y+self.h-110,self.w-70,20)
        pygame.draw.rect(self.screen,SYS_WINDOW,ir)
        draw_edge(self.screen,ir,raised=False)
        draw_text(self.screen,self.new_name,(ir.x+4,ir.y+3),SYS_TEXT,FONT_SMALL)
        if pygame.time.get_ticks()%1000<500:
            cx=ir.x+4+FONT_SMALL.size(self.new_name[:self.cursor])[0]
            pygame.draw.line(self.screen,BLACK,(cx,ir.y+2),(cx,ir.y+16))

        for lbl,bx,bw in [("Add",10,90),("Delete",110,90),("Rename",210,90)]:
            r=pygame.Rect(self.x+bx,self.y+self.h-80,bw,24)
            pygame.draw.rect(self.screen,SYS_BTN_FACE,r)
            draw_edge(self.screen,r,raised=True)
            draw_text(self.screen,lbl,r.center,SYS_TEXT,FONT_SMALL,True)
        for lbl,bx in [("OK",self.w-170),("Close",self.w-90)]:
            r=pygame.Rect(self.x+bx,self.y+self.h-44,70,26)
            pygame.draw.rect(self.screen,SYS_BTN_FACE,r)
            draw_edge(self.screen,r,raised=True)
            draw_text(self.screen,lbl,r.center,SYS_TEXT,FONT_SMALL,True)


# -------------------------
# SPRITE CLASSES
# -------------------------
class GameObject(pygame.sprite.Sprite):
    def __init__(self,x,y,obj_type,layer=0):
        super().__init__()
        self.rect=pygame.Rect(x,y,GRID_SIZE,GRID_SIZE)
        self.layer=layer; self.obj_type=obj_type

class Tile(GameObject):
    def __init__(self,x,y,tile_type,layer=0):
        super().__init__(x,y,tile_type,layer)
        self.tile_type=tile_type
        self.is_solid=tile_type not in ['coin']
        self.update_image()

    def update_image(self):
        self.image=pygame.Surface((GRID_SIZE,GRID_SIZE))
        self.image.fill(get_theme_color(self.tile_type))
        if self.tile_type=='question':
            draw_text(self.image,'?',(GRID_SIZE//2,GRID_SIZE//2),BLACK,FONT_SMALL,True)
        elif self.tile_type=='brick':
            pygame.draw.line(self.image,BLACK,(0,GRID_SIZE//2),(GRID_SIZE,GRID_SIZE//2),2)
            pygame.draw.line(self.image,BLACK,(GRID_SIZE//2,0),(GRID_SIZE//2,GRID_SIZE),2)
        elif self.tile_type=='coin':
            pygame.draw.circle(self.image,YELLOW,(GRID_SIZE//2,GRID_SIZE//2),GRID_SIZE//3)
        elif self.tile_type=='pipe_vertical':
            pygame.draw.rect(self.image,(0,160,0),(4,0,GRID_SIZE-8,GRID_SIZE))
            pygame.draw.rect(self.image,(0,200,0),(2,0,GRID_SIZE-4,8))
        elif self.tile_type=='pipe_horizontal':
            pygame.draw.rect(self.image,(0,160,0),(0,4,GRID_SIZE,GRID_SIZE-8))
            pygame.draw.rect(self.image,(0,200,0),(0,2,8,GRID_SIZE-4))
        pygame.draw.rect(self.image,(0,0,0,60),self.image.get_rect(),1)

class BGO(GameObject):
    def __init__(self,x,y,bgo_type,layer=0):
        super().__init__(x,y,bgo_type,layer)
        self.bgo_type=bgo_type; self.update_image()

    def update_image(self):
        self.image=pygame.Surface((GRID_SIZE,GRID_SIZE),pygame.SRCALPHA)
        color=get_theme_color('bgo_'+self.bgo_type) if not self.bgo_type.startswith('bgo_') else get_theme_color(self.bgo_type)
        pygame.draw.rect(self.image,color,self.image.get_rect().inflate(-4,-4))
        pygame.draw.rect(self.image,(*color[:3],180),self.image.get_rect(),2)

class NPC(GameObject):
    def __init__(self,x,y,npc_type,layer=0):
        super().__init__(x,y,npc_type,layer)
        self.npc_type=npc_type
        self.velocity=pygame.Vector2(random.choice([-1,1]),0)
        self.state='normal'; self.frame=0; self.update_image()

    def update_image(self):
        self.image=pygame.Surface((GRID_SIZE,GRID_SIZE),pygame.SRCALPHA)
        color=get_theme_color(self.npc_type)
        if self.npc_type=='goomba':
            pygame.draw.ellipse(self.image,color,(4,4,GRID_SIZE-8,GRID_SIZE-4))
            pygame.draw.rect(self.image,color,(0,GRID_SIZE-8,GRID_SIZE,8))
        elif self.npc_type.startswith('koopa'):
            pygame.draw.rect(self.image,color,(4,4,GRID_SIZE-8,GRID_SIZE-4))
            if self.state=='shell':
                pygame.draw.circle(self.image,(200,100,0),(GRID_SIZE//2,GRID_SIZE//2),GRID_SIZE//3)
        elif self.npc_type=='mushroom':
            pygame.draw.ellipse(self.image,color,(4,4,GRID_SIZE-8,GRID_SIZE-8))
            pygame.draw.rect(self.image,(200,200,200),(6,GRID_SIZE-10,GRID_SIZE-12,8))
        else:
            pygame.draw.rect(self.image,color,(4,4,GRID_SIZE-8,GRID_SIZE-4))

    def update(self,solid_tiles,player=None):
        self.velocity.y+=GRAVITY
        self.velocity.y=min(self.velocity.y,TERMINAL_VELOCITY)
        self.rect.x+=self.velocity.x; self._collide(solid_tiles,'x')
        self.rect.y+=self.velocity.y; self._collide(solid_tiles,'y')

    def _collide(self,tiles,axis):
        for t in tiles:
            if self.rect.colliderect(t.rect):
                if axis=='x':
                    self.rect.right=t.rect.left if self.velocity.x>0 else t.rect.right
                    if self.velocity.x > 0: self.rect.right=t.rect.left
                    else: self.rect.left=t.rect.right
                    self.velocity.x*=-1
                elif axis=='y':
                    if self.velocity.y>0: self.rect.bottom=t.rect.top
                    else: self.rect.top=t.rect.bottom
                    self.velocity.y=0

class Player(pygame.sprite.Sprite):
    def __init__(self,x,y):
        super().__init__()
        self.rect=pygame.Rect(x,y,GRID_SIZE,GRID_SIZE)
        self.image=pygame.Surface((GRID_SIZE,GRID_SIZE)); self.image.fill(RED)
        self.velocity=pygame.Vector2(0,0)
        self.on_ground=False; self.powerup_state=0
        self.invincible=0; self.coins=0; self.score=0

    def update(self,solid_tiles,npc_group):
        keys=pygame.key.get_pressed()
        self.velocity.x=0
        if keys[pygame.K_LEFT]:  self.velocity.x=-MOVE_SPEED
        if keys[pygame.K_RIGHT]: self.velocity.x= MOVE_SPEED
        if keys[pygame.K_SPACE] and self.on_ground:
            self.velocity.y=JUMP_STRENGTH; self.on_ground=False
        self.velocity.y=min(self.velocity.y+GRAVITY,TERMINAL_VELOCITY)
        self.rect.x+=self.velocity.x; self._collide(solid_tiles,'x')
        self.rect.y+=self.velocity.y; self.on_ground=False; self._collide(solid_tiles,'y')
        for npc in pygame.sprite.spritecollide(self,npc_group,False):
            if self.velocity.y>0 and self.rect.bottom<=npc.rect.centery:
                npc.kill(); self.velocity.y=JUMP_STRENGTH*0.7; self.score+=100
            elif self.invincible<=0:
                if self.powerup_state>0:
                    self.powerup_state=0; self.invincible=120
                else:
                    self.rect.topleft=(100,500); self.score=0; self.coins=0
        if self.invincible>0: self.invincible-=1

    def _collide(self,tiles,axis):
        for t in tiles:
            if self.rect.colliderect(t.rect):
                if axis=='x':
                    if self.velocity.x>0: self.rect.right=t.rect.left
                    else: self.rect.left=t.rect.right
                    self.velocity.x=0
                elif axis=='y':
                    if self.velocity.y>0: self.rect.bottom=t.rect.top; self.on_ground=True
                    else: self.rect.top=t.rect.bottom
                    self.velocity.y=0

    def draw(self,surf,camera_offset):
        if self.invincible>0 and (self.invincible//5)%2==0: return
        surf.blit(self.image,self.rect.move(camera_offset))

# -------------------------
# CAMERA
# -------------------------
class Camera:
    def __init__(self,width,height):
        self.camera=pygame.Rect(0,0,width,height)
        self.width,self.height=width,height; self.zoom=1.0

    def update(self,target):
        x=min(0,max(-(self.width-CANVAS_WIDTH/self.zoom),
               -target.rect.centerx+(CANVAS_WIDTH//2)/self.zoom))
        y=min(0,max(-(self.height-CANVAS_HEIGHT/self.zoom),
               -target.rect.centery+(CANVAS_HEIGHT//2)/self.zoom))
        self.camera=pygame.Rect(x,y,self.width,self.height)

    def move(self,dx,dy):
        self.camera.x=max(-(self.width-CANVAS_WIDTH/self.zoom), min(0,self.camera.x+dx/self.zoom))
        self.camera.y=max(-(self.height-CANVAS_HEIGHT/self.zoom),min(0,self.camera.y+dy/self.zoom))

# -------------------------
# LAYER / SECTION / LEVEL
# -------------------------
class Layer:
    def __init__(self,name="Layer 1",visible=True,locked=False):
        self.name=name; self.visible=visible; self.locked=locked
        self.tiles=pygame.sprite.Group(); self.bgos=pygame.sprite.Group()
        self.npcs=pygame.sprite.Group(); self.tile_map={}

    def add_tile(self,tile):
        self.tiles.add(tile); self.tile_map[(tile.rect.x,tile.rect.y)]=tile

    def remove_tile(self,tile):
        self.tiles.remove(tile)
        self.tile_map.pop((tile.rect.x,tile.rect.y),None)

class Section:
    def __init__(self,width=100,height=30):
        self.width=width*GRID_SIZE; self.height=height*GRID_SIZE
        self.layers=[Layer("Layer 1")]; self.current_layer_idx=0
        self.bg_color=(92,148,252); self.music=1

    def current_layer(self): return self.layers[self.current_layer_idx]

    def get_solid_tiles(self):
        return [t for layer in self.layers if layer.visible
                for t in layer.tiles if t.is_solid]

class Level:
    def __init__(self):
        self.sections=[Section()]; self.current_section_idx=0
        self.start_pos=(100,500); self.name="Untitled"; self.author="Unknown"

    def current_section(self): return self.sections[self.current_section_idx]
    def current_layer(self):   return self.current_section().current_layer()

# -------------------------
# FILE I/O
# -------------------------
def read_lvl(filename):
    level=Level(); section=level.current_section()
    try:
        with open(filename,'rb') as f:
            nb,ng,nn=struct.unpack('<III',f.read(12))
            for _ in range(nb):
                x,y,sid,lyr,ev=struct.unpack('<IIIII',f.read(20))
                if sid in TILE_ID_TO_NAME and lyr<len(section.layers):
                    section.layers[lyr].add_tile(Tile(x,y,TILE_ID_TO_NAME[sid],lyr))
            for _ in range(ng):
                x,y,sid,lyr,ev=struct.unpack('<IIIII',f.read(20))
                if sid in BGO_ID_TO_NAME and lyr<len(section.layers):
                    section.layers[lyr].bgos.add(BGO(x,y,BGO_ID_TO_NAME[sid],lyr))
            for _ in range(nn):
                x,y,sid,lyr,ev=struct.unpack('<IIIII',f.read(20))
                if sid in NPC_ID_TO_NAME and lyr<len(section.layers):
                    section.layers[lyr].npcs.add(NPC(x,y,NPC_ID_TO_NAME[sid],lyr))
    except Exception as e: print("Load error:",e)
    return level

def write_lvl(filename,level):
    section=level.current_section()
    blocks,bgos,npcs=[],[],[]
    for li,layer in enumerate(section.layers):
        for t in layer.tiles:
            blocks.append((t.rect.x,t.rect.y,TILE_SMBX_IDS.get(t.tile_type,1),li,0))
        for b in layer.bgos:
            bgos.append((b.rect.x,b.rect.y,BGO_SMBX_IDS.get(b.bgo_type,5),li,0))
        for n in layer.npcs:
            npcs.append((n.rect.x,n.rect.y,NPC_SMBX_IDS.get(n.npc_type,1),li,0))
    with open(filename,'wb') as f:
        f.write(struct.pack('<III',len(blocks),len(bgos),len(npcs)))
        for row in blocks+bgos+npcs:
            f.write(struct.pack('<IIIII',*row))

# -------------------------
# MENU SYSTEM
# -------------------------
class MenuItem:
    def __init__(self,label,callback=None,shortcut="",checkable=False,checked=False,separator=False):
        self.label=label; self.callback=callback; self.shortcut=shortcut
        self.checkable=checkable; self.checked=checked; self.separator=separator
        self.enabled=True

class DropMenu:
    ITEM_H=18; PAD=6
    def __init__(self,items):
        self.items=items
        self.hovered=-1
        w=max((FONT_SMALL.size(i.label+("  "+i.shortcut if i.shortcut else ""))[0]+30)
              for i in items if not i.separator)
        self.w=max(140,w)
        self.h=sum(6 if i.separator else self.ITEM_H for i in items)+self.PAD*2

    def draw(self,surf,x,y):
        r=pygame.Rect(x,y,self.w,self.h)
        pygame.draw.rect(surf,SYS_BTN_FACE,r)
        draw_edge(surf,r,raised=True)
        cy=y+self.PAD
        for i,item in enumerate(self.items):
            if item.separator:
                pygame.draw.line(surf,SYS_BTN_DARK,(x+4,cy+3),(x+self.w-4,cy+3))
                cy+=6; continue
            ir=pygame.Rect(x+2,cy,self.w-4,self.ITEM_H)
            if i==self.hovered and item.enabled:
                pygame.draw.rect(surf,SYS_HIGHLIGHT,ir)
            col=WHITE if i==self.hovered and item.enabled else (GRAY if not item.enabled else SYS_TEXT)
            if item.checkable:
                ch_col=col
                draw_text(surf,"✓"if item.checked else " ",(x+8,cy+2),ch_col,FONT_SMALL)
            draw_text(surf,item.label,(x+22,cy+2),col,FONT_SMALL)
            if item.shortcut:
                sw=FONT_SMALL.size(item.shortcut)[0]
                draw_text(surf,item.shortcut,(x+self.w-sw-6,cy+2),col,FONT_SMALL)
            cy+=self.ITEM_H

    def hit_item(self,pos,ox,oy):
        cy=oy+self.PAD
        for i,item in enumerate(self.items):
            if item.separator: cy+=6; continue
            ir=pygame.Rect(ox+2,cy,self.w-4,self.ITEM_H)
            if ir.collidepoint(pos): return i
            cy+=self.ITEM_H
        return -1

    def update_hover(self,pos,ox,oy):
        self.hovered=self.hit_item(pos,ox,oy)


class MenuBar:
    BAR_H=MENU_HEIGHT
    def __init__(self,menus_def):
        self.menus=[]   # (label, x, w, DropMenu)
        self.open_idx=-1
        x=4
        for label,items in menus_def:
            w=FONT_MENU.size(label)[0]+14
            dm=DropMenu(items)
            self.menus.append([label,x,w,dm])
            x+=w

    def handle_event(self,event):
        if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
            mx,my=event.pos
            if my<self.BAR_H:
                for i,(lbl,bx,bw,dm) in enumerate(self.menus):
                    if bx<=mx<bx+bw:
                        self.open_idx= -1 if self.open_idx==i else i
                        return True
            elif self.open_idx>=0:
                lbl,bx,bw,dm=self.menus[self.open_idx]
                idx=dm.hit_item(event.pos,bx,self.BAR_H)
                if idx>=0:
                    item=dm.items[idx]
                    if item.enabled and item.callback:
                        item.callback()
                        if item.checkable: item.checked=not item.checked
                self.open_idx=-1
                return True
            else:
                self.open_idx=-1
        if event.type==pygame.MOUSEMOTION and self.open_idx>=0:
            lbl,bx,bw,dm=self.menus[self.open_idx]
            dm.update_hover(event.pos,bx,self.BAR_H)
            # Switch open menu on hover
            for i,(l2,bx2,bw2,dm2) in enumerate(self.menus):
                if bx2<=event.pos[0]<bx2+bw2 and event.pos[1]<self.BAR_H:
                    self.open_idx=i
        if event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE:
            self.open_idx=-1
        return False

    def draw(self,surf):
        pygame.draw.rect(surf,SYS_BTN_FACE,(0,0,WINDOW_WIDTH,self.BAR_H))
        pygame.draw.line(surf,SYS_BTN_DARK,(0,self.BAR_H-1),(WINDOW_WIDTH,self.BAR_H-1))
        for i,(lbl,bx,bw,dm) in enumerate(self.menus):
            r=pygame.Rect(bx,1,bw,self.BAR_H-2)
            if i==self.open_idx:
                pygame.draw.rect(surf,SYS_HIGHLIGHT,r)
                draw_text(surf,lbl,(bx+7,3),WHITE,FONT_MENU)
            else:
                draw_text(surf,lbl,(bx+7,3),SYS_TEXT,FONT_MENU)
        if self.open_idx>=0:
            lbl,bx,bw,dm=self.menus[self.open_idx]
            dm.draw(surf,bx,self.BAR_H)

# -------------------------
# TOOLBAR BUTTON
# -------------------------
class ToolbarButton:
    def __init__(self,rect,icon_key,callback=None,tooltip="",toggle=False):
        self.rect=pygame.Rect(rect); self.icon_key=icon_key
        self.callback=callback; self.tooltip=tooltip
        self.hovered=False; self.pressed=False; self.toggle=toggle; self.active=False

    def handle_event(self,event):
        if event.type==pygame.MOUSEMOTION: self.hovered=self.rect.collidepoint(event.pos)
        if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
            if self.rect.collidepoint(event.pos): self.pressed=True; return True
        if event.type==pygame.MOUSEBUTTONUP and event.button==1:
            if self.pressed and self.rect.collidepoint(event.pos) and self.callback:
                if self.toggle: self.active=not self.active
                self.callback()
            self.pressed=False
        return False

    def draw(self,surf):
        sunken=self.pressed or (self.toggle and self.active)
        if sunken:
            pygame.draw.rect(surf,SYS_BTN_FACE,self.rect)
            pygame.draw.line(surf,SYS_BTN_DARK,self.rect.topleft,self.rect.topright)
            pygame.draw.line(surf,SYS_BTN_DARK,self.rect.topleft,self.rect.bottomleft)
        elif self.hovered:
            pygame.draw.rect(surf,SYS_BTN_FACE,self.rect)
            pygame.draw.line(surf,SYS_BTN_LIGHT,self.rect.topleft,self.rect.topright)
            pygame.draw.line(surf,SYS_BTN_LIGHT,self.rect.topleft,self.rect.bottomleft)
            pygame.draw.line(surf,SYS_BTN_DARK,self.rect.bottomleft,self.rect.bottomright)
            pygame.draw.line(surf,SYS_BTN_DARK,self.rect.topright,self.rect.bottomright)
        else:
            pygame.draw.rect(surf,SYS_BTN_FACE,self.rect)
        fn=ICON_FNS.get(self.icon_key)
        if fn:
            off=(1,1) if sunken else (0,0)
            fn(surf,self.rect.move(off[0],off[1]))

# -------------------------
# SIDEBAR
# -------------------------
class Sidebar:
    def __init__(self):
        self.rect=pygame.Rect(0,CANVAS_Y,SIDEBAR_WIDTH,CANVAS_HEIGHT)
        self.categories=["Tiles","BGOs","NPCs","Layers"]
        self.current_category="Tiles"
        self.items={"Tiles":list(TILE_SMBX_IDS.keys()),"BGOs":list(BGO_SMBX_IDS.keys()),
                    "NPCs":list(NPC_SMBX_IDS.keys()),"Layers":[]}
        self.selected_item='ground'
        self.tab_h=20; self.title_h=18

    def draw(self,surf,level):
        pygame.draw.rect(surf,SYS_BTN_FACE,self.rect)
        draw_edge(surf,self.rect,raised=False)
        tr=pygame.Rect(self.rect.x+2,self.rect.y+2,self.rect.width-4,self.title_h)
        pygame.draw.rect(surf,SYS_HIGHLIGHT,tr)
        draw_text(surf,"Item Palette",(tr.x+4,tr.y+3),WHITE,FONT_SMALL)
        tab_y=self.rect.y+self.title_h+2
        tab_w=self.rect.width//len(self.categories)
        for i,cat in enumerate(self.categories):
            r=pygame.Rect(self.rect.x+2+i*tab_w,tab_y,tab_w-2,self.tab_h)
            sel=(cat==self.current_category)
            pygame.draw.rect(surf,SYS_WINDOW if sel else SYS_BTN_FACE,r)
            draw_edge(surf,r,raised=not sel)
            draw_text(surf,cat,r.center,SYS_TEXT,FONT_SMALL,True)
        content=pygame.Rect(self.rect.x+2,tab_y+self.tab_h,self.rect.width-4,
                            self.rect.height-self.title_h-self.tab_h-4)
        pygame.draw.rect(surf,SYS_WINDOW,content)
        if self.current_category=="Layers": self._draw_layers(surf,content,level)
        else: self._draw_items(surf,content)

    def _draw_items(self,surf,area):
        items=self.items[self.current_category]
        for i,item in enumerate(items):
            r=pygame.Rect(area.x+4+(i%5)*36,area.y+4+(i//5)*36,32,32)
            if not area.contains(r): continue
            if item==self.selected_item:
                pygame.draw.rect(surf,SYS_HIGHLIGHT2,r.inflate(4,4))
            color=get_theme_color(item)
            pygame.draw.rect(surf,color,r.inflate(-2,-2))
            pygame.draw.rect(surf,BLACK,r.inflate(-2,-2),1)
            # Mini label
            draw_text(surf,item[:4],(r.x+2,r.bottom+1),SYS_TEXT,FONT_SMALL)

    def _draw_layers(self,surf,area,level):
        y=area.y+5; section=level.current_section()
        for i,layer in enumerate(section.layers):
            r=pygame.Rect(area.x+2,y,area.width-4,18)
            pygame.draw.rect(surf,SYS_HIGHLIGHT if i==section.current_layer_idx else SYS_WINDOW,r)
            col=WHITE if i==section.current_layer_idx else SYS_TEXT
            draw_text(surf,layer.name,(r.x+5,r.y+1),col,FONT_SMALL)
            pygame.draw.circle(surf,GREEN if layer.visible else RED,(r.right-8,r.centery),4)
            pygame.draw.rect(surf,GRAY if layer.locked else SYS_BTN_FACE,(r.right-20,r.y+2,8,8))
            y+=22

    def handle_click(self,pos,level):
        tab_y=self.rect.y+self.title_h+2; tab_w=self.rect.width//len(self.categories)
        for i,cat in enumerate(self.categories):
            r=pygame.Rect(self.rect.x+2+i*tab_w,tab_y,tab_w-2,self.tab_h)
            if r.collidepoint(pos): self.current_category=cat; return True
        content=pygame.Rect(self.rect.x+2,tab_y+self.tab_h,self.rect.width-4,
                            self.rect.height-self.title_h-self.tab_h-4)
        if self.current_category=="Layers":
            y=content.y+5; section=level.current_section()
            for i,layer in enumerate(section.layers):
                r=pygame.Rect(content.x+2,y,content.width-4,18)
                if r.collidepoint(pos):
                    if pos[0]>r.right-20: layer.locked=not layer.locked
                    elif pos[0]>r.right-35: layer.visible=not layer.visible
                    else: section.current_layer_idx=i
                    return True
                y+=22
        else:
            items=self.items[self.current_category]
            for i,item in enumerate(items):
                r=pygame.Rect(content.x+4+(i%5)*36,content.y+4+(i//5)*36,32,32)
                if r.collidepoint(pos): self.selected_item=item; return True
        return False

# -------------------------
# EDITOR
# -------------------------
class Editor:
    def __init__(self,level,screen):
        self.screen=screen
        self.level=level
        self.camera=Camera(level.current_section().width,level.current_section().height)
        self.playtest_mode=False; self.player=None
        self.undo_stack=[]; self.redo_stack=[]
        self.sidebar=Sidebar()
        self.drag_draw=False; self.drag_erase=False
        self.current_file=None; self.selection=[]; self.clipboard=[]
        self.tool='pencil'; self.grid_enabled=True; self.mouse_pos=(0,0)
        self.tooltip_text=""; self.status_msg=""
        self._build_menu()
        self._build_toolbar()

    # ---- MENU CONSTRUCTION ----
    def _build_menu(self):
        MI=MenuItem
        file_items=[
            MI("New Level",      self.cmd_new,        "Ctrl+N"),
            MI("Open Level...",  self.cmd_open,       "Ctrl+O"),
            MI("Save",           self.cmd_save,       "Ctrl+S"),
            MI("Save As...",     self.cmd_save_as,    "Ctrl+Shift+S"),
            MI("",separator=True),
            MI("Export as JSON", self.cmd_export_json,""),
            MI("",separator=True),
            MI("Exit",           self.cmd_exit,       "Alt+F4"),
        ]
        edit_items=[
            MI("Undo",           self.undo,            "Ctrl+Z"),
            MI("Redo",           self.redo,            "Ctrl+Y"),
            MI("",separator=True),
            MI("Cut",            self.cut_selection,   "Ctrl+X"),
            MI("Copy",           self.copy_selection,  "Ctrl+C"),
            MI("Paste",          self.paste_clipboard, "Ctrl+V"),
            MI("Delete",         self.delete_selected, "Del"),
            MI("",separator=True),
            MI("Select All",     self.select_all,      "Ctrl+A"),
            MI("Deselect All",   self.deselect_all,    "Esc"),
        ]
        view_items=[
            MI("Zoom In",        self.cmd_zoom_in,     "Ctrl+="),
            MI("Zoom Out",       self.cmd_zoom_out,    "Ctrl+-"),
            MI("Reset Zoom",     self.cmd_zoom_reset,  "Ctrl+0"),
            MI("",separator=True),
            MI("Toggle Grid",    self.cmd_toggle_grid, "G", checkable=True, checked=True),
            MI("",separator=True),
            MI("Theme: SMB1",    lambda:self.cmd_set_theme('SMB1')),
            MI("Theme: SMB3",    lambda:self.cmd_set_theme('SMB3')),
            MI("Theme: SMW",     lambda:self.cmd_set_theme('SMW')),
        ]
        level_items=[
            MI("Level Properties...", self.cmd_properties, "F4"),
            MI("",separator=True),
            MI("Add Layer",      self.cmd_add_layer,   ""),
            MI("Layer Manager...",self.cmd_layer_manager,""),
            MI("",separator=True),
            MI("Set Start Pos",  self.cmd_set_start,   ""),
            MI("Fill BG",        self.cmd_fill_bg,     ""),
            MI("Clear All",      self.cmd_clear_all,   ""),
        ]
        tool_items=[
            MI("Select",  self.set_tool_select, "S"),
            MI("Pencil",  self.set_tool_pencil, "P"),
            MI("Eraser",  self.set_tool_erase,  "E"),
            MI("Fill",    self.set_tool_fill,   "F"),
        ]
        test_items=[
            MI("Playtest",       self.toggle_playtest, "F5"),
            MI("",separator=True),
            MI("Reset Player",   self.cmd_reset_player,""),
        ]
        help_items=[
            MI("Controls...",    self.cmd_help,        "F1"),
            MI("About...",       self.cmd_about,       ""),
        ]
        self.menubar=MenuBar([
            ("File",  file_items),
            ("Edit",  edit_items),
            ("View",  view_items),
            ("Level", level_items),
            ("Tools", tool_items),
            ("Test",  test_items),
            ("Help",  help_items),
        ])

    # ---- TOOLBAR ----
    def _build_toolbar(self):
        items=[
            ("new",     self.cmd_new,       "New Level (Ctrl+N)"),
            ("open",    self.cmd_open,      "Open Level (Ctrl+O)"),
            ("save",    self.cmd_save,      "Save (Ctrl+S)"),
            None,
            ("undo",    self.undo,          "Undo (Ctrl+Z)"),
            ("redo",    self.redo,          "Redo (Ctrl+Y)"),
            None,
            ("select",  self.set_tool_select,"Select Tool [S]"),
            ("pencil",  self.set_tool_pencil,"Pencil Tool [P]"),
            ("eraser",  self.set_tool_erase, "Eraser Tool [E]"),
            ("fill",    self.set_tool_fill,  "Fill Tool [F]"),
            None,
            ("grid",    self.cmd_toggle_grid,"Toggle Grid [G]",True),
            ("zoom_in", self.cmd_zoom_in,   "Zoom In (Ctrl+=)"),
            ("zoom_out",self.cmd_zoom_out,  "Zoom Out (Ctrl+-)"),
            None,
            ("layer",   self.cmd_layer_manager,"Layer Manager"),
            ("props",   self.cmd_properties,"Level Properties [F4]"),
            None,
            ("play",    self.toggle_playtest,"Playtest [F5]",True),
        ]
        self.toolbar_btns=[]
        x=SIDEBAR_WIDTH+4
        for item in items:
            if item is None: x+=8; continue
            if len(item)==4:
                ik,cb,tip,tog=item
                self.toolbar_btns.append(ToolbarButton((x,MENU_HEIGHT+2,22,22),ik,cb,tip,toggle=tog))
            else:
                ik,cb,tip=item
                self.toolbar_btns.append(ToolbarButton((x,MENU_HEIGHT+2,22,22),ik,cb,tip))
            x+=24

    # ---- MENU COMMANDS ----
    def cmd_new(self):
        res=MessageBox(self.screen,"New Level",
                       "Discard current level and start new?",("Yes","No")).run()
        if res=="Yes":
            self.level=Level(); self.current_file=None
            self.camera=Camera(self.level.current_section().width,self.level.current_section().height)
            self.undo_stack.clear(); self.redo_stack.clear(); self.selection.clear()
            self.status("New level created.")

    def cmd_open(self):
        dlg=InputDialog(self.screen,"Open Level","Enter filename:","level.lvl")
        fn=dlg.run()
        if fn:
            if os.path.exists(fn):
                self.level=read_lvl(fn); self.current_file=fn
                self.camera=Camera(self.level.current_section().width,self.level.current_section().height)
                self.status(f"Opened: {fn}")
            else:
                MessageBox(self.screen,"Error",f"File not found:\n{fn}").run()

    def cmd_save(self):
        if not self.current_file:
            self.cmd_save_as(); return
        write_lvl(self.current_file,self.level)
        self.status(f"Saved: {self.current_file}")

    def cmd_save_as(self):
        dlg=InputDialog(self.screen,"Save As","Enter filename:",
                        self.current_file or "level.lvl")
        fn=dlg.run()
        if fn:
            self.current_file=fn
            write_lvl(fn,self.level)
            self.status(f"Saved as: {fn}")

    def cmd_export_json(self):
        fn=(self.current_file or "level").replace(".lvl","")+".json"
        section=self.level.current_section()
        data={"name":self.level.name,"author":self.level.author,"tiles":[],"bgos":[],"npcs":[]}
        for li,layer in enumerate(section.layers):
            for t in layer.tiles:
                data["tiles"].append({"x":t.rect.x,"y":t.rect.y,"type":t.tile_type,"layer":li})
            for b in layer.bgos:
                data["bgos"].append({"x":b.rect.x,"y":b.rect.y,"type":b.bgo_type,"layer":li})
            for n in layer.npcs:
                data["npcs"].append({"x":n.rect.x,"y":n.rect.y,"type":n.npc_type,"layer":li})
        with open(fn,'w') as f: json.dump(data,f,indent=2)
        MessageBox(self.screen,"Export","Exported to:\n"+fn).run()

    def cmd_exit(self):
        res=MessageBox(self.screen,"Exit","Exit Mario Fan Builder?",("Yes","No")).run()
        if res=="Yes": pygame.quit(); sys.exit()

    def cmd_zoom_in(self):
        self.camera.zoom=min(ZOOM_MAX,round(self.camera.zoom+ZOOM_STEP,2))
        self.status(f"Zoom: {int(self.camera.zoom*100)}%")

    def cmd_zoom_out(self):
        self.camera.zoom=max(ZOOM_MIN,round(self.camera.zoom-ZOOM_STEP,2))
        self.status(f"Zoom: {int(self.camera.zoom*100)}%")

    def cmd_zoom_reset(self):
        self.camera.zoom=1.0; self.status("Zoom: 100%")

    def cmd_toggle_grid(self):
        self.grid_enabled=not self.grid_enabled
        self.status("Grid: "+"ON" if self.grid_enabled else "OFF")
        # Sync menu checkmark
        for lbl,bx,bw,dm in self.menubar.menus:
            if lbl=="View":
                for item in dm.items:
                    if item.label=="Toggle Grid": item.checked=self.grid_enabled
        # Sync toolbar toggle
        for btn in self.toolbar_btns:
            if btn.icon_key=='grid': btn.active=self.grid_enabled

    def cmd_set_theme(self,theme):
        global current_theme
        current_theme=theme
        # Refresh all tile images
        section=self.level.current_section()
        for layer in section.layers:
            for t in layer.tiles: t.update_image()
            for b in layer.bgos:  b.update_image()
            for n in layer.npcs:  n.update_image()
        self.status(f"Theme: {theme}")

    def cmd_properties(self):
        PropertiesDialog(self.screen,self.level).run()
        self.camera=Camera(self.level.current_section().width,self.level.current_section().height)
        # Refresh images for theme change
        section=self.level.current_section()
        for layer in section.layers:
            for t in layer.tiles: t.update_image()

    def cmd_add_layer(self):
        section=self.level.current_section()
        section.layers.append(Layer(f"Layer {len(section.layers)+1}"))
        self.status(f"Added layer {len(section.layers)}")

    def cmd_layer_manager(self):
        LayerDialog(self.screen,self.level.current_section()).run()

    def cmd_set_start(self):
        wx,wy=self.get_mouse_world()
        gx,gy=self.world_to_grid(wx,wy)
        self.level.start_pos=(gx,gy)
        self.status(f"Start pos set: {gx},{gy}")

    def cmd_fill_bg(self):
        bgs=list(BG_PRESETS.items())
        # Show quick picker
        dlg=MessageBox(self.screen,"Background",
                       "Choose:\n"+"  ".join(f"{i+1}={n}" for i,( n,_) in enumerate(bgs)),
                       tuple(str(i+1) for i in range(len(bgs)))+("Cancel",))
        res=dlg.run()
        if res and res!="Cancel":
            try:
                idx=int(res)-1
                self.level.current_section().bg_color=bgs[idx][1]
            except: pass

    def cmd_clear_all(self):
        res=MessageBox(self.screen,"Clear All",
                       "Clear ALL objects from level?\nThis cannot be undone!",("Yes","No")).run()
        if res=="Yes":
            section=self.level.current_section()
            for layer in section.layers:
                layer.tiles.empty(); layer.bgos.empty(); layer.npcs.empty(); layer.tile_map.clear()
            self.undo_stack.clear(); self.redo_stack.clear(); self.selection.clear()
            self.status("Level cleared.")

    def cmd_reset_player(self):
        if self.player:
            self.player.rect.topleft=self.level.start_pos
            self.player.velocity.update(0,0)
            self.status("Player reset.")

    def cmd_help(self):
        MessageBox(self.screen,"Controls",
            "EDITOR:\n"
            "  Left Click - Place / Select\n"
            "  Right Click - Erase\n"
            "  Arrow Keys - Scroll\n"
            "  Ctrl+Z/Y - Undo/Redo\n"
            "  Ctrl+C/V/X - Copy/Paste/Cut\n"
            "  Ctrl+A - Select All\n"
            "  G - Toggle Grid\n"
            "  Ctrl+=/-  Zoom In/Out\n"
            "  F5 - Playtest\n\n"
            "PLAYTEST:\n"
            "  Arrow/WASD - Move\n"
            "  Space - Jump\n"
            "  Escape - Back to editor"
        ).run()

    def cmd_about(self):
        MessageBox(self.screen,"About",
            "Mario Fan Builder\n"
            "CATSAN Engine [C] AC Holding\n\n"
            "An SMBX 1.3 style level editor\n"
            "Built with Python + Pygame"
        ).run()

    def select_all(self):
        self.selection.clear()
        layer=self.level.current_layer()
        self.selection.extend(layer.tiles.sprites())
        self.selection.extend(layer.bgos.sprites())
        self.selection.extend(layer.npcs.sprites())
        self.status(f"Selected {len(self.selection)} objects")

    def deselect_all(self):
        self.selection.clear()

    def delete_selected(self):
        for obj in self.selection:
            self._delete_object(obj)
        self.selection.clear()
        self.status("Deleted selected objects")

    # ---- TOOLS ----
    def set_tool_select(self): self.tool='select';  self.status("Tool: Select")
    def set_tool_pencil(self): self.tool='pencil';  self.status("Tool: Pencil")
    def set_tool_erase(self):  self.tool='erase';   self.status("Tool: Eraser")
    def set_tool_fill(self):   self.tool='fill';    self.status("Tool: Fill")

    def toggle_playtest(self):
        if self.menubar.open_idx>=0: self.menubar.open_idx=-1
        self.playtest_mode=not self.playtest_mode
        if self.playtest_mode:
            self.player=Player(*self.level.start_pos)
            self.camera.update(self.player)
            self.status("PLAYTEST - Esc to return")
        else:
            self.player=None; self.status("Editor mode")
        for btn in self.toolbar_btns:
            if btn.icon_key=='play': btn.active=self.playtest_mode

    def status(self,msg): self.status_msg=msg

    # ---- UNDO/REDO ----
    def push_undo(self,action):
        self.undo_stack.append(action); self.redo_stack.clear()

    def undo(self):
        if not self.undo_stack: self.status("Nothing to undo"); return
        action=self.undo_stack.pop(); action['undo'](); self.redo_stack.append(action)
        self.status("Undo")

    def redo(self):
        if not self.redo_stack: self.status("Nothing to redo"); return
        action=self.redo_stack.pop(); action['redo'](); self.undo_stack.append(action)
        self.status("Redo")

    # ---- COORD HELPERS ----
    def world_to_grid(self,wx,wy):
        return (int(wx)//GRID_SIZE)*GRID_SIZE,(int(wy)//GRID_SIZE)*GRID_SIZE

    def get_mouse_world(self):
        mx,my=self.mouse_pos
        return ((mx-SIDEBAR_WIDTH)/self.camera.zoom-self.camera.camera.x,
                (my-CANVAS_Y)/self.camera.zoom-self.camera.camera.y)

    def canvas_to_world(self,sx,sy):
        return (sx-SIDEBAR_WIDTH)/self.camera.zoom-self.camera.camera.x,\
               (sy-CANVAS_Y)/self.camera.zoom-self.camera.camera.y

    # ---- OBJECT PLACEMENT ----
    def place_object(self,gx,gy):
        layer=self.level.current_layer()
        if layer.locked: return
        key=(gx,gy)
        if self.sidebar.current_category=="NPCs":
            npc=NPC(gx,gy,self.sidebar.selected_item,layer=layer)
            layer.npcs.add(npc)
            self.push_undo({'undo':lambda l=layer,n=npc:l.npcs.remove(n),
                            'redo':lambda l=layer,n=npc:l.npcs.add(n)})
        elif self.sidebar.current_category=="BGOs":
            bgo=BGO(gx,gy,self.sidebar.selected_item,layer=layer)
            layer.bgos.add(bgo)
            self.push_undo({'undo':lambda l=layer,b=bgo:l.bgos.remove(b),
                            'redo':lambda l=layer,b=bgo:l.bgos.add(b)})
        else:
            if key in layer.tile_map: return
            tile=Tile(gx,gy,self.sidebar.selected_item,layer=layer)
            layer.add_tile(tile)
            self.push_undo({'undo':lambda l=layer,t=tile:l.remove_tile(t),
                            'redo':lambda l=layer,t=tile:l.add_tile(t)})

    def erase_object(self,gx,gy):
        layer=self.level.current_layer()
        if layer.locked: return
        key=(gx,gy)
        if key in layer.tile_map:
            tile=layer.tile_map[key]; layer.remove_tile(tile)
            self.push_undo({'undo':lambda l=layer,t=tile:l.add_tile(t),
                            'redo':lambda l=layer,k=key:l.remove_tile(l.tile_map[k]) if k in l.tile_map else None})
            return
        for group,kind in [(layer.npcs,'npc'),(layer.bgos,'bgo')]:
            for obj in list(group):
                if obj.rect.x==gx and obj.rect.y==gy:
                    group.remove(obj)
                    self.push_undo({'undo':lambda g=group,o=obj:g.add(o),
                                    'redo':lambda g=group,o=obj:g.remove(o)})
                    return

    def fill_area(self,sx,sy):
        layer=self.level.current_layer()
        if layer.locked: return
        target=self.sidebar.selected_item
        start=(sx,sy)
        old_type=layer.tile_map[start].tile_type if start in layer.tile_map else None
        if old_type==target: return
        queue=deque([start]); visited=set(); new_tiles=[]
        while queue:
            x,y=queue.popleft()
            if (x,y) in visited: continue
            visited.add((x,y))
            if old_type is None:
                if (x,y) in layer.tile_map: continue
            else:
                if (x,y) not in layer.tile_map or layer.tile_map[(x,y)].tile_type!=old_type: continue
            if (x,y) in layer.tile_map: layer.remove_tile(layer.tile_map[(x,y)])
            t=Tile(x,y,target,layer=layer); layer.add_tile(t); new_tiles.append(t)
            sec=self.level.current_section()
            for dx,dy in [(GRID_SIZE,0),(-GRID_SIZE,0),(0,GRID_SIZE),(0,-GRID_SIZE)]:
                nx,ny=x+dx,y+dy
                if 0<=nx<sec.width and 0<=ny<sec.height: queue.append((nx,ny))
        if new_tiles:
            self.push_undo({'undo':lambda l=layer,nt=new_tiles:[l.remove_tile(t) for t in nt],
                            'redo':lambda l=layer,nt=new_tiles:[l.add_tile(t) for t in nt]})

    def handle_select(self,gx,gy,event):
        layer=self.level.current_layer(); obj=None
        if (gx,gy) in layer.tile_map: obj=layer.tile_map[(gx,gy)]
        else:
            for n in layer.npcs:
                if n.rect.x==gx and n.rect.y==gy: obj=n; break
            if not obj:
                for b in layer.bgos:
                    if b.rect.x==gx and b.rect.y==gy: obj=b; break
        if obj:
            mods=pygame.key.get_mods()
            if mods&pygame.KMOD_SHIFT:
                if obj in self.selection: self.selection.remove(obj)
                else: self.selection.append(obj)
            else: self.selection=[obj]

    def copy_selection(self):
        self.clipboard=[(o.rect.x,o.rect.y,o.obj_type,o.layer) for o in self.selection]
        self.status(f"Copied {len(self.clipboard)} object(s)")

    def cut_selection(self):
        self.copy_selection()
        for o in self.selection: self._delete_object(o)
        self.selection.clear()

    def paste_clipboard(self):
        if not self.clipboard: return
        wx,wy=self.get_mouse_world()
        bx,by=self.world_to_grid(wx,wy)
        ox,oy=self.clipboard[0][0],self.clipboard[0][1]
        for x,y,otype,li in self.clipboard:
            nx,ny=bx+(x-ox),by+(y-oy)
            if otype in TILE_SMBX_IDS:
                self.level.current_section().layers[li].add_tile(Tile(nx,ny,otype,li))
            elif otype in BGO_SMBX_IDS:
                self.level.current_section().layers[li].bgos.add(BGO(nx,ny,otype,li))
            elif otype in NPC_SMBX_IDS:
                self.level.current_section().layers[li].npcs.add(NPC(nx,ny,otype,li))
        self.status(f"Pasted {len(self.clipboard)} object(s)")

    def _delete_object(self,obj):
        layer=self.level.current_section().layers[obj.layer if isinstance(obj.layer,int) else 0]
        if isinstance(obj,Tile): layer.remove_tile(obj)
        elif isinstance(obj,BGO): layer.bgos.remove(obj)
        elif isinstance(obj,NPC): layer.npcs.remove(obj)

    # ---- EVENT HANDLING ----
    def handle_event(self,event):
        if event.type==pygame.QUIT: return False

        # Menu eats events first
        if self.menubar.handle_event(event):
            return True

        for btn in self.toolbar_btns:
            btn.handle_event(event)

        if event.type==pygame.MOUSEMOTION:
            self.mouse_pos=event.pos
            self.tooltip_text=""
            for btn in self.toolbar_btns:
                if btn.rect.collidepoint(event.pos): self.tooltip_text=btn.tooltip

        if event.type==pygame.KEYDOWN:
            mods=pygame.key.get_mods()
            ctrl=mods&pygame.KMOD_CTRL
            if event.key==pygame.K_ESCAPE:
                if self.playtest_mode: self.toggle_playtest()
                elif self.menubar.open_idx>=0: self.menubar.open_idx=-1
                else: self.deselect_all()
            # Tool keys (only when not in playtest)
            if not self.playtest_mode and not ctrl:
                if event.key==pygame.K_s and not mods: self.set_tool_select()
                if event.key==pygame.K_p: self.set_tool_pencil()
                if event.key==pygame.K_e: self.set_tool_erase()
                if event.key==pygame.K_f: self.set_tool_fill()
                if event.key==pygame.K_g: self.cmd_toggle_grid()
                if event.key==pygame.K_LEFT:  self.camera.move(GRID_SIZE,0)
                if event.key==pygame.K_RIGHT: self.camera.move(-GRID_SIZE,0)
                if event.key==pygame.K_UP:    self.camera.move(0,GRID_SIZE)
                if event.key==pygame.K_DOWN:  self.camera.move(0,-GRID_SIZE)
                if event.key==pygame.K_F4:    self.cmd_properties()
                if event.key==pygame.K_F5:    self.toggle_playtest()
                if event.key==pygame.K_F1:    self.cmd_help()
                if event.key==pygame.K_DELETE: self.delete_selected()
            if ctrl:
                if event.key==pygame.K_n: self.cmd_new()
                if event.key==pygame.K_o: self.cmd_open()
                if event.key==pygame.K_s: self.cmd_save()
                if event.key==pygame.K_z: self.undo()
                if event.key==pygame.K_y: self.redo()
                if event.key==pygame.K_c: self.copy_selection()
                if event.key==pygame.K_v: self.paste_clipboard()
                if event.key==pygame.K_x: self.cut_selection()
                if event.key==pygame.K_a: self.select_all()
                if event.key==pygame.K_EQUALS or event.key==pygame.K_PLUS: self.cmd_zoom_in()
                if event.key==pygame.K_MINUS: self.cmd_zoom_out()
                if event.key==pygame.K_0: self.cmd_zoom_reset()

        # Mouse in canvas
        if event.type==pygame.MOUSEBUTTONDOWN:
            if self.sidebar.rect.collidepoint(event.pos) and event.button==1:
                self.sidebar.handle_click(event.pos,self.level)
            elif (event.pos[1]>CANVAS_Y and event.pos[0]>SIDEBAR_WIDTH
                  and not self.playtest_mode and self.menubar.open_idx<0):
                wx,wy=self.canvas_to_world(event.pos[0],event.pos[1])
                gx,gy=self.world_to_grid(wx,wy)
                if event.button==1:
                    if self.tool=='pencil': self.drag_draw=True; self.place_object(gx,gy)
                    elif self.tool=='erase': self.drag_erase=True; self.erase_object(gx,gy)
                    elif self.tool=='select': self.handle_select(gx,gy,event)
                    elif self.tool=='fill': self.fill_area(gx,gy)
                elif event.button==3:
                    self.drag_erase=True; self.erase_object(gx,gy)
                # Scroll wheel zoom
                elif event.button==4: self.cmd_zoom_in()
                elif event.button==5: self.cmd_zoom_out()

        if event.type==pygame.MOUSEMOTION and not self.playtest_mode:
            if self.drag_draw or self.drag_erase:
                wx,wy=self.canvas_to_world(event.pos[0],event.pos[1])
                gx,gy=self.world_to_grid(wx,wy)
                if self.drag_draw: self.place_object(gx,gy)
                elif self.drag_erase: self.erase_object(gx,gy)

        if event.type==pygame.MOUSEBUTTONUP:
            if event.button in(1,3): self.drag_draw=False; self.drag_erase=False

        return True

    # ---- UPDATE ----
    def update(self):
        if self.playtest_mode and self.player:
            section=self.level.current_section()
            solid=section.get_solid_tiles()
            npcs=pygame.sprite.Group()
            for layer in section.layers:
                if layer.visible: npcs.add(layer.npcs.sprites())
            self.player.update(solid,npcs)
            for npc in npcs: npc.update(solid,self.player)
            self.camera.update(self.player)

    # ---- DRAW ----
    def draw(self,surf):
        surf.fill(SYS_BTN_FACE)

        # Toolbar bar
        pygame.draw.rect(surf,SYS_BTN_FACE,(0,MENU_HEIGHT,WINDOW_WIDTH,TOOLBAR_HEIGHT))
        pygame.draw.line(surf,SYS_BTN_DARK,(0,MENU_HEIGHT+TOOLBAR_HEIGHT-1),(WINDOW_WIDTH,MENU_HEIGHT+TOOLBAR_HEIGHT-1))

        # Draw toolbar separators
        x=SIDEBAR_WIDTH+4
        items=[("new",),("open",),("save",),None,("undo",),("redo",),None,
               ("select",),("pencil",),("eraser",),("fill",),None,
               ("grid",),("zoom_in",),("zoom_out",),None,("layer",),("props",),None,("play",)]
        for item in items:
            if item is None:
                pygame.draw.line(surf,SYS_BTN_DARK,(x+2,MENU_HEIGHT+3),(x+2,MENU_HEIGHT+TOOLBAR_HEIGHT-4))
                pygame.draw.line(surf,SYS_BTN_LIGHT,(x+3,MENU_HEIGHT+3),(x+3,MENU_HEIGHT+TOOLBAR_HEIGHT-4))
                x+=8
            else: x+=24

        for btn in self.toolbar_btns:
            # Highlight active tool
            if btn.icon_key in('select','pencil','eraser','fill'):
                tool_map={'select':'select','pencil':'pencil','eraser':'erase','fill':'fill'}
                btn.active=(tool_map.get(btn.icon_key)==self.tool)
            btn.draw(surf)

        # Sidebar
        self.sidebar.draw(surf,self.level)

        # Canvas
        canvas_rect=pygame.Rect(SIDEBAR_WIDTH,CANVAS_Y,CANVAS_WIDTH,CANVAS_HEIGHT)
        surf.set_clip(canvas_rect)
        surf.fill(self.level.current_section().bg_color)

        # Grid
        if self.grid_enabled:
            zoom=self.camera.zoom; cam=self.camera.camera
            sc=int(-cam.x//GRID_SIZE); ec=sc+int(CANVAS_WIDTH/(GRID_SIZE*zoom))+2
            sr=int(-cam.y//GRID_SIZE); er=sr+int(CANVAS_HEIGHT/(GRID_SIZE*zoom))+2
            for c in range(sc,ec):
                px=c*GRID_SIZE+cam.x+SIDEBAR_WIDTH
                if canvas_rect.left<px<canvas_rect.right:
                    pygame.draw.line(surf,SMBX_GRID,(px,canvas_rect.y),(px,canvas_rect.bottom))
            for r in range(sr,er):
                py=r*GRID_SIZE+cam.y+CANVAS_Y
                if canvas_rect.top<py<canvas_rect.bottom:
                    pygame.draw.line(surf,SMBX_GRID,(canvas_rect.x,py),(canvas_rect.right,py))

        # Sprites
        section=self.level.current_section()
        for layer in section.layers:
            if not layer.visible: continue
            for bgo in layer.bgos:
                p=bgo.rect.move(self.camera.camera.x+SIDEBAR_WIDTH,self.camera.camera.y+CANVAS_Y)
                surf.blit(bgo.image,p)
            for tile in layer.tiles:
                p=tile.rect.move(self.camera.camera.x+SIDEBAR_WIDTH,self.camera.camera.y+CANVAS_Y)
                surf.blit(tile.image,p)
            for npc in layer.npcs:
                p=npc.rect.move(self.camera.camera.x+SIDEBAR_WIDTH,self.camera.camera.y+CANVAS_Y)
                surf.blit(npc.image,p)

        # Selection outlines
        if not self.playtest_mode:
            for obj in self.selection:
                p=obj.rect.move(self.camera.camera.x+SIDEBAR_WIDTH,self.camera.camera.y+CANVAS_Y)
                pygame.draw.rect(surf,YELLOW,p,2)
                pygame.draw.rect(surf,WHITE,p.inflate(2,2),1)

        # Start position marker
        sp=pygame.Rect(self.level.start_pos[0]+self.camera.camera.x+SIDEBAR_WIDTH,
                       self.level.start_pos[1]+self.camera.camera.y+CANVAS_Y,
                       GRID_SIZE,GRID_SIZE)
        if not self.playtest_mode:
            pygame.draw.rect(surf,GREEN,sp,2)
            draw_text(surf,"S",(sp.x+2,sp.y+2),GREEN,FONT_SMALL)

        # Player
        if self.playtest_mode and self.player:
            self.player.draw(surf,(self.camera.camera.x+SIDEBAR_WIDTH,self.camera.camera.y+CANVAS_Y))

        surf.set_clip(None)

        # Canvas border
        draw_edge(surf,canvas_rect,raised=False)

        # Status Bar
        sb_y=WINDOW_HEIGHT-STATUSBAR_HEIGHT
        pygame.draw.rect(surf,SYS_BTN_FACE,(0,sb_y,WINDOW_WIDTH,STATUSBAR_HEIGHT))
        pygame.draw.line(surf,SYS_BTN_LIGHT,(0,sb_y),(WINDOW_WIDTH,sb_y))

        def panel(px,pw,text):
            pr=pygame.Rect(px,sb_y+2,pw,STATUSBAR_HEIGHT-4)
            pygame.draw.rect(surf,SYS_BTN_FACE,pr); draw_edge(surf,pr,raised=False)
            draw_text(surf,text,(pr.x+4,pr.y+3),SYS_TEXT,FONT_SMALL)

        mode="PLAYTEST" if self.playtest_mode else f"{self.tool.upper()}"
        panel(2,120,f"Mode: {mode}")
        panel(126,160,f"Layer: {self.level.current_layer().name}")
        wx,wy=self.get_mouse_world()
        gx,gy=self.world_to_grid(wx,wy)
        panel(290,140,f"X:{int(gx//GRID_SIZE)} Y:{int(gy//GRID_SIZE)}")
        panel(434,100,f"Zoom: {int(self.camera.zoom*100)}%")
        if self.playtest_mode and self.player:
            panel(538,200,f"Coins:{self.player.coins}  Score:{self.player.score}")
        elif self.status_msg:
            panel(538,WINDOW_WIDTH-542,self.status_msg)

        # Tooltip
        if self.tooltip_text:
            tx,ty=self.mouse_pos; ty-=20
            tw=FONT_SMALL.size(self.tooltip_text)[0]+10
            tr=pygame.Rect(tx,max(CANVAS_Y,ty),tw,17)
            pygame.draw.rect(surf,(255,255,220),tr)
            draw_edge(surf,tr,raised=True)
            draw_text(surf,self.tooltip_text,(tr.x+5,tr.y+3),BLACK,FONT_SMALL)

        # Menubar drawn LAST so dropdowns appear on top
        self.menubar.draw(surf)

# -------------------------
# MAIN MENU SCREEN
# -------------------------
def main_menu(screen):
    clock=pygame.time.Clock()
    btns=[
        pygame.Rect(WINDOW_WIDTH//2-100,300,200,32),
        pygame.Rect(WINDOW_WIDTH//2-100,340,200,32),
        pygame.Rect(WINDOW_WIDTH//2-100,380,200,32),
    ]
    labels=["New Level","Open Level","Quit"]
    hovered=-1

    while True:
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return "QUIT"
            if event.type==pygame.MOUSEMOTION:
                hovered=-1
                for i,r in enumerate(btns):
                    if r.collidepoint(event.pos): hovered=i
            if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
                for i,r in enumerate(btns):
                    if r.collidepoint(event.pos):
                        return ["NEW","LOAD","QUIT"][i]

        screen.fill(SYS_BTN_FACE)
        wr=pygame.Rect(WINDOW_WIDTH//2-220,80,440,360)
        pygame.draw.rect(screen,SYS_BTN_FACE,wr); draw_edge(screen,wr,raised=True)
        tr=pygame.Rect(wr.x,wr.y,wr.w,22)
        pygame.draw.rect(screen,SYS_HIGHLIGHT,tr)
        draw_text(screen,"Mario Fan Builder - CATSAN [C] AC Holding",(tr.x+4,tr.y+4),WHITE,FONT_SMALL)

        cr=pygame.Rect(wr.x+6,tr.bottom+6,wr.w-12,wr.h-tr.h-12)
        pygame.draw.rect(screen,SYS_WINDOW,cr); draw_edge(screen,cr,raised=False)

        draw_text(screen,"Mario Fan Builder",(cr.centerx,cr.y+40),SYS_HIGHLIGHT,FONT_TITLE,True)
        draw_text(screen,"SMBX 1.3 Style Level Editor",(cr.centerx,cr.y+70),SYS_TEXT,FONT,True)
        draw_text(screen,"CATSAN Engine  [C] AC Holding",(cr.centerx,cr.y+92),GRAY,FONT_SMALL,True)

        for i,(r,lbl) in enumerate(zip(btns,labels)):
            sel=(i==hovered)
            pygame.draw.rect(screen,SYS_HIGHLIGHT if sel else SYS_BTN_FACE,r)
            draw_edge(screen,r,raised=not sel)
            draw_text(screen,lbl,r.center,WHITE if sel else SYS_TEXT,FONT,True)

        pygame.display.flip(); clock.tick(60)

# -------------------------
# MAIN
# -------------------------
def main():
    screen=pygame.display.set_mode((WINDOW_WIDTH,WINDOW_HEIGHT))
    clock=pygame.time.Clock()
    while True:
        result=main_menu(screen)
        if result=="QUIT": pygame.quit(); sys.exit()
        level=Level()
        if result=="LOAD":
            dlg=InputDialog(screen,"Open Level","Enter filename:","level.lvl")
            fn=dlg.run()
            if fn and os.path.exists(fn): level=read_lvl(fn)
        editor=Editor(level,screen)
        running=True
        while running:
            for event in pygame.event.get():
                res=editor.handle_event(event)
                if res is False: pygame.quit(); sys.exit()
                if res=="MENU": running=False
            editor.update()
            editor.draw(screen)
            pygame.display.flip()
            clock.tick(FPS)

if __name__=="__main__":
    main()
