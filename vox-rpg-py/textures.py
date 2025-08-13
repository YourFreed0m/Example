import os
import pathlib
import requests
from typing import Dict

# Texture sources: singlecolorimage.com returns a PNG of the given hex color and size.
# These are generated images from the internet, suitable as placeholder textures.
TEXTURE_SPECS = {
    'grass':   ('https://singlecolorimage.com/get/55aa55/32x32', 'grass.png'),
    'dirt':    ('https://singlecolorimage.com/get/8b5a2b/32x32', 'dirt.png'),
    'stone':   ('https://singlecolorimage.com/get/888888/32x32', 'stone.png'),
    'log':     ('https://singlecolorimage.com/get/8b6b3b/32x32', 'log.png'),
    'plank':   ('https://singlecolorimage.com/get/caa472/32x32', 'plank.png'),
    'water':   ('https://singlecolorimage.com/get/3a71c4/32x32', 'water.png')
}

ASSET_DIR = pathlib.Path(__file__).resolve().parent / 'textures'
ASSET_DIR.mkdir(parents=True, exist_ok=True)


def ensure_textures_downloaded() -> Dict[str, str]:
    paths: Dict[str, str] = {}
    for key, (url, filename) in TEXTURE_SPECS.items():
        local_path = ASSET_DIR / filename
        if not local_path.exists():
            try:
                r = requests.get(url, timeout=10)
                r.raise_for_status()
                with open(local_path, 'wb') as f:
                    f.write(r.content)
                print(f"Downloaded texture: {key} -> {local_path}")
            except Exception as e:
                print(f"Warning: failed to download {key} from {url}: {e}")
        paths[key] = str(local_path)
    return paths