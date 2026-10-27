"""Original looping soundtrack and sound-effect loader for zapp!!."""
import pygame
from settings import ASSET_DIR

class Audio:
    def __init__(self):
        self.sounds = {}
        self.enabled = False
        self.music_loaded = False
        self.music_enabled = True
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            for name in ("shoot", "hit", "explode", "powerup", "damage", "boss", "wave"):
                path = ASSET_DIR / "sounds" / f"{name}.wav"
                try:
                    sound = pygame.mixer.Sound(str(path))
                    sound.set_volume(0.32 if name == "shoot" else 0.5)
                    self.sounds[name] = sound
                except (pygame.error, OSError):
                    pass
            music_path = ASSET_DIR / "sounds" / "background_music.wav"
            try:
                pygame.mixer.music.load(str(music_path))
                pygame.mixer.music.set_volume(0.13)  # intentionally subtle background level
                pygame.mixer.music.play(-1)
                self.music_loaded = True
            except (pygame.error, OSError):
                # Gameplay and sound effects still work if the music file is unavailable.
                self.music_loaded = False
            self.enabled = True
        except (pygame.error, OSError):
            # Some machines have no audio device; do not block game startup.
            self.enabled = False

    def play(self, name):
        sound = self.sounds.get(name)
        if sound:
            try:
                sound.play()
            except pygame.error:
                pass

    def pause_music(self):
        if self.enabled and self.music_loaded and self.music_enabled:
            try:
                pygame.mixer.music.pause()
            except pygame.error:
                pass

    def resume_music(self):
        if self.enabled and self.music_loaded and self.music_enabled:
            try:
                pygame.mixer.music.unpause()
            except pygame.error:
                pass

    def toggle_music(self):
        self.music_enabled = not self.music_enabled
        if not (self.enabled and self.music_loaded):
            return
        try:
            if self.music_enabled:
                pygame.mixer.music.set_volume(0.13)
                # Restart the loop if it was stopped by the toggle.
                pygame.mixer.music.play(-1)
            else:
                pygame.mixer.music.stop()
        except pygame.error:
            pass
