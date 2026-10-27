import math
import random
import pygame
from settings import *

_IMAGE_CACHE = {}

def load_image(filename, size=None):
    """Load an asset if available; callers have vector fallbacks."""
    key = (filename, size)
    if key in _IMAGE_CACHE:
        return _IMAGE_CACHE[key]
    try:
        image = pygame.image.load(str(ASSET_DIR / filename)).convert_alpha()
        if size:
            # Nearest-neighbour scaling keeps the sprite art crisp.
            image = pygame.transform.scale(image, size)
        _IMAGE_CACHE[key] = image
        return image
    except (pygame.error, FileNotFoundError, OSError):
        _IMAGE_CACHE[key] = None
        return None

class Bullet:
    def __init__(self, x, y, velocity_y, friendly=True, velocity_x=0):
        self.rect = pygame.Rect(0, 0, 6 if friendly else 8, 17 if friendly else 14)
        self.rect.center = (int(x), int(y))
        self.x = float(x)
        self.y = float(y)
        self.velocity_x = float(velocity_x)
        self.velocity_y = float(velocity_y)
        self.friendly = friendly
        self.alive = True

    def update(self, dt):
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt
        self.rect.center = (round(self.x), round(self.y))
        if self.rect.bottom < -12 or self.rect.top > HEIGHT + 12 or self.rect.right < 0 or self.rect.left > WIDTH:
            self.alive = False

    def draw(self, surface):
        if self.friendly:
            pygame.draw.rect(surface, CYAN, self.rect, border_radius=3)
            pygame.draw.rect(surface, WHITE, self.rect.inflate(-3, -5), border_radius=2)
        else:
            pygame.draw.rect(surface, PINK, self.rect, border_radius=3)
            pygame.draw.rect(surface, YELLOW, self.rect.inflate(-4, -7), border_radius=2)

