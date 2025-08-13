from ursina import Entity, scene, load_texture, Color
from typing import Dict, Tuple

# Noise helpers: prefer noise.pnoise2; fallback to perlin-noise if not available
try:
    from noise import pnoise2  # type: ignore

    def height_noise(x: int, z: int, seed: int, scale: float) -> float:
        return pnoise2((x + seed) / scale, (z - seed) / scale,
                       octaves=2, persistence=0.5, lacunarity=2.0,
                       repeatx=4096, repeaty=4096, base=0)

    def tree_noise(x: int, z: int, seed: int) -> float:
        return pnoise2((x + 999) / 10.0, (z - 555) / 10.0)

except Exception:
    from perlin_noise import PerlinNoise  # type: ignore
    _height_noise = None
    _tree_noise = None

    def _ensure_noises(seed: int):
        global _height_noise, _tree_noise
        if _height_noise is None:
            _height_noise = PerlinNoise(octaves=2, seed=seed)
        if _tree_noise is None:
            _tree_noise = PerlinNoise(octaves=1, seed=seed + 12345)

    def height_noise(x: int, z: int, seed: int, scale: float) -> float:
        _ensure_noises(seed)
        return float(_height_noise([x / scale, z / scale]))

    def tree_noise(x: int, z: int, seed: int) -> float:
        _ensure_noises(seed)
        return float(_tree_noise([x / 10.0, z / 10.0]))


def key_of(x: int, y: int, z: int) -> str:
    return f"{x},{y},{z}"


class Voxel(Entity):
    def __init__(self, position=(0, 0, 0), texture_path: str | None = None, block_id: str = 'grass'):
        super().__init__(
            parent=scene,
            position=position,
            model='cube',
            origin_y=.5,
            texture=load_texture(texture_path) if texture_path else None,
            color=Color(1, 1, 1, 1),
            collider='box'
        )
        self.block_id = block_id


class VoxelWorld:
    def __init__(self, size_x: int = 16, size_z: int = 16, max_height: int = 12, seed: int = 1337, textures: Dict[str, str] | None = None):
        self.size_x = size_x
        self.size_z = size_z
        self.max_height = max_height
        self.seed = seed
        self.textures = textures or {}
        self.blocks: Dict[str, Voxel] = {}
        self.modified: Dict[str, str] = {}  # pos_key -> block_id or 'air'

    def generate(self):
        scale = 20.0
        for x in range(self.size_x):
            for z in range(self.size_z):
                n = height_noise(x, z, self.seed, scale)
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
                t = tree_noise(x, z, self.seed)
                if t > 0.35 and base_h + 4 < self.max_height:
                    for ty in range(1, 4):
                        self._spawn((x, base_h + ty, z), 'log')
                    for dx in range(-1, 2):
                        for dz in range(-1, 2):
                            self._spawn((x + dx, base_h + 3, z + dz), 'plank')

    def _spawn(self, pos: Tuple[int, int, int], block_id: str):
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
                self.blocks[k].disable()
                self.blocks[k].parent = None
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
                    self.blocks[k].disable(); self.blocks[k].parent = None; del self.blocks[k]
            else:
                self.set_block(x, y, z, block_id)