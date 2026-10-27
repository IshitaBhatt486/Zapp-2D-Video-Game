import json
import random
import pygame

from settings import *
from entities import Player, Enemy, Boss, Bullet, PowerUp, load_image
from effects import Effects
from audio import Audio
from ui import draw_background, draw_hud, draw_boss_bar, panel, text

pygame.init()
display = pygame.display.set_mode((WIDTH, HEIGHT))
canvas = pygame.Surface((WIDTH, HEIGHT))
pygame.display.set_caption(TITLE)
pygame.mouse.set_visible(True)
try:
    icon = pygame.image.load(str(ASSET_DIR / "spaceship.png"))
    pygame.display.set_icon(icon)
except (pygame.error, FileNotFoundError, OSError):
    pass
clock = pygame.time.Clock()
audio = Audio()
effects = Effects()
title_ship = load_image("spaceship.png", (52, 43))

# Each star stores x, y, size, speed, brightness, phase.
stars = [(random.randrange(WIDTH), random.randrange(HEIGHT), random.choice((1, 2, 2, 3)),
          random.randrange(10, 55), random.randrange(80, 180), random.random() * 6.28)
         for _ in range(105)]
elapsed = 0.0
state = "menu"


def load_best():
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as file:
            return max(0, int(json.load(file).get("best", 0)))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return 0


def save_best(value):
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as file:
            json.dump({"best": int(value)}, file)
    except OSError:
        pass


best_score = load_best()

