from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple

# Simple block registry

@dataclass(frozen=True)
class Block:
    id: int
    name: str
    textures: Tuple[str, str, str, str, str, str]  # per-face names: px, nx, py, ny, pz, nz
    solid: bool = True
    hardness: float = 1.0


class Blocks:
    by_id: Dict[int, Block] = {}
    by_name: Dict[str, Block] = {}

    @classmethod
    def register(cls, block: Block) -> None:
        cls.by_id[block.id] = block
        cls.by_name[block.name] = block

    @classmethod
    def get(cls, block_id: int) -> Block:
        return cls.by_id.get(block_id, cls.by_name["air"])  # type: ignore


# Register core blocks
Blocks.register(Block(0, "air", ("", "", "", "", "", ""), solid=False, hardness=0.0))
Blocks.register(Block(1, "stone", ("stone",)*6, hardness=3.0))
Blocks.register(Block(2, "dirt", ("dirt",)*6, hardness=0.5))
Blocks.register(Block(3, "grass", ("grass_side", "grass_side", "grass_top", "dirt", "grass_side", "grass_side"), hardness=0.6))
Blocks.register(Block(4, "planks", ("planks_oak",)*6, hardness=1.5))
Blocks.register(Block(5, "log", ("log_oak", "log_oak", "log_oak_top", "log_oak_top", "log_oak", "log_oak"), hardness=2.0))
Blocks.register(Block(6, "sand", ("sand",)*6, hardness=0.5))
Blocks.register(Block(7, "glass", ("glass",)*6, hardness=0.3))