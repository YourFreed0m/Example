from __future__ import annotations
from typing import Dict, Tuple
from perlin_noise import PerlinNoise

from .utils import CHUNK_SIZE_X, CHUNK_SIZE_Z, CHUNK_HEIGHT
from .chunk import Chunk
from .block import Blocks


class World:
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.chunks: Dict[Tuple[int, int], Chunk] = {}
        self.uvs = None  # filled by window/renderer after atlas creation
        # Multi-octave noise
        self.noise_layers = [
            PerlinNoise(octaves=1, seed=seed),
            PerlinNoise(octaves=2, seed=seed + 1),
            PerlinNoise(octaves=4, seed=seed + 2),
        ]

    def height_at(self, wx: int, wz: int) -> int:
        x = wx / 128.0
        z = wz / 128.0
        n = 0.0
        amp = 1.0
        for i, layer in enumerate(self.noise_layers):
            n += layer([x, z]) * amp
            amp *= 0.5
        # Normalize to [0,1]
        n = (n * 0.5) + 0.5
        h = int(n * (CHUNK_HEIGHT * 0.6)) + 32
        return max(1, min(CHUNK_HEIGHT - 1, h))

    def ensure_chunk(self, coords: Tuple[int, int]) -> Chunk:
        if coords in self.chunks:
            return self.chunks[coords]
        chunk = Chunk(coords)
        self.generate_chunk(chunk)
        self.chunks[coords] = chunk
        return chunk

    def generate_chunk(self, chunk: Chunk) -> None:
        cx, cz = chunk.coords
        base_x = cx * CHUNK_SIZE_X
        base_z = cz * CHUNK_SIZE_Z
        for x in range(CHUNK_SIZE_X):
            for z in range(CHUNK_SIZE_Z):
                wx = base_x + x
                wz = base_z + z
                h = self.height_at(wx, wz)
                top_block = Blocks.by_name["grass"].id
                for y in range(h):
                    if y == h - 1:
                        bid = top_block
                    elif y >= h - 4:
                        bid = Blocks.by_name["dirt"].id
                    else:
                        bid = Blocks.by_name["stone"].id
                    chunk.set_block(x, y, z, bid)

    def build_visible_meshes(self) -> None:
        if self.uvs is None:
            return
        for chunk in self.chunks.values():
            if chunk.mesh_dirty:
                chunk.rebuild_mesh(self.uvs)