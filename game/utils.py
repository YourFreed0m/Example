from __future__ import annotations
import os
import time
from dataclasses import dataclass
from typing import Tuple

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
TEXTURES_DIR = os.path.join(ASSETS_DIR, "textures")
ATLAS_DIR = os.path.join(ASSETS_DIR, "atlas")
SHADERS_DIR = os.path.join(ASSETS_DIR, "shaders")
CACHE_DIR = os.path.join(ASSETS_DIR, "cache")
SKY_DIR = os.path.join(ASSETS_DIR, "sky")

for directory in (ASSETS_DIR, TEXTURES_DIR, ATLAS_DIR, SHADERS_DIR, CACHE_DIR, SKY_DIR):
    os.makedirs(directory, exist_ok=True)


def monotonic_ms() -> int:
    return int(time.monotonic() * 1000)


@dataclass(frozen=True)
class ChunkCoords:
    x: int
    z: int

    def as_tuple(self) -> Tuple[int, int]:
        return (self.x, self.z)


CHUNK_SIZE_X = 16
CHUNK_SIZE_Z = 16
CHUNK_HEIGHT = 128
BLOCK_AIR = 0