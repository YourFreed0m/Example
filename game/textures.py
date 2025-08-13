from __future__ import annotations
import os
import io
import math
from typing import Dict, List, Tuple
from PIL import Image
import requests

from .utils import TEXTURES_DIR, ATLAS_DIR

BLOCKS_SRC: Dict[str, str] = {
    # CC0/CC-BY sources (fallback mirrors may be used). Kept small; user may add more.
    "stone": "https://raw.githubusercontent.com/BSVino/DoubleAgent/master/Tests/Minecraft/stone.png",
    "dirt": "https://raw.githubusercontent.com/BSVino/DoubleAgent/master/Tests/Minecraft/dirt.png",
    "grass_top": "https://raw.githubusercontent.com/BSVino/DoubleAgent/master/Tests/Minecraft/grass_top.png",
    "grass_side": "https://raw.githubusercontent.com/BSVino/DoubleAgent/master/Tests/Minecraft/grass_side.png",
    "planks_oak": "https://raw.githubusercontent.com/BSVino/DoubleAgent/master/Tests/Minecraft/wood.png",
    "log_oak": "https://raw.githubusercontent.com/BSVino/DoubleAgent/master/Tests/Minecraft/log_oak.png",
    "log_oak_top": "https://raw.githubusercontent.com/BSVino/DoubleAgent/master/Tests/Minecraft/log_oak_top.png",
    "sand": "https://raw.githubusercontent.com/BSVino/DoubleAgent/master/Tests/Minecraft/sand.png",
    "glass": "https://raw.githubusercontent.com/BSVino/DoubleAgent/master/Tests/Minecraft/glass.png",
}


def _safe_download(url: str) -> Image.Image | None:
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = io.BytesIO(resp.content)
        img = Image.open(data).convert("RGBA")
        return img
    except Exception:
        return None


def ensure_textures_and_atlas(block_size: int = 16) -> Tuple[Image.Image, Dict[str, Tuple[float, float, float, float]]]:
    os.makedirs(TEXTURES_DIR, exist_ok=True)
    os.makedirs(ATLAS_DIR, exist_ok=True)

    block_images: Dict[str, Image.Image] = {}
    for name, url in BLOCKS_SRC.items():
        png_path = os.path.join(TEXTURES_DIR, f"{name}.png")
        if not os.path.exists(png_path):
            img = _safe_download(url)
            if img is None:
                # Fallback: procedural solid color
                img = Image.new("RGBA", (block_size, block_size), (int(hash(name)) & 255, 128, 128, 255))
            img.resize((block_size, block_size)).save(png_path)
        block_images[name] = Image.open(png_path).convert("RGBA").resize((block_size, block_size))

    # Build atlas grid
    names = sorted(block_images.keys())
    grid = math.ceil(math.sqrt(len(names)))
    atlas_size = grid * block_size
    atlas = Image.new("RGBA", (atlas_size, atlas_size))
    uvs: Dict[str, Tuple[float, float, float, float]] = {}

    for idx, name in enumerate(names):
        gx = idx % grid
        gy = idx // grid
        x = gx * block_size
        y = gy * block_size
        atlas.paste(block_images[name], (x, y))
        # UVs as (u0, v0, u1, v1) with pixel-center offset to avoid bleeding
        pad = 0.5 / atlas_size
        u0 = x / atlas_size + pad
        v0 = y / atlas_size + pad
        u1 = (x + block_size) / atlas_size - pad
        v1 = (y + block_size) / atlas_size - pad
        uvs[name] = (u0, v0, u1, v1)

    atlas_path = os.path.join(ATLAS_DIR, "blocks_atlas.png")
    atlas.save(atlas_path)
    return atlas, uvs