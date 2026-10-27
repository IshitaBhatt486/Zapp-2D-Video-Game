import math
import pygame
from settings import *

_FONT_CACHE = {}
def font(size, bold=False):
    key = (size, bold)
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = pygame.font.SysFont("consolas", size, bold=bold)
    return _FONT_CACHE[key]

def text(surface, value, size, color, pos, center=False, bold=False):
    image = font(size, bold).render(str(value), True, color)
    rect = image.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos
    surface.blit(image, rect)
    return rect

_GLOW = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
pygame.draw.circle(_GLOW, (40, 29, 99, 27), (WIDTH // 2, HEIGHT // 3), 275)

def draw_background(surface, stars, elapsed):
    surface.fill(BG)
    surface.blit(_GLOW, (0, 0))
    # A faint arcade grid gives the scene depth without clutter.
    grid = (18, 23, 48)
    for x in range(0, WIDTH, 60):
        pygame.draw.line(surface, grid, (x, 54), (x, HEIGHT), 1)
    for y in range(72, HEIGHT, 60):
        pygame.draw.line(surface, grid, (0, y), (WIDTH, y), 1)
    for x, y, radius, speed, brightness, phase in stars:
        yy = (y + elapsed * speed) % HEIGHT
        pulse = 0.75 + 0.25 * math.sin(elapsed * 2 + phase)
        c = max(45, min(230, int(brightness * pulse)))
        pygame.draw.rect(surface, (c, min(255, c + 22), min(255, c + 50)),
                         (int(x), int(yy), radius, radius))

def draw_hud(surface, score, wave, lives, best, powered):
    pygame.draw.rect(surface, PANEL, (0, 0, WIDTH, 54))
    pygame.draw.line(surface, (46, 58, 100), (0, 53), (WIDTH, 53), 2)
    text(surface, "zapp!!", 21, CYAN, (20, 15), bold=True)
    text(surface, f"SCORE {score:06d}", 17, WHITE, (180, 18))
    text(surface, f"WAVE {wave:02d}", 17, PURPLE, (378, 18))
    text(surface, f"BEST {best:06d}", 15, MUTED, (520, 19))
    text(surface, "HULL", 12, MUTED, (714, 8))
    for i in range(lives):
        x = 722 + i * 28
        pygame.draw.polygon(surface, PINK, [(x + 8, 18), (x, 34), (x + 16, 34)])
        pygame.draw.rect(surface, CYAN, (x + 5, 26, 6, 5))
    if powered:
        text(surface, "TRIPLE SHOT", 12, YELLOW, (WIDTH - 135, 39))

def draw_boss_bar(surface, boss):
    if boss is None:
        return
    width = 360
    x = (WIDTH - width) // 2
    y = 66
    text(surface, "MOTHERSHIP", 12, PINK, (WIDTH // 2, y - 3), center=True, bold=True)
    track = pygame.Rect(x, y + 13, width, 8)
    pygame.draw.rect(surface, (44, 31, 67), track, border_radius=3)
    fill = track.copy()
    fill.width = max(0, round(track.width * boss.health / boss.max_health))
    if fill.width:
        pygame.draw.rect(surface, PINK, fill, border_radius=3)
    pygame.draw.rect(surface, (95, 63, 113), track, width=1, border_radius=3)

def panel(surface, title, subtitle, hint=None, accent=CYAN):
    shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    shade.fill((3, 5, 16, 198))
    surface.blit(shade, (0, 0))
    box = pygame.Rect(WIDTH // 2 - 250, HEIGHT // 2 - 155, 500, 310)
    pygame.draw.rect(surface, PANEL, box, border_radius=8)
    pygame.draw.rect(surface, (58, 80, 133), box, width=2, border_radius=8)
    pygame.draw.line(surface, accent, (box.x + 22, box.y + 18), (box.right - 22, box.y + 18), 3)
    text(surface, title, 38, accent, (WIDTH // 2, HEIGHT // 2 - 78), center=True, bold=True)
    text(surface, subtitle, 18, WHITE, (WIDTH // 2, HEIGHT // 2 - 18), center=True)
    if hint:
        text(surface, hint, 14, MUTED, (WIDTH // 2, HEIGHT // 2 + 67), center=True)
