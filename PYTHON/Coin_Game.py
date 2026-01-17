
import pygame
import random
import math
import os
import sys

# --- Constants ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
TARGET_FPS = 120

# Colors
COLOR_BG = (26, 26, 26)
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_YELLOW = (255, 204, 0)
COLOR_SILVER = (192, 192, 192)
COLOR_RED = (255, 68, 68)
COLOR_BLUE = (0, 136, 255)
COLOR_CYAN = (0, 255, 255)
COLOR_GREEN = (0, 255, 0)
COLOR_TEXT_GRAY = (170, 170, 170)

# Game Constants
PLAYER_SIZE = 50
COIN_SIZE = 50
COIN_RADIUS = COIN_SIZE // 2

# Scale factors
# The original JS values (7, 5, 0.5, 15) seem effectively tuned for 60 FPS "base" feel.
TIME_SCALE = 60 / TARGET_FPS
PLAYER_SPEED = 7 * TIME_SCALE
COIN_SPEED = 5 * TIME_SCALE

# Default Physics
GRAVITY_DEFAULT = 0.5 * TIME_SCALE
JUMP_FORCE_DEFAULT = 15 * TIME_SCALE

# --- Global State ---
game_gravity = GRAVITY_DEFAULT
game_jump_force = JUMP_FORCE_DEFAULT

wallet = 0
score = 0
high_score = 0

upgrade_levels = {
    "multiplier": 0,
    "luck": 0,
    "goldChance": 0
}

current_skin_id = 'default'

upgrades_info = {
    "multiplier": {
        "name": "Coin Multiplier",
        "desc": "Boosts coins earned at end",
        "levels": [1.0, 1.2, 1.5, 2.0, 3.0],
        "costs": [100, 250, 500, 1000, "MAX"]
    },
    "luck": {
        "name": "Luck",
        "desc": "Increases power-up chance",
        "levels": [0.005, 0.02, 0.04, 0.06, 0.1],
        "costs": [150, 300, 600, 1200, "MAX"]
    },
    "goldChance": {
        "name": "Gold Rush",
        "desc": "Increases gold coin chance",
        "levels": [0.01, 0.05, 0.10, 0.20, 0.40],
        "costs": [200, 400, 800, 1600, "MAX"]
    }
}

skins_info = [
    {'id': 'default', 'name': 'Classic White', 'color': (255, 255, 255), 'price': 0, 'owned': True},
    {'id': 'blue', 'name': 'Cyber Blue', 'color': (0, 255, 255), 'price': 50, 'owned': False},
    {'id': 'pink', 'name': 'Neon Pink', 'color': (255, 0, 255), 'price': 100, 'owned': False},
    {'id': 'gold', 'name': 'Tycoon Gold', 'color': (255, 215, 0), 'price': 200, 'owned': False},
    {'id': 'matrix', 'name': 'Hacker Green', 'color': (0, 255, 0), 'price': 300, 'owned': False},
    {'id': 'red', 'name': 'Danger Red', 'color': (255, 68, 68), 'price': 500, 'owned': False}
]

# --- Pygame Initialization ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Coin Game - Space Catcher")
clock = pygame.time.Clock()

# Fonts
try:
    font_large = pygame.font.SysFont("Segoe UI", 48, bold=True)
    font_medium = pygame.font.SysFont("Segoe UI", 32, bold=True)
    font_small = pygame.font.SysFont("Segoe UI", 20)
    font_tiny = pygame.font.SysFont("Segoe UI", 16)
except:
    font_large = pygame.font.SysFont(None, 48)
    font_medium = pygame.font.SysFont(None, 32)
    font_small = pygame.font.SysFont(None, 24)
    font_tiny = pygame.font.SysFont(None, 18)

