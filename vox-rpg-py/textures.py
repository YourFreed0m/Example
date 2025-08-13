import pathlib
import requests
from typing import Dict

try:
    from PIL import Image, ImageDraw
except Exception:
    Image = None
    ImageDraw = None

# Prefer local files; fallback to downloading if missing; finally generate
TEXTURE_SPECS = {
    'grass':   ('https://raw.githubusercontent.com/emmelleppi/tiny-textures/main/grass_16x16.png', 'grass.png'),
    'dirt':    ('https://raw.githubusercontent.com/emmelleppi/tiny-textures/main/dirt_16x16.png', 'dirt.png'),
    'stone':   ('https://raw.githubusercontent.com/emmelleppi/tiny-textures/main/stone_16x16.png', 'stone.png'),
    'log':     ('https://raw.githubusercontent.com/emmelleppi/tiny-textures/main/log_16x16.png', 'log.png'),
    'plank':   ('https://raw.githubusercontent.com/emmelleppi/tiny-textures/main/planks_16x16.png', 'plank.png'),
    'water':   ('https://raw.githubusercontent.com/emmelleppi/tiny-textures/main/water_16x16.png', 'water.png')
}

ASSET_DIR = pathlib.Path(__file__).resolve().parent / 'textures'
ASSET_DIR.mkdir(parents=True, exist_ok=True)


def _generate_procedural(name: str, path: pathlib.Path) -> None:
    if Image is None:
        return
    size = 32
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    if name == 'grass':
        base = (86, 125, 70)
        for y in range(size):
            for x in range(size):
                shade = ((x ^ y) & 1) * 8
                draw.point((x, y), fill=(base[0]-shade, base[1]-shade, base[2]-shade, 255))
    elif name == 'dirt':
        base = (139, 90, 43)
        for y in range(size):
            for x in range(size):
                shade = ((x * 3 + y * 5) % 7)
                draw.point((x, y), fill=(base[0]-shade, base[1]-shade, base[2]-shade, 255))
    elif name == 'stone':
        base = (128, 128, 128)
        for y in range(size):
            for x in range(size):
                shade = ((x * 2 + y * 2) % 10)
                draw.point((x, y), fill=(base[0]-shade, base[1]-shade, base[2]-shade, 255))
    elif name == 'log':
        base = (139, 107, 59)
        for y in range(size):
            for x in range(size):
                shade = ((x + (y//4)*2) % 12)
                draw.point((x, y), fill=(base[0]-shade, base[1]-shade, base[2]-shade, 255))
    elif name == 'plank':
        base = (202, 164, 114)
        for y in range(size):
            for x in range(size):
                shade = ((x + y) % 6)
                draw.point((x, y), fill=(base[0]-shade, base[1]-shade, base[2]-shade, 255))
            if y % 8 == 0:
                draw.line([(0, y), (size, y)], fill=(120, 90, 50, 255))
    elif name == 'water':
        base = (58, 113, 196)
        for y in range(size):
            for x in range(size):
                shade = ((x * x + y * y) % 11)
                draw.point((x, y), fill=(base[0]-shade, base[1]-shade, base[2]-shade, 200))
    img.save(path)


def ensure_textures_downloaded() -> Dict[str, str]:
    paths: Dict[str, str] = {}
    for key, (url, filename) in TEXTURE_SPECS.items():
        local_path = ASSET_DIR / filename
        if not local_path.exists():
            # try download
            try:
                r = requests.get(url, timeout=10)
                if r.ok and r.content and len(r.content) > 0:
                    with open(local_path, 'wb') as f:
                        f.write(r.content)
                    print(f"Downloaded texture: {key} -> {local_path}")
                else:
                    raise RuntimeError('empty')
            except Exception:
                # generate fallback
                _generate_procedural(key, local_path)
        # return relative path from asset_folder
        paths[key] = f"textures/{filename}"
    return paths