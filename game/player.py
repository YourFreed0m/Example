from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Tuple
import glm


@dataclass
class Camera:
    position: glm.vec3
    yaw: float
    pitch: float

    def view_matrix(self) -> glm.mat4:
        # Clamp pitch
        self.pitch = max(-89.9, min(89.9, self.pitch))
        front = glm.vec3(
            math.cos(math.radians(self.yaw)) * math.cos(math.radians(self.pitch)),
            math.sin(math.radians(self.pitch)),
            math.sin(math.radians(self.yaw)) * math.cos(math.radians(self.pitch)),
        )
        center = self.position + glm.normalize(front)
        up = glm.vec3(0.0, 1.0, 0.0)
        return glm.lookAt(self.position, center, up)


class Player:
    def __init__(self):
        self.camera = Camera(position=glm.vec3(0.0, 80.0, 0.0), yaw=90.0, pitch=0.0)
        self.velocity = glm.vec3(0.0, 0.0, 0.0)
        self.speed = 6.0
        self.jump_strength = 6.0
        self.on_ground = False

    def update(self, dt: float, inputs) -> None:
        forward = glm.vec3(
            math.cos(math.radians(self.camera.yaw)), 0.0, math.sin(math.radians(self.camera.yaw))
        )
        right = glm.normalize(glm.cross(forward, glm.vec3(0.0, 1.0, 0.0)))
        forward = glm.normalize(glm.vec3(forward.x, 0.0, forward.z))

        wish = glm.vec3(0.0)
        if inputs.move_forward:
            wish += forward
        if inputs.move_back:
            wish -= forward
        if inputs.move_right:
            wish += right
        if inputs.move_left:
            wish -= right
        if glm.length(wish) > 0:
            wish = glm.normalize(wish)

        move_speed = self.speed * (0.5 if inputs.sneak else 1.0)
        self.velocity.x = wish.x * move_speed
        self.velocity.z = wish.z * move_speed

        # Gravity
        self.velocity.y -= 20.0 * dt
        if inputs.jump and self.on_ground:
            self.velocity.y = self.jump_strength
            self.on_ground = False

        # Integrate
        self.camera.position += self.velocity * dt

        # Simple ground collision at y=64 for now (until voxel collision is added)
        if self.camera.position.y < 64.0:
            self.camera.position.y = 64.0
            self.velocity.y = 0.0
            self.on_ground = True