def make_enemies(wave):
    rows = min(3 + (wave - 1) // 3, 5)
    cols = min(7 + (wave - 1) // 4, 10)
    formation_width = (cols - 1) * ENEMY_GAP_X + 36
    left = (WIDTH - formation_width) // 2
    enemies = []
    for row in range(rows):
        for col in range(cols):
            enemies.append(Enemy(left + col * ENEMY_GAP_X, 112 + row * ENEMY_GAP_Y, row))
    return enemies


def configure_wave(game_state, wave):
    if wave % BOSS_EVERY_WAVES == 0:
        game_state["enemies"] = []
        game_state["boss"] = Boss(wave)
        audio.play("boss")
    else:
        game_state["enemies"] = make_enemies(wave)
        game_state["boss"] = None


def reset_game():
    result = {
        "player": Player(), "wave": 1, "score": 0,
        "enemies": [], "boss": None, "bullets": [], "enemy_bullets": [],
        "powerups": [], "power_timer": 0.0, "enemy_direction": 1,
        "enemy_shot_timer": 1.1, "wave_banner": 1.5,
        "shake_timer": 0.0, "shake_strength": 0,
    }
    configure_wave(result, 1)
    return result


game = reset_game()


def shake(power=5, duration=0.12):
    game["shake_timer"] = max(game["shake_timer"], duration)
    game["shake_strength"] = max(game["shake_strength"], power)


def record_score():
    global best_score
    if game["score"] > best_score:
        best_score = game["score"]
        save_best(best_score)


def advance_wave():
    game["wave"] += 1
    game["bullets"].clear()
    game["enemy_bullets"].clear()
    game["enemy_shot_timer"] = 0.85
    game["wave_banner"] = 1.65
    configure_wave(game, game["wave"])
    audio.play("wave")


def update_playing(dt):
    global state
    player = game["player"]
    keys = pygame.key.get_pressed()
    player.update(dt, keys)
    game["power_timer"] = max(0.0, game["power_timer"] - dt)

    if keys[pygame.K_SPACE] and player.can_shoot():
        game["bullets"].extend(player.shoot(game["power_timer"] > 0))
        audio.play("shoot")

    # The boss has its own movement and a three-projectile spread attack.
    boss = game["boss"]
    if boss:
        boss.update(dt)
        if boss.shot_timer <= 0:
            game["enemy_bullets"].extend(boss.shots())
            audio.play("hit")
    else:
        enemies = game["enemies"]
        if enemies:
            speed = 45 + game["wave"] * 6
            dx = game["enemy_direction"] * speed * dt
            edge_hit = any(e.rect.left + dx < 14 or e.rect.right + dx > WIDTH - 14 for e in enemies)
            if edge_hit:
                game["enemy_direction"] *= -1
                for enemy in enemies:
                    enemy.rect.y += ENEMY_DROP
            else:
                for enemy in enemies:
                    enemy.rect.x = round(enemy.rect.x + dx)
            for enemy in enemies:
                enemy.update(dt)
                if enemy.rect.bottom >= player.rect.top:
                    state = "lost"
                    audio.play("damage")
                    record_score()
                    return

        game["enemy_shot_timer"] -= dt
        if enemies and game["enemy_shot_timer"] <= 0:
            shooter = random.choice(enemies)
            game["enemy_bullets"].append(Bullet(shooter.rect.centerx, shooter.rect.bottom,
                                                  ENEMY_BULLET_SPEED, False))
            game["enemy_shot_timer"] = max(0.34, 1.25 - game["wave"] * 0.045) * random.uniform(0.72, 1.18)

    for bullet in game["bullets"] + game["enemy_bullets"]:
        bullet.update(dt)
    game["bullets"] = [b for b in game["bullets"] if b.alive]
    game["enemy_bullets"] = [b for b in game["enemy_bullets"] if b.alive]

    # Player fire versus boss.
    boss = game["boss"]
    if boss:
        defeated = False
        for bullet in game["bullets"]:
            if bullet.alive and bullet.rect.colliderect(boss.rect):
                bullet.alive = False
                boss.health -= 1
                boss.flash = 0.13
                game["score"] += 25 * game["wave"]
                effects.sparks(bullet.rect.centerx, bullet.rect.centery, (CYAN, WHITE, YELLOW))
                audio.play("hit")
                if boss.health <= 0:
                    effects.burst(boss.rect.centerx, boss.rect.centery, big=True,
                                  colors=(PINK, PURPLE, CYAN, YELLOW, WHITE))
                    effects.burst(boss.rect.left + 24, boss.rect.centery, big=True,
                                  colors=(PINK, PURPLE, YELLOW))
                    game["score"] += 500 * game["wave"]
                    game["boss"] = None
                    defeated = True
                    audio.play("explode")
                    shake(11, 0.32)
                    break
        game["bullets"] = [b for b in game["bullets"] if b.alive]
        if defeated:
            record_score()
            advance_wave()
            return
    else:
        # Regular enemies take one hit; defeated enemies burst into pixels.
        for bullet in game["bullets"]:
            if not bullet.alive:
                continue
            for enemy in game["enemies"]:
                if enemy.alive and bullet.rect.colliderect(enemy.rect):
                    bullet.alive = False
                    enemy.alive = False
                    game["score"] += 10 * game["wave"]
                    effects.burst(enemy.rect.centerx, enemy.rect.centery,
                                  colors=(CYAN, PURPLE, PINK, WHITE))
                    audio.play("explode")
                    shake(2, 0.06)
                    if random.random() < 0.13:
                        game["powerups"].append(PowerUp(enemy.rect.centerx, enemy.rect.centery))
                    break
        game["enemies"] = [e for e in game["enemies"] if e.alive]
        game["bullets"] = [b for b in game["bullets"] if b.alive]

        if not game["enemies"]:
            record_score()
            advance_wave()
            return

    # An enemy projectile damages the player, followed by brief invulnerability.
    if player.invulnerable <= 0:
        for bullet in game["enemy_bullets"]:
            if bullet.rect.colliderect(player.rect):
                bullet.alive = False
                player.lives -= 1
                player.invulnerable = 1.3
                effects.burst(player.rect.centerx, player.rect.centery, colors=(PINK, RED, WHITE))
                audio.play("damage")
                shake(7, 0.18)
                if player.lives <= 0:
                    state = "lost"
                    record_score()
                break
    game["enemy_bullets"] = [b for b in game["enemy_bullets"] if b.alive]

    for powerup in game["powerups"]:
        powerup.update(dt)
        if powerup.rect.colliderect(player.rect):
            powerup.alive = False
            game["power_timer"] = 8.0
            effects.burst(powerup.rect.centerx, powerup.rect.centery, colors=(YELLOW, GREEN, CYAN))
            audio.play("powerup")
    game["powerups"] = [p for p in game["powerups"] if p.alive]
    game["wave_banner"] = max(0.0, game["wave_banner"] - dt)
    game["shake_timer"] = max(0.0, game["shake_timer"] - dt)
    if game["shake_timer"] <= 0:
        game["shake_strength"] = 0
    record_score()


running = True
while running:
    dt = min(clock.tick(FPS) / 1000.0, 0.04)
    elapsed += dt

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_m:
                audio.toggle_music()
            elif event.key == pygame.K_ESCAPE:
                if state == "playing":
                    state = "paused"
                    audio.pause_music()
                elif state == "paused":
                    state = "playing"
                    audio.resume_music()
                elif state in ("lost", "won"):
                    state = "menu"
            elif state == "menu" and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                game = reset_game()
                effects.clear()
                state = "playing"
                audio.resume_music()
            elif state in ("lost", "won") and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                game = reset_game()
                effects.clear()
                state = "playing"
                audio.resume_music()
            elif state == "paused" and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                state = "playing"
                audio.resume_music()

    draw_background(canvas, stars, elapsed)
    if state == "playing":
        update_playing(dt)

    # Render the current scene. Effects continue animating in menus and overlays too.
    effects.update(dt)
    if state != "menu":
        for powerup in game["powerups"]:
            powerup.draw(canvas)
        for enemy in game["enemies"]:
            enemy.draw(canvas)
        if game["boss"]:
            game["boss"].draw(canvas)
        for bullet in game["bullets"] + game["enemy_bullets"]:
            bullet.draw(canvas)
        game["player"].draw(canvas)
        effects.draw(canvas)
        draw_hud(canvas, game["score"], game["wave"], game["player"].lives, best_score,
                 game["power_timer"] > 0)
        draw_boss_bar(canvas, game["boss"])
        if game["wave_banner"] > 0 and state == "playing":
            label = "BOSS INCOMING" if game["boss"] else f"WAVE {game['wave']}"
            tint = PINK if game["boss"] else WHITE
            text(canvas, label, 28, tint, (WIDTH // 2, 207 if game["boss"] else 94), center=True, bold=True)

    if state == "menu":
        text(canvas, "zapp!!", 70, CYAN, (WIDTH // 2, 172), center=True, bold=True)
        text(canvas, "SPACE ARCADE", 20, PURPLE, (WIDTH // 2, 229), center=True, bold=True)
        text(canvas, "A hostile enemy is approaching.", 18, WHITE, (WIDTH // 2, 291), center=True)
        text(canvas, "PRESS ENTER TO DEPLOY", 18, YELLOW, (WIDTH // 2, 365), center=True, bold=True)
        text(canvas, "MOVE  A / D or LEFT / RIGHT     FIRE  SPACE     PAUSE  ESC", 13, MUTED,
             (WIDTH // 2, 430), center=True)
        text(canvas, f"PERSONAL BEST  {best_score:06d}", 15, MUTED, (WIDTH // 2, 465), center=True)
        text(canvas, "M  TOGGLE MUSIC", 13, MUTED, (WIDTH // 2, 491), center=True)
        # Decorative pixel ships in the title screen.
        if title_ship:
            canvas.blit(title_ship, (WIDTH // 2 - 26, 94))
    elif state == "paused":
        panel(canvas, "PAUSED", "", "Press ENTER or ESC to resume", PURPLE)
    elif state == "lost":
        panel(canvas, "SHIP LOST", f"FINAL SCORE  {game['score']}", "ENTER: retry     ESC: main menu", PINK)
    elif state == "won":
        panel(canvas, "SECTOR CLEARED", f"FINAL SCORE  {game['score']}", "ENTER: play again     ESC: main menu", GREEN)

    # The camera shake is applied to the finished frame, so all elements move together.
    display.fill(BG)
    offset_x = offset_y = 0
    if state == "playing" and game["shake_timer"] > 0:
        strength = game["shake_strength"]
        offset_x = random.randint(-strength, strength)
        offset_y = random.randint(-strength, strength)
    display.blit(canvas, (offset_x, offset_y))
    pygame.display.flip()

pygame.quit()