class Player:
    def __init__(self):
        self.rect = pygame.Rect(WIDTH // 2 - 22, HEIGHT - 76, 44, 36)
        self.speed = PLAYER_SPEED
        self.cooldown = 0.0
        self.lives = PLAYER_LIVES
        self.invulnerable = 0.0
        self.image = load_image("spaceship.png", self.rect.size)

    def update(self, dt, keys):
        right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        direction = int(bool(right)) - int(bool(left))
        self.rect.x = round(self.rect.x + direction * self.speed * dt)
        self.rect.clamp_ip(pygame.Rect(12, 54, WIDTH - 24, HEIGHT - 54))
        self.cooldown = max(0.0, self.cooldown - dt)
        self.invulnerable = max(0.0, self.invulnerable - dt)

    def can_shoot(self):
        return self.cooldown <= 0

    def shoot(self, powered=False):
        self.cooldown = PLAYER_FIRE_DELAY * (0.64 if powered else 1.0)
        if powered:
            return [
                Bullet(self.rect.centerx - 13, self.rect.top, -BULLET_SPEED),
                Bullet(self.rect.centerx, self.rect.top - 5, -BULLET_SPEED * 1.07),
                Bullet(self.rect.centerx + 13, self.rect.top, -BULLET_SPEED),
            ]
        return [Bullet(self.rect.centerx, self.rect.top, -BULLET_SPEED)]

    def draw(self, surface):
        if self.invulnerable > 0 and int(self.invulnerable * 14) % 2 == 0:
            return
        if self.image:
            surface.blit(self.image, self.rect)
            return
        x, y = self.rect.centerx, self.rect.centery
        points = [(x, self.rect.top), (self.rect.left, self.rect.bottom),
                  (x, self.rect.bottom - 8), (self.rect.right, self.rect.bottom)]
        pygame.draw.polygon(surface, CYAN, points)
        pygame.draw.polygon(surface, WHITE, [(x, y - 6), (x - 5, y + 6), (x + 5, y + 6)])

class Enemy:
    def __init__(self, x, y, row):
        self.rect = pygame.Rect(x, y, 36, 29)
        self.row = row
        self.phase = random.random() * math.tau
        self.alive = True
        self.image = load_image(f"enemy_{row % 3}.png", self.rect.size)
        if self.image is None:
            self.image = load_image("ghost.png", self.rect.size)

    def update(self, dt):
        self.phase += dt * 3.2
        self.draw_y = self.rect.y + math.sin(self.phase) * 2

    def draw(self, surface):
        y = int(getattr(self, "draw_y", self.rect.y))
        if self.image:
            surface.blit(self.image, (self.rect.x, y))
            return
        color = (PINK, PURPLE, CYAN)[self.row % 3]
        x, w, h = self.rect.x, self.rect.w, self.rect.h
        pygame.draw.rect(surface, color, (x + 4, y, w - 8, h - 5), border_radius=5)
        pygame.draw.rect(surface, color, (x, y + 8, w, h - 12), border_radius=4)
        pygame.draw.circle(surface, WHITE, (x + 12, y + 11), 4)
        pygame.draw.circle(surface, WHITE, (x + 24, y + 11), 4)
        for foot_x in (x + 7, x + 18, x + 28):
            pygame.draw.rect(surface, color, (foot_x, y + h - 5, 5, 7), border_radius=2)

class Boss:
    """A large mothership with a sweeping movement pattern and multi-shot attacks."""
    def __init__(self, wave):
        self.rect = pygame.Rect(WIDTH // 2 - 64, 112, 128, 72)
        self.x = float(self.rect.x)
        self.direction = 1
        self.speed = 145 + wave * 7
        self.phase = 0.0
        self.health = 14 + wave * 2
        self.max_health = self.health
        self.shot_timer = 0.9
        self.flash = 0.0
        self.image = load_image("boss.png", self.rect.size)

    def update(self, dt):
        self.phase += dt
        self.x += self.direction * self.speed * dt
        if self.rect.left < 14:
            self.x = 14
            self.direction = 1
        elif self.rect.right > WIDTH - 14:
            self.x = WIDTH - self.rect.width - 14
            self.direction = -1
        self.rect.x = round(self.x)
        self.rect.y = round(105 + math.sin(self.phase * 1.8) * 15)
        self.shot_timer -= dt
        self.flash = max(0.0, self.flash - dt)

    def shots(self):
        self.shot_timer = max(0.48, 1.0 - self.max_health * 0.006) * random.uniform(0.82, 1.15)
        x, y = self.rect.centerx, self.rect.bottom - 6
        return [
            Bullet(x - 22, y, ENEMY_BULLET_SPEED * 0.88, False, -115),
            Bullet(x, y, ENEMY_BULLET_SPEED * 1.05, False, 0),
            Bullet(x + 22, y, ENEMY_BULLET_SPEED * 0.88, False, 115),
        ]

    def draw(self, surface):
        if self.image:
            surface.blit(self.image, self.rect)
        else:
            x, y, w, h = self.rect
            pygame.draw.polygon(surface, PURPLE, [(x, y + 22), (x + 26, y + 5), (x + 48, y + 17),
                                                  (x + 64, y), (x + 80, y + 17), (x + 102, y + 5),
                                                  (x + w, y + 22), (x + w - 18, y + h - 5),
                                                  (x + 18, y + h - 5)])
            pygame.draw.rect(surface, CYAN, (x + 46, y + 23, 36, 20), border_radius=4)
            pygame.draw.rect(surface, PINK, (x + 8, y + 34, 18, 8))
            pygame.draw.rect(surface, PINK, (x + w - 26, y + 34, 18, 8))
        if self.flash > 0 and int(self.flash * 40) % 2 == 0:
            flash = pygame.Surface(self.rect.size, pygame.SRCALPHA)
            flash.fill((255, 255, 255, 95))
            surface.blit(flash, self.rect.topleft)

class PowerUp:
    def __init__(self, x, y):
        self.rect = pygame.Rect(int(x) - 10, int(y) - 10, 20, 20)
        self.y = float(self.rect.y)
        self.speed = 125
        self.phase = 0.0
        self.alive = True

    def update(self, dt):
        self.y += self.speed * dt
        self.phase += dt * 5
        self.rect.y = round(self.y)
        if self.rect.top > HEIGHT:
            self.alive = False

    def draw(self, surface):
        pulse = 2 if int(self.phase * 3) % 2 == 0 else 0
        pygame.draw.rect(surface, YELLOW, self.rect.inflate(pulse, pulse), border_radius=4)
        pygame.draw.rect(surface, BG, self.rect.inflate(-6, -6), border_radius=2)
        pygame.draw.line(surface, YELLOW, (self.rect.centerx, self.rect.top + 4),
                         (self.rect.centerx, self.rect.bottom - 4), 3)
        pygame.draw.line(surface, YELLOW, (self.rect.left + 4, self.rect.centery),
                         (self.rect.right - 4, self.rect.centery), 3)
