from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from typing import Dict
import json

from rpg import PlayerStats, Inventory, save_game, load_game
from world import VoxelWorld
from textures import ensure_textures_downloaded
from hud import HUD


app = Ursina()
window.title = 'Voxel RPG (Python)'
window.borderless = False
window.fullscreen = False

# Load or init state
saved = load_game()
player_stats = PlayerStats(**saved.get('stats', {})) if saved.get('stats') else PlayerStats()
inv_data = saved.get('inventory', None)
inventory = Inventory(**inv_data) if inv_data else Inventory()
spawn = saved.get('position', {'x': 8, 'y': 20, 'z': 8})

# Lighting
AmbientLight(color=color.rgba(255,255,255,80))
DirectionalLight(direction=(1,-1,-.5), color=color.rgba(255,255,255,255))

# Textures
texture_paths: Dict[str, str] = ensure_textures_downloaded()

# World
world = VoxelWorld(size_x=24, size_z=24, max_height=16, seed=1337, textures=texture_paths)
world.generate()

# Apply saved modifications if any
mods = saved.get('mods', {})
if mods:
    world.apply_modifications(mods)

# Player
player = FirstPersonController(position=(spawn['x'], spawn['y'], spawn['z']))
player.gravity = 1.0

# HUD
hud = HUD([slot['id'] for slot in inventory.slots])
hud.set_selected(inventory.selected_index)

crosshair = Entity(parent=camera.ui, model='quad', color=color.white, scale=(.0025,.02), rotation_z=0)
Entity(parent=camera.ui, model='quad', color=color.white, scale=(.02,.0025), rotation_z=0)


selected_block_id = lambda: inventory.slots[inventory.selected_index]['id']


def place_block():
    if mouse.hovered_entity and hasattr(mouse.hovered_entity, 'block_id'):
        p = mouse.hovered_entity.position + mouse.normal
        world.set_block(int(p.x), int(p.y), int(p.z), selected_block_id())
        player_stats.add_xp(2)


def break_block():
    if mouse.hovered_entity and hasattr(mouse.hovered_entity, 'block_id'):
        p = mouse.hovered_entity.position
        world.set_block(int(p.x), int(p.y), int(p.z), 'air')
        player_stats.add_xp(5)


def input(key):
    global inventory
    if key == 'left mouse down':
        break_block()
    if key == 'right mouse down':
        place_block()

    if key in ['1','2','3','4','5']:
        i = int(key) - 1
        if 0 <= i < len(inventory.slots):
            inventory.selected_index = i
            hud.set_selected(i)

    if key == 'escape':
        mouse.locked = not mouse.locked


def update():
    dt = time.dt
    player_stats.regen(dt)
    hud.update_stats(player_stats)


# Autosave
from direct.stdpy import threading

def autosave_loop():
    while True:
        import time as _t
        _t.sleep(2)
        data = {
            'stats': player_stats.__dict__,
            'inventory': {
                'selected_index': inventory.selected_index,
                'slots': inventory.slots,
            },
            'position': {'x': player.x, 'y': player.y, 'z': player.z},
            'mods': world.modified,
        }
        save_game(data)

threading.Thread(target=autosave_loop, daemon=True).start()

app.run()