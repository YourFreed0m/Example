# Voxel RPG (Python, Ursina)

Features:
- Voxel terrain with Perlin noise, block break/place (ЛКМ/ПКМ)
- First-person controls (WASD + Space), mouse lock toggle with Esc
- RPG: XP, levels, HP/Stamina/Mana bars, hotbar 1-5
- Auto-save every 2s (position, stats, modified blocks)
- Textures auto-downloaded on first run from the internet

Run:
- Install: `pip install -r requirements.txt`
- Start: `python main.py`

Notes:
- If `noise` fails to install, the game automatically falls back to `perlin-noise` (already listed in requirements).
- If your Ursina version lacks color helpers (e.g. `color.white`), this project uses `Color(r,g,b,a)` everywhere to be version-agnostic.
- On Windows, prefer a virtualenv:
  - `py -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt && py main.py`