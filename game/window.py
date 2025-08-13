from __future__ import annotations
import math
from typing import Tuple
import pyglet
from pyglet.window import key, mouse

from .renderer import Renderer
from .textures import ensure_textures_and_atlas
from .world import World
from .player import Player
from .input import InputState
from .sky import SkyCycle
from .block import Blocks


class GameWindow(pyglet.window.Window):
    def __init__(self, width=1280, height=720, caption="PyCraft"):
        super().__init__(width=width, height=height, caption=caption, resizable=True)
        self.exclusive_mouse = True

        self.input = InputState()
        self.player = Player()
        self.sky = SkyCycle()
        self.world = World()

        atlas, uvs = ensure_textures_and_atlas()
        self.renderer = Renderer(self)
        self.renderer.upload_atlas(atlas, uvs)
        self.world.uvs = uvs

        # Preload chunks around spawn
        for cx in range(-2, 3):
            for cz in range(-2, 3):
                chunk = self.world.ensure_chunk((cx, cz))
                chunk.rebuild_mesh(self.world.uvs)
                self.renderer.rebuild_chunk(self.world, chunk)

        pyglet.clock.schedule_interval(self.update, 1.0 / 60.0)

    def on_draw(self):
        self.clear()
        self.renderer.draw_world(self.world, self.player.camera, self.sky.time_of_day)

    def update(self, dt: float):
        self.sky.update(dt)
        self.player.update(dt, self.input)
        self.input.reset_mouse()

    def on_key_press(self, symbol, modifiers):
        if symbol == key.W:
            self.input.move_forward = True
        elif symbol == key.S:
            self.input.move_back = True
        elif symbol == key.A:
            self.input.move_left = True
        elif symbol == key.D:
            self.input.move_right = True
        elif symbol == key.SPACE:
            self.input.jump = True
        elif symbol == key.LSHIFT:
            self.input.sneak = True
        elif symbol == key.ESCAPE:
            self.exclusive_mouse = False
            self.set_exclusive_mouse(False)

    def on_key_release(self, symbol, modifiers):
        if symbol == key.W:
            self.input.move_forward = False
        elif symbol == key.S:
            self.input.move_back = False
        elif symbol == key.A:
            self.input.move_left = False
        elif symbol == key.D:
            self.input.move_right = False
        elif symbol == key.SPACE:
            self.input.jump = False
        elif symbol == key.LSHIFT:
            self.input.sneak = False

    def on_mouse_press(self, x, y, button, modifiers):
        if not self.exclusive_mouse:
            self.exclusive_mouse = True
            self.set_exclusive_mouse(True)
            return
        if button == mouse.LEFT:
            self.mine_block()
        elif button == mouse.RIGHT:
            self.place_block()

    def on_mouse_motion(self, x, y, dx, dy):
        sens = 0.15
        self.player.camera.yaw += dx * sens
        self.player.camera.pitch -= dy * sens

    def mine_block(self):
        # Raycast forward to remove a block (very simplified)
        import glm
        origin = self.player.camera.position
        yaw = math.radians(self.player.camera.yaw)
        pitch = math.radians(self.player.camera.pitch)
        direction = glm.vec3(math.cos(yaw) * math.cos(pitch), math.sin(pitch), math.sin(yaw) * math.cos(pitch))
        pos = glm.vec3(origin)
        for _ in range(100):
            pos += direction * 0.5
            wx, wy, wz = int(math.floor(pos.x)), int(math.floor(pos.y)), int(math.floor(pos.z))
            if wy < 0 or wy >= 128:
                break
            cx, cz = wx // 16, wz // 16
            lx, lz = wx % 16, wz % 16
            chunk = self.world.ensure_chunk((cx, cz))
            if chunk.get_block(lx, wy, lz) != 0:
                chunk.set_block(lx, wy, lz, 0)
                chunk.rebuild_mesh(self.world.uvs)
                self.renderer.rebuild_chunk(self.world, chunk)
                break

    def place_block(self):
        # Place a block at the first empty voxel after a solid one along the ray
        import glm
        origin = self.player.camera.position
        yaw = math.radians(self.player.camera.yaw)
        pitch = math.radians(self.player.camera.pitch)
        direction = glm.vec3(math.cos(yaw) * math.cos(pitch), math.sin(pitch), math.sin(yaw) * math.cos(pitch))
        pos = glm.vec3(origin)
        previous_air = None
        for _ in range(100):
            pos += direction * 0.5
            wx, wy, wz = int(math.floor(pos.x)), int(math.floor(pos.y)), int(math.floor(pos.z))
            if wy < 0 or wy >= 128:
                break
            cx, cz = wx // 16, wz // 16
            lx, lz = wx % 16, wz % 16
            chunk = self.world.ensure_chunk((cx, cz))
            if chunk.get_block(lx, wy, lz) == 0:
                previous_air = (chunk, lx, wy, lz)
            else:
                if previous_air is not None:
                    ch, x, y, z = previous_air
                    ch.set_block(x, y, z, Blocks.by_name["planks"].id)
                    ch.rebuild_mesh(self.world.uvs)
                    self.renderer.rebuild_chunk(self.world, ch)
                break

    def run(self):
        pyglet.app.run()