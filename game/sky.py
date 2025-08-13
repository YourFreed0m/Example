from __future__ import annotations
import math


class SkyCycle:
    def __init__(self):
        self.time_of_day = 0.25  # morning
        self.day_length_seconds = 600.0

    def update(self, dt: float):
        self.time_of_day = (self.time_of_day + dt / self.day_length_seconds) % 1.0

    def sun_direction(self):
        angle = (self.time_of_day * 2.0 * math.pi) - math.pi / 2.0
        return (math.cos(angle), math.sin(angle), 0.0)