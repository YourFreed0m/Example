from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class ItemStack:
    item: str
    count: int


class Inventory:
    def __init__(self):
        self.slots: List[ItemStack | None] = [None] * 36  # 27 main + 9 hotbar
        self.hotbar_index: int = 0

    def add(self, item: str, count: int = 1) -> None:
        # Try merge
        for s in self.slots:
            if s and s.item == item and s.count < 64:
                space = 64 - s.count
                take = min(space, count)
                s.count += take
                count -= take
                if count == 0:
                    return
        # Fill empties
        for i in range(len(self.slots)):
            if self.slots[i] is None:
                self.slots[i] = ItemStack(item, min(64, count))
                count -= min(64, count)
                if count == 0:
                    return

    def select_hotbar(self, idx: int) -> None:
        self.hotbar_index = max(0, min(8, idx))