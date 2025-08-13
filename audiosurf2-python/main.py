import sys
import math
import numpy as np
import pygame
from pygame import mixer
from pydub import AudioSegment
from pydub.utils import mediainfo
from tkinter import Tk, filedialog

WIDTH, HEIGHT = 1280, 800
LANE_W = 120
GROUND_Y = int(HEIGHT * 0.7)

class Rider:
    def __init__(self):
        self.x = 0.0
        self.y = 0.35
        self.vy = 0.0

    @property
    def on_ground(self):
        return self.y <= 0.351

    def jump(self):
        self.vy = 6.0

    def update(self, dt, target_x):
        self.x += (target_x - self.x) * min(1.0, dt * 10.0)
        if self.vy > 0 or self.y > 0.35:
            self.y += self.vy * dt
            self.vy -= 18.0 * dt
            if self.y <= 0.35:
                self.y = 0.35
                self.vy = 0.0

    def draw(self, surf):
        cx = WIDTH // 2
        x = cx + int(self.x)
        y = GROUND_Y - int(self.y * 100)
        pygame.draw.circle(surf, (255, 204, 0), (x, y), 12)

class Track:
    def __init__(self):
        self.speed = 10.0
        self.pickups = []  # list of (lane, z)
        self.spawn_timer = 0.0

    def update(self, dt, intensity):
        self.spawn_timer += dt * (0.5 + intensity * 4.0)
        if self.spawn_timer >= 1.0:
            self.spawn_timer = 0.0
            lane = np.random.randint(-1, 2)
            z = -600.0 - np.random.randint(0, 300)
            self.pickups.append([lane, z])
        # move
        for p in self.pickups:
            p[1] += self.speed * dt * 60.0
        # cleanup
        self.pickups = [p for p in self.pickups if p[1] <= 100.0]

    def draw(self, surf):
        cx = WIDTH // 2
        for i in (-1, 0, 1):
            x = cx + int(i * LANE_W)
            pygame.draw.rect(surf, (28, 36, 48), (x - LANE_W//2, GROUND_Y - 600, LANE_W, 800))
        for lane, z in self.pickups:
            x = cx + int(lane * LANE_W)
            y = GROUND_Y - int(z)
            pygame.draw.circle(surf, (0, 209, 255), (x, y), 8)

class AudioAnalyzer:
    def __init__(self):
        self.samples = None
        self.sample_rate = 44100
        self.t = 0.0
        self.play_obj = None

    def load(self, path):
        seg = AudioSegment.from_file(path)
        seg = seg.set_channels(1).set_frame_rate(self.sample_rate)
        s = np.array(seg.get_array_of_samples()).astype(np.float32)
        self.samples = s / np.max(np.abs(s))
        # play via pygame mixer
        mixer.music.load(path)
        mixer.music.play()

    def get_intensity(self, dt):
        # fallback if no file
        if self.samples is None:
            self.t += dt
            return 0.3 + 0.2 * math.sin(self.t * 3.0)
        # estimate instantaneous energy in bass band using a very simple window
        # not perfect, but enough for spawning
        window = int(self.sample_rate * 0.03)
        self.t += dt
        idx = int((self.t % (len(self.samples)/self.sample_rate)) * self.sample_rate)
        lo = max(0, idx - window)
        hi = min(len(self.samples), idx + window)
        energy = float(np.mean(np.abs(self.samples[lo:hi])))
        return max(0.0, min(1.0, energy * 4.0))

class Game:
    def __init__(self):
        pygame.init()
        mixer.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Audiosurf2 Mini (Python)")
        self.clock = pygame.time.Clock()
        self.rider = Rider()
        self.track = Track()
        self.audio = AudioAnalyzer()
        self.target_x = 0.0

    def choose_audio(self):
        try:
            Tk().withdraw()
            file = filedialog.askopenfilename(filetypes=[("Audio", "*.mp3 *.wav *.ogg *.flac *.m4a")])
            if file:
                self.audio.load(file)
        except Exception as e:
            print("Audio load failed:", e)

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(120) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1 and self.rider.on_ground:
                        self.rider.jump()
                    if event.button == 4:
                        self.track.speed = min(40.0, self.track.speed + 2.0)
                    if event.button == 5:
                        self.track.speed = max(4.0, self.track.speed - 2.0)

            # mouse X -> lane
            mx, _ = pygame.mouse.get_pos()
            nx = mx / WIDTH
            lane = int(round(nx * 2.0)) - 1
            lane = max(-1, min(1, lane))
            self.target_x = lane * LANE_W

            # update
            self.rider.update(dt, self.target_x)
            intensity = self.audio.get_intensity(dt)
            self.track.update(dt, intensity)

            # draw
            self.screen.fill((11, 14, 19))
            self.track.draw(self.screen)
            self.rider.draw(self.screen)
            self.draw_ui()
            pygame.display.flip()

        pygame.quit()

    def draw_ui(self):
        font = pygame.font.SysFont(None, 22)
        text = font.render("Мышь: X — полоса, колесо — скорость, ЛКМ — прыжок | F: выбрать аудио", True, (200, 200, 200))
        self.screen.blit(text, (12, 12))

if __name__ == '__main__':
    game = Game()
    game.choose_audio()
    game.run()