# --- Asset Manager ---
class ResourceManager:
    def __init__(self):
        self.gold_sprites = []
        self.silver_sprites = []
        self.load_sprites()

    def load_sprites(self):
        # Determine base path
        base_path = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(base_path, 'assets')
        
        # Helper to load sequence
        def load_seq(folder, prefix, count):
            sprites = []
            path = os.path.join(assets_dir, folder)
            if not os.path.exists(path):
                return []
            for i in range(1, count + 1):
                fname = f"{prefix}{i}.png"
                fpath = os.path.join(path, fname)
                if os.path.exists(fpath):
                    try:
                        img = pygame.image.load(fpath).convert_alpha()
                        img = pygame.transform.scale(img, (COIN_SIZE, COIN_SIZE))
                        sprites.append(img)
                    except:
                        pass
            return sprites

        self.gold_sprites = load_seq("Coin Animation_sprites", "coin", 6)
        self.silver_sprites = load_seq("Silver_sprites", "silver", 6)

    def get_gold(self, frame_idx):
        if not self.gold_sprites: return None
        return self.gold_sprites[frame_idx % len(self.gold_sprites)]

    def get_silver(self, frame_idx):
        if not self.silver_sprites: return None
        return self.silver_sprites[frame_idx % len(self.silver_sprites)]
    
    def get_frame_count(self):
        return max(len(self.gold_sprites), len(self.silver_sprites), 1)

resources = ResourceManager()

# --- Classes ---

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.uniform(3, 8)
        self.speed_x = random.uniform(-3, 3) * TIME_SCALE
        self.speed_y = random.uniform(-3, 3) * TIME_SCALE
        self.life = 1.0
        self.decay = random.uniform(0.02, 0.04) * TIME_SCALE

    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.life -= self.decay
        self.size *= 0.98

    def draw(self, surface):
        if self.life > 0:
            s = pygame.Surface((int(self.size*2), int(self.size*2)), pygame.SRCALPHA)
            alpha = int(max(0, self.life * 255))
            pygame.draw.circle(s, (*self.color, alpha), (int(self.size), int(self.size)), int(self.size))
            surface.blit(s, (int(self.x - self.size), int(self.y - self.size)))

