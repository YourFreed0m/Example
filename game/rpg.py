from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class PassiveNode:
    id: str
    name: str
    description: str
    stat_mods: Dict[str, float]
    neighbors: List[str]


class PassiveTree:
    def __init__(self):
        # Minimal example tree
        self.nodes: Dict[str, PassiveNode] = {
            "root": PassiveNode("root", "Start", "Starting node", {}, ["speed1", "mine1"]),
            "speed1": PassiveNode("speed1", "+5% Move Speed", "Move faster", {"move_speed_pct": 5.0}, ["root", "speed2"]),
            "speed2": PassiveNode("speed2", "+10% Move Speed", "Move even faster", {"move_speed_pct": 10.0}, ["speed1"]),
            "mine1": PassiveNode("mine1", "+10% Mining Speed", "Mine faster", {"mine_speed_pct": 10.0}, ["root", "mine2"]),
            "mine2": PassiveNode("mine2", "+15% Mining Speed", "Mine much faster", {"mine_speed_pct": 15.0}, ["mine1"]),
            "hp1": PassiveNode("hp1", "+20 Max HP", "More durable", {"max_hp": 20.0}, ["root"]),
        }
        self.allocated: Dict[str, bool] = {"root": True}
        self.points_available: int = 3

    def can_allocate(self, node_id: str) -> bool:
        if node_id in self.allocated and self.allocated[node_id]:
            return False
        # Must be adjacent to an allocated node
        for n in self.nodes.values():
            if self.allocated.get(n.id) and node_id in n.neighbors:
                return True
        return False

    def allocate(self, node_id: str) -> bool:
        if self.points_available <= 0:
            return False
        if not self.can_allocate(node_id):
            return False
        self.allocated[node_id] = True
        self.points_available -= 1
        return True

    def total_mods(self) -> Dict[str, float]:
        out: Dict[str, float] = {}
        for nid, allocated in self.allocated.items():
            if not allocated:
                continue
            for k, v in self.nodes[nid].stat_mods.items():
                out[k] = out.get(k, 0.0) + v
        return out