import sys
import math
import numpy as np
import pygame
from pygame import mixer
from pydub import AudioSegment
from tkinter import Tk, filedialog

WIDTH, HEIGHT = 1280, 800
GROUND_Y = HEIGHT  # draw from top to bottom

class Rider:
    def __init__(self):
        self.x = 0.0

    def update(self, dt, target_x):
        self.x += (target_x - self.x) * min(1.0, dt * 10.0)

    def draw(self, surf):
        cx = WIDTH // 2
        x = cx + int(self.x)
        y = int(HEIGHT * 0.85)
        pygame.draw.circle(surf, (255, 204, 0), (x, y), 14)

class Track:
    def __init__(self):
        self.speed = 10.0
        self.pickups = []  # list of (lane, y)

    def spawn_lane(self, lane: int):
        y = -20.0
        self.pickups.append([lane, y])

    def update(self, dt):
        for p in self.pickups:
            p[1] += self.speed * dt * 120.0
        self.pickups = [p for p in self.pickups if p[1] <= HEIGHT + 40]

    def draw(self, surf):
        cx = WIDTH // 2
        lane_w = int(WIDTH * 0.28)  # ~84% total width across 3 lanes
        for i in (-1, 0, 1):
            x = cx + int(i * lane_w)
            pygame.draw.rect(surf, (28, 36, 48), (x - lane_w//2, 0, lane_w, HEIGHT))
        for lane, y in self.pickups:
            x = cx + int(lane * lane_w)
            pygame.draw.circle(surf, (0, 209, 255), (x, int(y)), 10)

class AudioAnalyzer:
    def __init__(self):
        self.samples = None
        self.sample_rate = 44100
        self.t = 0.0
        # EMA averages for bands
        self.avg_low = 1e-6
        self.avg_mid = 1e-6
        self.avg_high = 1e-6
        self.cool_low = 0.0
        self.cool_mid = 0.0
        self.cool_high = 0.0

    def load(self, path):
        seg = AudioSegment.from_file(path)
        seg = seg.set_channels(1).set_frame_rate(self.sample_rate)
        s = np.array(seg.get_array_of_samples()).astype(np.float32)
        m = np.max(np.abs(s))
        self.samples = (s / m) if m > 0 else s
        mixer.music.load(path)
        mixer.music.play()

    def get_beats(self, dt):
        # No audio -> fake pulsation
        if self.samples is None:
            self.t += dt
            val = 0.3 + 0.2 * math.sin(self.t * 3.0)
            return (val > 0.45, False, False), (val, 0.0, 0.0)

        self.t += dt
        # FFT window
        win_size = 4096
        idx = int((self.t % (len(self.samples)/self.sample_rate)) * self.sample_rate)
        lo = max(0, idx - win_size//2)
        hi = min(len(self.samples), lo + win_size)
        chunk = self.samples[lo:hi]
        if len(chunk) < win_size:
            chunk = np.pad(chunk, (0, win_size - len(chunk)))
        window = np.hanning(win_size)
        spec = np.fft.rfft(chunk * window)
        mag = np.abs(spec)
        freqs = np.fft.rfftfreq(win_size, d=1.0/self.sample_rate)

        def band_energy(fa, fb):
            ia = int(fa / (self.sample_rate / win_size))
            ib = int(fb / (self.sample_rate / win_size))
            ia = max(0, min(ia, len(mag)-1))
            ib = max(ia+1, min(ib, len(mag)))
            return float(np.mean(mag[ia:ib]))

        low = band_energy(20, 150)
        mid = band_energy(150, 2000)
        high = band_energy(2000, 8000)

        # EMA
        alpha = 0.15
        self.avg_low = (1-alpha)*self.avg_low + alpha*low
        self.avg_mid = (1-alpha)*self.avg_mid + alpha*mid
        self.avg_high = (1-alpha)*self.avg_high + alpha*high

        # Cooldowns
        self.cool_low = max(0.0, self.cool_low - dt)
        self.cool_mid = max(0.0, self.cool_mid - dt)
        self.cool_high = max(0.0, self.cool_high - dt)

        # Beat when current > k * avg and cooldown elapsed
        k = 1.6
        beat_low = low > self.avg_low * k and self.cool_low <= 0
        beat_mid = mid > self.avg_mid * k and self.cool_mid <= 0
        beat_high = high > self.avg_high * k and self.cool_high <= 0
        if beat_low: self.cool_low = 0.18
        if beat_mid: self.cool_mid = 0.18
        if beat_high: self.cool_high = 0.18
        return (beat_low, beat_mid, beat_high), (low, mid, high)

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
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_f:
                    self.choose_audio()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 4:
                        self.track.speed = min(40.0, self.track.speed + 2.0)
                    if event.button == 5:
                        self.track.speed = max(4.0, self.track.speed - 2.0)

            # mouse X -> lane
            mx, _ = pygame.mouse.get_pos()
            nx = mx / WIDTH
            lane = int(round(nx * 2.0)) - 1
            lane = max(-1, min(1, lane))
            lane_w = int(WIDTH * 0.28)
            self.target_x = lane * lane_w

            # analysis and spawning strictly on beats
            beats, bands = self.audio.get_beats(dt)
            low_b, mid_b, high_b = beats
            if low_b: self.track.spawn_lane(-1)
            if mid_b: self.track.spawn_lane(0)
            if high_b: self.track.spawn_lane(1)

            # update world
            self.rider.update(dt, self.target_x)
            self.track.update(dt)

            # draw
            self.screen.fill((11, 14, 19))
            self.track.draw(self.screen)
            self.rider.draw(self.screen)
            self.draw_ui()
            pygame.display.flip()

        pygame.quit()

    def draw_ui(self):
        font = pygame.font.SysFont(None, 22)
        text = font.render("Мышь: X — полоса, колесо — скорость | F: выбрать аудио", True, (200, 200, 200))
        self.screen.blit(text, (12, 12))

if __name__ == '__main__':
    game = Game()
    game.choose_audio()
    game.run()