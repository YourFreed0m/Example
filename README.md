# Python Minecraft-like Clone

This is a feature-rich Minecraft-like sandbox game written in Python with a focus on:
- Procedural infinite world generation (chunk-based)
- Basic lighting and a day/night cycle with sun and moon
- Mining and building with block types and a texture atlas
- Inventory and a 3x3 crafting grid (basic recipes)
- RPG passive skill tree system (Path of Exile–inspired)

The code uses pyglet for the window/event loop, ModernGL for rendering, and common Python libraries for math and noise.

## Requirements
- Python 3.10+
- Linux/macOS/Windows
- GPU with OpenGL 3.3+

## Install
```bash
python -m venv .venv
source .venv/bin/activate # Windows: .venv\\Scripts\\activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Run
```bash
python main.py
```

If you are in a headless or remote environment without a display, you can run a quick validation (no window) which compiles shaders, builds a few chunks, and exits:
```bash
python main.py --headless
```

## Controls
- WASD: Move
- Space: Jump
- Shift: Sneak (slower walk)
- Mouse: Look around
- Left Click: Mine block
- Right Click: Place selected block
- Mouse Wheel / 1–9: Select hotbar slot
- E: Open/close inventory + crafting
- P: Open/close passive skill tree
- F5: Toggle third-person camera
- F11: Toggle fullscreen
- Esc: Pause / unlock mouse

## Textures
On first run, the game attempts to download CC0/CC-BY textures from public sources and builds a texture atlas under `assets/`. If the download fails (e.g., network restrictions), the game falls back to procedural colors. You can add your own textures by placing 16x16 PNGs into `assets/textures/blocks/` and re-running.

## Features
- Chunked world (16x128x16) with multi-octave Perlin noise
- Simple face-culling meshing with per-vertex ambient occlusion
- Directional sunlight and ambient light varying with time of day
- Sun/Moon sky dome with dynamic color gradient
- Block definitions with per-face textures
- Inventory + 3x3 crafting, with a few core recipes (planks, sticks, table, pickaxe)
- Mining hardness, basic tool tiers, and build placement rules
- Passive tree with nodes affecting movement speed, mining speed, health, carry capacity
- Save/Load of player state and world seed

## Known Limitations
- Lighting is simplified (no block light propagation)
- Physics and collisions are AABB-based and may be improved
- Meshing uses straightforward face culling (no greedy meshing yet)
- Recipe set is minimal; extend via `game/crafting.py`

## Project Structure
```
main.py
requirements.txt
assets/
  shaders/
  textures/
  atlas/
  cache/
  sky/
 game/
  __init__.py
  window.py
  renderer.py
  world.py
  chunk.py
  block.py
  textures.py
  player.py
  input.py
  inventory.py
  crafting.py
  rpg.py
  sky.py
  utils.py
  save.py
```

## License
Code is MIT. Textures are from CC0/CC-BY sources as referenced in comments and downloader script. Replace with your own if needed.