class Player:
    def __init__(self):
        self.width = PLAYER_SIZE
        self.height = PLAYER_SIZE
        self.reset()

    def reset(self):
        self.x = (SCREEN_WIDTH - self.width) // 2
        self.y = SCREEN_HEIGHT - self.height
        self.dy = 0
        self.on_ground = True
        self.trail = [] # List of tuples (x, y, alpha)
        self.blink_timer = 0
        self.magnet_timer = 0
        self.has_shield = False
        self.facing_right = True

    def update(self, keys):
        # Magnet
        if self.magnet_timer > 0:
            self.magnet_timer -= 1

        # Trail Capture
        is_moving_x = keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]
        speed_y_threshold = 0.5 
        
        # Add trail only every few frames to prevent solid block effect
        if not hasattr(self, 'trail_timer'): self.trail_timer = 0
        self.trail_timer += 1
        
        if (is_moving_x or abs(self.dy) > speed_y_threshold) and self.trail_timer % 4 == 0:
            self.trail.append([self.x, self.y, 0.3]) # Reduced alpha to 0.3
        
        # Update Trail
        for t in self.trail:
            t[2] -= 0.015 # Slower decay since we spawn fewer
        self.trail = [t for t in self.trail if t[2] > 0]

        # Movement
        if keys[pygame.K_LEFT]:
            self.x -= PLAYER_SPEED
            self.facing_right = False
        if keys[pygame.K_RIGHT]:
            self.x += PLAYER_SPEED
            self.facing_right = True

        # Jump
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP]) and self.on_ground:
            self.dy = -game_jump_force
            self.on_ground = False
            self.blink_timer = 45 # Frames?

        # Physics
        self.dy += game_gravity
        self.y += self.dy

        # Ground Collision
        ground_level = SCREEN_HEIGHT - self.height
        if self.y >= ground_level:
            self.y = ground_level
            self.dy = 0
            self.on_ground = True
            self.blink_timer = 0
        
        # Walls
        if self.x < 0: self.x = 0
        if self.x + self.width > SCREEN_WIDTH: self.x = SCREEN_WIDTH - self.width

        # Blink
        if self.blink_timer > 0:
            self.blink_timer -= 1

    def draw(self, surface):
        # Find skin color
        skin = next((s for s in skins_info if s['id'] == current_skin_id), skins_info[0])
        color = skin['color']

        # Draw Trail
        for t in self.trail:
            tx, ty, alpha = t
            s = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            s.fill((*color, int(alpha * 100))) # 100/255 transparency
            surface.blit(s, (tx, ty))

        # Draw Body
        pygame.draw.rect(surface, color, (self.x, self.y, self.width, self.height))

        # Draw Eyes
        eye_color = COLOR_BLACK
        eye_y = 15 if self.blink_timer > 0 else 12
        eye_h = 2 if self.blink_timer > 0 else 6
        
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RIGHT]:
             pygame.draw.rect(surface, eye_color, (self.x + 35, self.y + eye_y, 6, eye_h))
        elif keys[pygame.K_LEFT]:
             pygame.draw.rect(surface, eye_color, (self.x + 10, self.y + eye_y, 6, eye_h))
        else:
             pygame.draw.rect(surface, eye_color, (self.x + 12, self.y + eye_y, 6, eye_h))
             pygame.draw.rect(surface, eye_color, (self.x + 32, self.y + eye_y, 6, eye_h))

        # Shield Effect
        if self.has_shield:
            center = (self.x + self.width//2, self.y + self.height//2)
            pygame.draw.circle(surface, COLOR_CYAN, center, self.width//1.2, 3)
            # Semi-transparent fill
            s = pygame.Surface((self.width*2, self.height*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*COLOR_CYAN, 50), (self.width, self.height), self.width//1.2)
            surface.blit(s, (center[0]-self.width, center[1]-self.height))

        # Magnet Indicator
        if self.magnet_timer > 0:
            pygame.draw.circle(surface, COLOR_BLUE, (int(self.x + self.width/2), int(self.y - 15)), 5)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

class FallingItem:
    def __init__(self, item_type='coin'):
        self.rect = pygame.Rect(0, -COIN_SIZE, COIN_SIZE, COIN_SIZE)
        self.base_type = item_type if item_type != 'coin' else 'coin_slot'
        self.type = item_type
        self.current_frame = 0
        self.frame_timer = 0
        self.anim_interval = 30 // TIME_SCALE
        self.reset()
    
    def reset(self, others=[]):
        # Determine Type
        if self.base_type == 'coin_slot':
            rand = random.random()
            luck = upgrades_info['luck']['levels'][upgrade_levels['luck']]
            
            if rand < luck:
                 self.type = 'magnet' if random.random() < 0.5 else 'shield'
            else:
                gold_chance = upgrades_info['goldChance']['levels'][upgrade_levels['goldChance']]
                self.type = 'gold_coin' if random.random() < gold_chance else 'silver_coin'
        else:
            self.type = self.base_type

        # Position Logic
        attempts = 0
        while attempts < 50:
            new_x = random.randint(0, SCREEN_WIDTH - COIN_SIZE)
            collision = False
            for o in others:
                if o is self: continue
                if abs(new_x - o.rect.x) < 80: # Min separation
                    collision = True
                    break
            if not collision:
                self.rect.x = new_x
                self.rect.y = -random.randint(50, 450) - COIN_SIZE
                break
            attempts += 1
        
        if attempts >= 50:
            self.rect.x = random.randint(0, SCREEN_WIDTH - COIN_SIZE)
            self.rect.y = -100

        self.current_frame = random.randint(0, resources.get_frame_count() - 1)

    def update(self, player_obj):
        is_coin = self.type in ['gold_coin', 'silver_coin']

        # Animation
        if is_coin:
            self.frame_timer += 1
            if self.frame_timer >= self.anim_interval:
                self.frame_timer = 0
                self.current_frame = (self.current_frame + 1) % resources.get_frame_count()

        # Magnet
        if is_coin and player_obj.magnet_timer > 0 and 0 < self.rect.y < SCREEN_HEIGHT:
            dx = player_obj.x - self.rect.x
            dy = player_obj.y - self.rect.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                self.rect.x += (dx / dist) * 10 * TIME_SCALE
                self.rect.y += (dy / dist) * 10 * TIME_SCALE
        else:
            self.rect.y += COIN_SPEED

        # Reset if off screen
        if self.rect.y > SCREEN_HEIGHT:
            global score
            if is_coin:
                score = max(0, score - 5)
            self.reset()
            # In update loop we need reference to others, but we'll simplify reset here to just work without others checking for off-screen reset

    def draw(self, surface):
        img = None
        if self.type == 'gold_coin':
             img = resources.get_gold(self.current_frame)
        elif self.type == 'silver_coin':
             img = resources.get_silver(self.current_frame)
        
        if img:
            surface.blit(img, (self.rect.x, self.rect.y))
        else:
            # Fallback drawing
            center = (self.rect.x + COIN_RADIUS, self.rect.y + COIN_RADIUS)
            color = COLOR_YELLOW
            text = ""
            if self.type == 'fake': color = COLOR_RED
            elif self.type == 'magnet': 
                color = COLOR_BLUE
                text = "M"
            elif self.type == 'shield': 
                color = COLOR_CYAN
                text = "S"
            elif self.type == 'gold_coin': color = COLOR_YELLOW
            elif self.type == 'silver_coin': color = COLOR_SILVER

            pygame.draw.circle(surface, color, center, COIN_RADIUS)
            # Shine
            pygame.draw.circle(surface, (255, 255, 255, 100), (center[0]-8, center[1]-8), 8)
            
            if text:
                txt_surf = font_medium.render(text, True, COLOR_WHITE)
                surface.blit(txt_surf, (center[0] - txt_surf.get_width()//2, center[1] - txt_surf.get_height()//2))

# --- UI Components ---
class Button:
    def __init__(self, x, y, w, h, text, callback, color=COLOR_WHITE, text_color=COLOR_BLACK, font=font_small):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback
        self.color = color
        self.text_color = text_color
        self.font = font
        self.hovered = False

    def draw(self, surface):
        col = self.color
        if self.hovered:
            # Lighter version
            col = (min(col[0]+30, 255), min(col[1]+30, 255), min(col[2]+30, 255))
        
        pygame.draw.rect(surface, col, self.rect, border_radius=8)
        pygame.draw.rect(surface, (100, 100, 100), self.rect, 2, border_radius=8)
        
        if "\n" in self.text:
             lines = self.text.split("\n")
             y_off = - (len(lines)*10)
             for line in lines:
                 txt = self.font.render(line, True, self.text_color)
                 surface.blit(txt, (self.rect.centerx - txt.get_width()//2, self.rect.centery + y_off))
                 y_off += 20
        else:
            txt = self.font.render(self.text, True, self.text_color)
            surface.blit(txt, (self.rect.centerx - txt.get_width()//2, self.rect.centery - txt.get_height()//2))

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered and self.callback:
                self.callback()

class Slider:
    def __init__(self, x, y, w, min_val, max_val, initial, label):
        self.rect = pygame.Rect(x, y + 20, w, 10)
        self.handle_rect = pygame.Rect(0, 0, 20, 20)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial
        self.label = label
        self.dragging = False
        self.update_handle()

    def update_handle(self):
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        self.handle_rect.centerx = self.rect.x + ratio * self.rect.width
        self.handle_rect.centery = self.rect.centery

    def draw(self, surface):
        # Label
        lbl_surf = font_small.render(f"{self.label}: {self.value:.1f}", True, COLOR_WHITE)
        surface.blit(lbl_surf, (self.rect.x, self.rect.y - 25))
        
        # Track
        pygame.draw.rect(surface, (100, 100, 100), self.rect, border_radius=5)
        # Handle
        col = COLOR_YELLOW if self.dragging else COLOR_WHITE
        pygame.draw.rect(surface, col, self.handle_rect, border_radius=5)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.handle_rect.collidepoint(event.pos):
                self.dragging = True
            elif self.rect.inflate(10, 20).collidepoint(event.pos):
                 self.dragging = True
                 self.update_value(event.pos[0])

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.update_value(event.pos[0])

    def update_value(self, mouse_x):
        rel = mouse_x - self.rect.x
        rel = max(0, min(rel, self.rect.width))
        ratio = rel / self.rect.width
        self.value = self.min_val + ratio * (self.max_val - self.min_val)
        self.update_handle()
        
        global game_gravity, game_jump_force
        if self.label == "Gravity":
            game_gravity = self.value
        elif self.label == "Jump":
            game_jump_force = self.value

# --- Game Logic ---

STATE_MENU = 0
STATE_PLAYING = 1
STATE_GAME_OVER = 2
STATE_SHOP = 3
STATE_SETTINGS = 4

current_state = STATE_PLAYING

player = Player()
particles = []
items = []

# Init items
def init_game():
    global score, particles, items
    score = 0
    player.reset()
    particles = []
    items = []
    # Create coin slots and fakes
    items.append(FallingItem('coin'))
    items.append(FallingItem('coin'))
    items.append(FallingItem('fake'))
    items.append(FallingItem('fake'))
    items.append(FallingItem('fake'))
    # Reset them to scatter
    for i in items:
        i.reset(items)

init_game()

# UI Objects
buttons_shop = []
buttons_settings = []
buttons_gameover = []
buttons_hud = []
sliders = []

def open_shop():
    global current_state, buttons_shop, current_shop_tab
    current_state = STATE_SHOP
    current_shop_tab = 'skins'
    refresh_shop_ui()

def close_shop():
    global current_state
    current_state = STATE_GAME_OVER # Return to where we came from? Or Pause? Usually Game Over.
    # Actually logic says Shop is accessed from Game Over
    
def refresh_shop_ui():
    global buttons_shop
    buttons_shop = []
    
    # Close Button
    buttons_shop.append(Button(SCREEN_WIDTH - 100, 20, 80, 40, "Close", lambda: set_state(STATE_GAME_OVER), COLOR_RED))
    
    # Tabs
    buttons_shop.append(Button(20, 80, 150, 40, "Skins", lambda: set_shop_tab('skins'), COLOR_YELLOW if current_shop_tab == 'skins' else (50,50,50), COLOR_BLACK if current_shop_tab == 'skins' else COLOR_WHITE))
    buttons_shop.append(Button(180, 80, 150, 40, "Upgrades", lambda: set_shop_tab('upgrades'), COLOR_YELLOW if current_shop_tab == 'upgrades' else (50,50,50), COLOR_BLACK if current_shop_tab == 'upgrades' else COLOR_WHITE))

    start_y = 150
    
    if current_shop_tab == 'skins':
        x = 50
        y = start_y
        for skin in skins_info:
            is_owned = skin['owned']
            is_equipped = (current_skin_id == skin['id'])
            
            label = skin['name']
            curr_skin = skin # capture for lambda
            
            def buy_or_equip(s=curr_skin):
                global wallet, current_skin_id
                if s['owned']:
                    current_skin_id = s['id']
                elif wallet >= s['price']:
                    wallet -= s['price']
                    s['owned'] = True
                    # Re-render to show update
                refresh_shop_ui()

            color_border = COLOR_YELLOW if is_equipped else (COLOR_WHITE if is_owned else COLOR_TEXT_GRAY)
            status_text = "Equipped" if is_equipped else ("Owned" if is_owned else f"${skin['price']}")
            
            if is_equipped: btn_col = (50, 50, 20)
            elif is_owned: btn_col = (40, 40, 40)
            else: btn_col = (30, 30, 30)

            btn = Button(x, y, 200, 120, "", buy_or_equip, btn_col)
            buttons_shop.append(btn)
            
            # We will manually draw skin info on top in draw loop or add custom draw instructions?
            # Easiest is to handle raw drawing in main loop if state is Shop.
            
            x += 220
            if x > SCREEN_WIDTH - 250:
                x = 50
                y += 140

    elif current_shop_tab == 'upgrades':
        y = start_y
        for key, info in upgrades_info.items():
            lvl = upgrade_levels[key]
            cost = info['costs'][lvl]
            name = info['name']
            
            def buy_upg(k=key, c=cost):
                global wallet
                if c != "MAX" and wallet >= c:
                    wallet -= c
                    upgrade_levels[k] += 1
                    refresh_shop_ui()
            
            btn_text = "MAX" if cost == "MAX" else f"Buy ${cost}"
            desc = f"{name} (Lv.{lvl+1})\n{info['desc']}"
            
            # Info box (passive)
            # Buy button
            can_buy = (cost != "MAX" and wallet >= cost)
            btn_col = COLOR_YELLOW if can_buy else (100, 100, 100)
            
            # We add a button for the buying action
            buttons_shop.append(Button(600, y, 150, 60, btn_text, buy_upg, btn_col, COLOR_BLACK))
            
            y += 100

def set_shop_tab(tab):
    global current_shop_tab
    current_shop_tab = tab
    refresh_shop_ui()

def open_settings():
    global current_state, sliders, buttons_settings
    current_state = STATE_SETTINGS
    sliders = []
    buttons_settings = []
    
    # Gravity Slider
    sliders.append(Slider(200, 150, 400, 0.1, 1.5, game_gravity, "Gravity"))
    # Jump Slider
    sliders.append(Slider(200, 250, 400, 5, 30, game_jump_force, "Jump"))
    
    # Back Button
    buttons_settings.append(Button(SCREEN_WIDTH//2 - 50, 500, 100, 50, "Back", lambda: set_state(STATE_PLAYING), COLOR_WHITE, COLOR_BLACK))

def set_state(new_state):
    global current_state
    current_state = new_state
    if new_state == STATE_SETTINGS:
        open_settings()
    elif new_state == STATE_SHOP:
        open_shop()
    elif new_state == STATE_PLAYING:
        pass # Unpause logic if needed
    elif new_state == STATE_GAME_OVER:
        create_gameover_ui()

def create_gameover_ui():
    global buttons_gameover
    buttons_gameover = []
    buttons_gameover.append(Button(SCREEN_WIDTH//2 - 110, 400, 100, 50, "Retry", restart_game, COLOR_YELLOW, COLOR_BLACK))
    buttons_gameover.append(Button(SCREEN_WIDTH//2 + 10, 400, 100, 50, "Shop", lambda: set_state(STATE_SHOP), COLOR_WHITE, COLOR_BLACK))

def restart_game():
    init_game()
    set_state(STATE_PLAYING)

# HUD Buttons
buttons_hud.append(Button(SCREEN_WIDTH - 100, 10, 80, 30, "Settings", lambda: set_state(STATE_SETTINGS), (50, 50, 50), COLOR_WHITE, font_tiny))

def update_game_logic():
    if current_state != STATE_PLAYING:
        return

    keys = pygame.key.get_pressed()
    player.update(keys)

    # Particle updates
    for p in particles[:]:
        p.update()
        if p.life <= 0:
            particles.remove(p)

    # Items Update
    player_rect = player.get_rect()
    global score, wallet
    
    for item in items:
        item.update(player)
        # Collision
        if player_rect.colliderect(item.rect):
             # Logic
             if item.type in ['gold_coin', 'silver_coin']:
                 points = 50 if item.type == 'gold_coin' else 10
                 col = COLOR_YELLOW if item.type == 'gold_coin' else COLOR_SILVER
                 score += points
                 create_explosion(item.rect.centerx, item.rect.centery, col)
                 item.reset(items)
             elif item.type == 'magnet':
                 player.magnet_timer = 600
                 create_explosion(item.rect.centerx, item.rect.centery, COLOR_BLUE)
                 item.reset(items)
             elif item.type == 'shield':
                 player.has_shield = True
                 create_explosion(item.rect.centerx, item.rect.centery, COLOR_CYAN)
                 item.reset(items)
             elif item.type == 'fake':
                 if player.has_shield:
                     player.has_shield = False
                     create_explosion(item.rect.centerx, item.rect.centery, COLOR_WHITE)
                     item.reset(items)
                 else:
                     # Game Over
                     game_over_process()

def create_explosion(x, y, color):
    for _ in range(12):
        particles.append(Particle(x, y, color))

def game_over_process():
    global wallet
    # Calculate earnings
    mult = upgrades_info['multiplier']['levels'][upgrade_levels['multiplier']]
    earned = int(score * mult)
    wallet += earned
    set_state(STATE_GAME_OVER)

# --- Draw Functions ---

def draw_hud(surface):
    # Score
    txt = font_medium.render(f"Score: {score}", True, COLOR_WHITE)
    surface.blit(txt, (20, 20))
    
    # Wallet
    txt_w = font_medium.render(f"$ {wallet}", True, COLOR_YELLOW)
    surface.blit(txt_w, (20, 60))
    
    # Multiplier
    mult = upgrades_info['multiplier']['levels'][upgrade_levels['multiplier']]
    txt_m = font_tiny.render(f"x{mult}", True, COLOR_TEXT_GRAY)
    surface.blit(txt_m, (200, 25))

    for btn in buttons_hud:
        btn.draw(surface)

def draw_shop_content(surface):
    # Wallet in shop
    txt = font_large.render(f"Wallet: ${wallet}", True, COLOR_YELLOW)
    surface.blit(txt, (SCREEN_WIDTH - 300, 20))

    if current_shop_tab == 'skins':
        x = 50
        y = 150
        for skin in skins_info:
            # Draw Skin Preview inside its zone
            # We can find the button corresponding to this skin?
            # Let's just overlay previews based on calculated positions (same as in create_ui)
            
            # Preview Box
            pygame.draw.rect(surface, skin['color'], (x + 75, y + 20, 50, 50))
            
            name_txt = font_small.render(skin['name'], True, COLOR_WHITE)
            surface.blit(name_txt, (x + 100 - name_txt.get_width()//2, y + 80))
            
            x += 220
            if x > SCREEN_WIDTH - 250:
                x = 50
                y += 140

    elif current_shop_tab == 'upgrades':
        y = 150
        for key, info in upgrades_info.items():
            lvl = upgrade_levels[key]
            
            # Info Text
            name_txt = font_medium.render(f"{info['name']} (Lv {lvl+1})", True, COLOR_YELLOW)
            surface.blit(name_txt, (50, y))
            
            desc_txt = font_small.render(info['desc'], True, COLOR_TEXT_GRAY)
            surface.blit(desc_txt, (50, y + 35))
            
            val = info['levels'][lvl]
            if key == 'goldChance' or key == 'luck': val = f"{int(val*100)}%"
            else: val = f"x{val}"
            
            curr_txt = font_small.render(f"Current: {val}", True, COLOR_WHITE)
            surface.blit(curr_txt, (50, y + 60))
            
            y += 100

def draw():
    screen.fill(COLOR_BG)
    
    if current_state == STATE_PLAYING or current_state == STATE_SETTINGS:
        # Game layer
        items_to_draw = items
        # Draw game elements even in settings for preview (optional)
        player.draw(screen)
        for i in items:
            i.draw(screen)
        for p in particles:
            p.draw(screen)
        
        # HUD
        if current_state == STATE_PLAYING:
            draw_hud(screen)

    if current_state == STATE_SETTINGS:
        # Dim background
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        s.set_alpha(200)
        s.fill((0,0,0))
        screen.blit(s, (0,0))
        
        # Title
        t = font_large.render("Settings", True, COLOR_WHITE)
        screen.blit(t, (SCREEN_WIDTH//2 - t.get_width()//2, 50))
        
        for sl in sliders:
            sl.draw(screen)
        for btn in buttons_settings:
            btn.draw(screen)

    elif current_state == STATE_GAME_OVER:
        # Draw game in background frozen? logic continues but we draw simple
        player.draw(screen) 
        
        # Overlay
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        s.set_alpha(200)
        s.fill((0,0,0))
        screen.blit(s, (0,0))
        
        t = font_large.render("GAME OVER", True, COLOR_RED)
        screen.blit(t, (SCREEN_WIDTH//2 - t.get_width()//2, 150))
        
        st = font_medium.render(f"Final Score: {score}", True, COLOR_WHITE)
        screen.blit(st, (SCREEN_WIDTH//2 - st.get_width()//2, 230))
        
        mult = upgrades_info['multiplier']['levels'][upgrade_levels['multiplier']]
        earned = int(score * mult)
        
        et = font_medium.render(f"Earnings: +{earned} (x{mult})", True, COLOR_YELLOW)
        screen.blit(et, (SCREEN_WIDTH//2 - et.get_width()//2, 280))

        for btn in buttons_gameover:
            btn.draw(screen)

    elif current_state == STATE_SHOP:
        screen.fill((30, 30, 30))
        t = font_large.render("Item Shop", True, COLOR_WHITE)
        screen.blit(t, (20, 20))
        
        for btn in buttons_shop:
            btn.draw(screen)

        draw_shop_content(screen)

    pygame.display.flip()

# --- Main Loop ---
running = True
while running:
    # 1. Events
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            running = False
        
        # Pass events to UI
        if current_state == STATE_SHOP:
            for btn in buttons_shop:
                btn.handle_event(event)

        elif current_state == STATE_SETTINGS:
            for btn in buttons_settings:
                btn.handle_event(event)
            for sl in sliders:
                sl.handle_event(event)

        elif current_state == STATE_GAME_OVER:
            for btn in buttons_gameover:
                btn.handle_event(event)

        elif current_state == STATE_PLAYING:
            for btn in buttons_hud:
                btn.handle_event(event)

    # 2. Update
    update_game_logic()
    
    # 3. Draw
    draw()
    
    # 4. Clock
    clock.tick(TARGET_FPS)

pygame.quit()
sys.exit()
