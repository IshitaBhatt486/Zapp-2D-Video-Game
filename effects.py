"""Small pixel particles and shock rings for hit feedback."""
import math
import random
import pygame
from settings import *

class Particle:
    def __init__(self, x, y, color, power=1.0):
        angle = random.random() * math.tau
        speed = random.uniform(45, 210) * power
        self.x, self.y = float(x), float(y)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.color = color
        self.size = random.choice((2, 3, 4)) if power < 1.5 else random.choice((3, 4, 5))
        self.life = random.uniform(0.22, 0.55) * min(power, 1.8)
        self.max_life = self.life

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 85 * dt
        self.life -= dt

    def draw(self, surface):
        if self.life <= 0:
            return
        scale = max(0.2, self.life / self.max_life)
        size = max(1, round(self.size * scale))
        pygame.draw.rect(surface, self.color, (round(self.x), round(self.y), size, size))

class ShockRing:
    def __init__(self, x, y, color, power=1.0):
        self.x, self.y = int(x), int(y)
        self.color = color
        self.age = 0.0
        self.duration = 0.28 * min(power, 1.8)
        self.max_radius = 18 * power

    def update(self, dt):
        self.age += dt

    def draw(self, surface):
        if self.age >= self.duration:
            return
        t = self.age / self.duration
        radius = max(1, int(self.max_radius * t))
        width = 3 if t < 0.5 else 1
        pygame.draw.circle(surface, self.color, (self.x, self.y), radius, width)

class Effects:
    def __init__(self):
        self.particles = []
        self.rings = []

    def burst(self, x, y, big=False, colors=None):
        colors = colors or (CYAN, WHITE, PURPLE, PINK, YELLOW)
        count = 42 if big else 13
        power = 1.7 if big else 1.0
        self.particles.extend(Particle(x, y, random.choice(colors), power) for _ in range(count))
        self.rings.append(ShockRing(x, y, random.choice(colors), power))

    def sparks(self, x, y, colors=None):
        colors = colors or (CYAN, WHITE, YELLOW)
        self.particles.extend(Particle(x, y, random.choice(colors), 0.65) for _ in range(5))

    def update(self, dt):
        for p in self.particles:
            p.update(dt)
        for ring in self.rings:
            ring.update(dt)
        self.particles = [p for p in self.particles if p.life > 0]
        self.rings = [r for r in self.rings if r.age < r.duration]

    def draw(self, surface):
        for ring in self.rings:
            ring.draw(surface)
        for particle in self.particles:
            particle.draw(surface)

    def clear(self):
        self.particles.clear()
        self.rings.clear()
