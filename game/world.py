from __future__ import annotations
from typing import Dict, Tuple
import math
from noise import pnoise2

from .utils import CHUNK_SIZE_X, CHUNK_SIZE_Z, CHUNK_HEIGHT
from .chunk import Chunk
from .block import Blocks


class World:
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.chunks: Dict[Tuple[int, int], Chunk] = {}
        self.uvs = None  # filled by window/renderer after atlas creation

    def height_at(self, wx: int, wz: int) -> int:
        scale = 128.0
        n = pnoise2((wx + self.seed) / scale, (wz + self.seed) / scale, octaves=4, persistence=0.5, lacunarity=2.0, repeatx=1024, repeaty=1024, base=self.seed)
        # Normalize to [0,1]
        h = int((n * 0.5 + 0.5) * (CHUNK_HEIGHT * 0.6)) + 32
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