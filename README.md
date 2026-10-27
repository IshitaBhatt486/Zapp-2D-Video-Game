# zapp!! Arcade Space 2D Video Game

An arcade shooter 2D video game made with Python and Pygame, with pixel-art sprites, animated explosions, retro sound effects, enemy waves, power-ups, and a mothership boss fight.

## Features

- Pixel-art-inspired player, enemies, and boss
- Animated pixel explosions, spark bursts, shock rings, and screen shake
- looping background music, plus retro sound effects
- Start menu, pause menu, HUD, and persistent local high score
- Enemy formations, enemy projectiles, player lives, and temporary triple-shot power-up
- A mothership boss every fourth wave, with a health bar and three-way projectile attacks
- Increasing enemy count and difficulty as the waves progress
- Vector-style fallbacks if sprite files are missing
- Press `M` to toggle background music; music pauses while the game is paused

## Requirements

- Python 3.10+
- Pygame 2.x

Install Pygame from your terminal:

```bash
python -m pip install pygame
```

On Windows, you can also try `py -m pip install pygame`. If your device blocks package installation with a Windows Application Control policy, use an approved Python environment or contact your administrator rather than bypassing the restriction.

## Run

Open the terminal in the extracted `space-game` folder and run:

```bash
python main.py
```

Or, on Windows:

```bash
py main.py
```

## Controls

- Move: `A` / `D` or Left / Right arrows
- Fire: hold `Space`
- Pause / resume: `Esc`
- Toggle background music: `M`
- Start / restart: `Enter`

## Project structure

- `main.py` — game loop, states, wave progression, collision handling, and score persistence
- `settings.py` — dimensions, colors, movement values, and paths
- `entities.py` — player, bullets, enemies, mothership boss, and power-up
- `effects.py` — explosions, shock rings, pixel particles, and sparks
- `audio.py` — sound-effect loading and background-music controls
- `ui.py` — starfield, HUD, boss health bar, and menus
- `assets/` — sprite PNGs and WAV sound/music assets

The game stores its best score in `highscore.json` in this folder.
