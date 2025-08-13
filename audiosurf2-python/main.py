from ursina import *
from ursina import Color
from pydub import AudioSegment
import numpy as np
from tkinter import Tk, filedialog

WIN_W, WIN_H = 1280, 800

class AudioAnalyzer:
    def __init__(self):
        self.samples = None
        self.sample_rate = 44100
        self.t = 0.0
        self.avg_low = 1e-6
        self.avg_mid = 1e-6
        self.avg_high = 1e-6
        self.cool_low = 0.0
        self.cool_mid = 0.0
        self.cool_high = 0.0

    def load(self, path):
        seg = AudioSegment.from_file(path)
        seg = seg.set_channels(1).set_frame_rate(self.sample_rate)
        s = np.array(seg.get_array_of_samples(), dtype=np.float32)
        m = np.max(np.abs(s))
        self.samples = (s / m) if m > 0 else s
        # playback using system default player is out-of-scope; rely on external playback or silence

    def get_beats(self, dt):
        if self.samples is None:
            self.t += dt
            val = 0.3 + 0.2 * np.sin(self.t * 3.0)
            return (val > 0.45, False, False)
        self.t += dt
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

        def band_energy(fa, fb):
            ia = int(fa / (self.sample_rate / win_size))
            ib = int(fb / (self.sample_rate / win_size))
            ia = max(0, min(ia, len(mag)-1))
            ib = max(ia+1, min(ib, len(mag)))
            return float(np.mean(mag[ia:ib]))

        low = band_energy(20, 150)
        mid = band_energy(150, 2000)
        high = band_energy(2000, 8000)

        alpha = 0.15
        self.avg_low = (1-alpha)*self.avg_low + alpha*low
        self.avg_mid = (1-alpha)*self.avg_mid + alpha*mid
        self.avg_high = (1-alpha)*self.avg_high + alpha*high

        self.cool_low = max(0.0, self.cool_low - dt)
        self.cool_mid = max(0.0, self.cool_mid - dt)
        self.cool_high = max(0.0, self.cool_high - dt)

        k = 1.6
        beat_low = low > self.avg_low * k and self.cool_low <= 0
        beat_mid = mid > self.avg_mid * k and self.cool_mid <= 0
        beat_high = high > self.avg_high * k and self.cool_high <= 0
        if beat_low: self.cool_low = 0.18
        if beat_mid: self.cool_mid = 0.18
        if beat_high: self.cool_high = 0.18
        return (beat_low, beat_mid, beat_high)

class Neon:
    @staticmethod
    def mat(color: Color) -> Color:
        return color

class Pickup(Entity):
    def __init__(self, lane: int, z: float):
        super().__init__(model='sphere', scale=0.6, color=Neon.mat(Color(0,1,1,1)))
        self.x = lane * 2.0
        self.y = 0.5
        self.z = z
        self.lane = lane

    def update(self):
        self.z += time.dt * 16.0
        if self.z > 6:
            destroy(self)

class Rider(Entity):
    def __init__(self):
        super().__init__(model='torus', color=Neon.mat(Color(1,0.8,0,1)), scale=0.8, y=0.5, z=4)
        self.target_x = 0.0

    def update(self):
        self.x = lerp(self.x, self.target_x, min(1, time.dt*10))

class Game(Ursina):
    def __init__(self):
        super().__init__(borderless=False)
        window.size = (WIN_W, WIN_H)
        camera.position = (0, 5, -8)
        camera.look_at((0,0.5,0))
        # Lanes
        for i in (-1, 0, 1):
            Entity(model='cube', position=(i*2.0, 0, 0), scale=(1.9, 0.1, 200), color=Color(0.12,0.15,0.2,1))
            # Neon stripes
            Entity(model='cube', position=(i*2.0, 0.06, 0), scale=(0.05, 0.01, 200), color=Color(0,1,1,1))
        self.rider = Rider()
        self.audio = AudioAnalyzer()
        self.last_spawn_z = -80
        # UI
        Text("Мышь: X — полоса | F: выбрать аудио", position=(-0.5, 0.45), scale=1, origin=(-.5,-.5))

    def input(self, key):
        if key == 'f':
            try:
                Tk().withdraw()
                file = filedialog.askopenfilename(filetypes=[("Audio","*.mp3 *.wav *.ogg *.flac *.m4a")])
                if file:
                    self.audio.load(file)
            except Exception as e:
                print('Audio load failed:', e)

    def update(self):
        # Mouse X -> lane
        nx = mouse.position[0]  # -1..1 in viewport coords
        lane = int(round((nx+1)/2 * 2)) - 1
        lane = max(-1, min(1, lane))
        self.rider.target_x = lane * 2.0

        # Beat-synced spawns
        bl, bm, bh = self.audio.get_beats(time.dt)
        if bl: Pickup(-1, -60)
        if bm: Pickup(0, -60)
        if bh: Pickup(1, -60)

if __name__ == '__main__':
    game = Game()
    game.run()