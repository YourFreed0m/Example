from __future__ import annotations

class InputState:
    def __init__(self) -> None:
        self.move_forward = False
        self.move_back = False
        self.move_left = False
        self.move_right = False
        self.jump = False
        self.sneak = False
        self.mouse_dx = 0.0
        self.mouse_dy = 0.0

    def reset_mouse(self) -> None:
        self.mouse_dx = 0.0
        self.mouse_dy = 0.0