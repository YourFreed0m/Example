from ursina import *
from noise import pnoise2
from typing import Dict, Tuple


def key_of(x: int, y: int, z: int) -> str:
    return f"{x},{y},{z}"


class Voxel(Button):
    def __init__(self, position=(0,0,0), texture_path: str = None, block_id: str = 'grass'):
        super().__init__(
            parent=scene,
            position=position,
            model='cube',
            origin_y=.5,
            texture=load_texture(texture_path) if texture_path else None,
            color=color.white,
            highlight_color=color.lime,
            collider='box')
        self.block_id = block_id


class VoxelWorld:
    def __init__(self, size_x: int = 16, size_z: int = 16, max_height: int = 12, seed: int = 1337, textures: Dict[str, str] = None):
        self.size_x = size_x
        self.size_z = size_z
        self.max_height = max_height
        self.seed = seed
        self.textures = textures or {}
        self.blocks: Dict[str, Voxel] = {}
        self.modified: Dict[str, str] = {}  # pos_key -> block_id or 'air'

    def generate(self):
        scale = 20.0
        octaves = 2
        persistence = 0.5
        lacunarity = 2.0
        for x in range(self.size_x):
            for z in range(self.size_z):
                n = pnoise2((x + self.seed) / scale, (z - self.seed) / scale,
                            octaves=octaves, persistence=persistence, lacunarity=lacunarity, repeatx=1024, repeaty=1024, base=0)
                base_h = int((n * 0.5 + 0.5) * (self.max_height - 4)) + 4
                for y in range(base_h + 1):
                    if y == base_h:
                        block_id = 'grass'
                    elif y > base_h - 3:
                        block_id = 'dirt'
                    else:
                        block_id = 'stone'
                    self._spawn((x, y, z), block_id)

                # Simple tree chance
                t = pnoise2((x + 999) / 10, (z - 555) / 10)
                if t > 0.35 and base_h + 4 < self.max_height:
                    for ty in range(1, 4):
                        self._spawn((x, base_h + ty, z), 'log')
                    for dx in range(-1, 2):
                        for dz in range(-1, 2):
                            self._spawn((x + dx, base_h + 3, z + dz), 'plank')

    def _spawn(self, pos: Tuple[int,int,int], block_id: str):
        x, y, z = pos
        if x < 0 or z < 0 or x >= self.size_x or z >= self.size_z:
            return
        k = key_of(x, y, z)
        if k in self.blocks:
            return
        tex_path = self.textures.get(block_id)
        v = Voxel(position=(x, y, z), texture_path=tex_path, block_id=block_id)
        self.blocks[k] = v

    def get_block(self, x: int, y: int, z: int) -> str:
        return self.blocks.get(key_of(x, y, z)).block_id if key_of(x, y, z) in self.blocks else 'air'

    def set_block(self, x: int, y: int, z: int, block_id: str):
        k = key_of(x, y, z)
        if block_id == 'air':
            if k in self.blocks:
                destroy(self.blocks[k])
                del self.blocks[k]
        else:
            if k in self.blocks:
                # Replace texture and id
                self.blocks[k].texture = load_texture(self.textures.get(block_id))
                self.blocks[k].block_id = block_id
            else:
                self._spawn((x, y, z), block_id)
        self.modified[k] = block_id

    def apply_modifications(self, mods: Dict[str, str]):
        for k, block_id in mods.items():
            x, y, z = map(int, k.split(','))
            if block_id == 'air':
                if k in self.blocks:
                    destroy(self.blocks[k]); del self.blocks[k]
            else:
                self.set_block(x, y, z, block_id)