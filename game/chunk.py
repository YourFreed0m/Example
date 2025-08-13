from __future__ import annotations
from typing import Dict, Tuple, List
import numpy as np

from .utils import CHUNK_SIZE_X, CHUNK_SIZE_Z, CHUNK_HEIGHT, BLOCK_AIR
from .block import Blocks


class Chunk:
    def __init__(self, coords: Tuple[int, int]):
        self.coords = coords
        self.blocks = np.zeros((CHUNK_SIZE_X, CHUNK_HEIGHT, CHUNK_SIZE_Z), dtype=np.uint16)
        self.mesh_dirty = True
        self.vertex_data: np.ndarray | None = None
        self.index_count: int = 0  # stores vertex count for non-indexed draw

    def set_block(self, x: int, y: int, z: int, block_id: int) -> None:
        if 0 <= x < CHUNK_SIZE_X and 0 <= y < CHUNK_HEIGHT and 0 <= z < CHUNK_SIZE_Z:
            self.blocks[x, y, z] = block_id
            self.mesh_dirty = True

    def get_block(self, x: int, y: int, z: int) -> int:
        if 0 <= x < CHUNK_SIZE_X and 0 <= y < CHUNK_HEIGHT and 0 <= z < CHUNK_SIZE_Z:
            return int(self.blocks[x, y, z])
        return BLOCK_AIR

    def rebuild_mesh(self, uvs: Dict[str, Tuple[float, float, float, float]]) -> None:
        # Vertex format per-vertex: x,y,z,u,v,light
        vertices: List[float] = []

        # Directions: (dx, dy, dz), face index
        directions = [
            ((1, 0, 0), 0),
            ((-1, 0, 0), 1),
            ((0, 1, 0), 2),
            ((0, -1, 0), 3),
            ((0, 0, 1), 4),
            ((0, 0, -1), 5),
        ]

        # Face-based light factor
        face_light = {
            2: 1.0,  # +Y top
            3: 0.6,  # -Y bottom
            0: 0.85,
            1: 0.85,
            4: 0.8,
            5: 0.8,
        }

        for x in range(CHUNK_SIZE_X):
            for y in range(CHUNK_HEIGHT):
                for z in range(CHUNK_SIZE_Z):
                    block_id = int(self.blocks[x, y, z])
                    if block_id == BLOCK_AIR:
                        continue
                    block = Blocks.get(block_id)
                    if not block.solid:
                        continue

                    for (dx, dy, dz), face in directions:
                        nx = x + dx
                        ny = y + dy
                        nz = z + dz
                        neighbor = self.get_block(nx, ny, nz)
                        if neighbor != BLOCK_AIR and Blocks.get(neighbor).solid:
                            continue

                        # Define quad vertices per face
                        if face == 0:  # +X
                            quad = [
                                (x + 1, y, z), (x + 1, y, z + 1), (x + 1, y + 1, z + 1), (x + 1, y + 1, z)
                            ]
                        elif face == 1:  # -X
                            quad = [
                                (x, y, z + 1), (x, y, z), (x, y + 1, z), (x, y + 1, z + 1)
                            ]
                        elif face == 2:  # +Y
                            quad = [
                                (x, y + 1, z), (x + 1, y + 1, z), (x + 1, y + 1, z + 1), (x, y + 1, z + 1)
                            ]
                        elif face == 3:  # -Y
                            quad = [
                                (x, y, z + 1), (x + 1, y, z + 1), (x + 1, y, z), (x, y, z)
                            ]
                        elif face == 4:  # +Z
                            quad = [
                                (x + 1, y, z + 1), (x, y, z + 1), (x, y + 1, z + 1), (x + 1, y + 1, z + 1)
                            ]
                        else:  # -Z
                            quad = [
                                (x, y, z), (x + 1, y, z), (x + 1, y + 1, z), (x, y + 1, z)
                            ]

                        # Fetch UV rect for this face
                        tex_name = block.textures[face] if block.textures[face] else block.textures[0]
                        u0, v0, u1, v1 = uvs.get(tex_name, (0.0, 0.0, 1.0, 1.0))
                        # Map in consistent order
                        uv_quad = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]

                        light = face_light.get(face, 0.8)

                        # Two triangles: (0,1,2) and (2,3,0)
                        order = [0, 1, 2, 2, 3, 0]
                        for idx in order:
                            vx, vy, vz = quad[idx]
                            uu, vv = uv_quad[idx]
                            vertices.extend([float(vx), float(vy), float(vz), float(uu), float(vv), float(light)])

        if vertices:
            self.vertex_data = np.array(vertices, dtype=np.float32)
            self.index_count = len(vertices) // 6
        else:
            self.vertex_data = None
            self.index_count = 0

        self.mesh_dirty = False