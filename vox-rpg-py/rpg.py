from dataclasses import dataclass, asdict
from typing import Dict, Any
import json
import pathlib

SAVE_PATH = pathlib.Path(__file__).resolve().parent / 'save.json'


@dataclass
class PlayerStats:
    level: int = 1
    xp: int = 0
    xp_to_next: int = 50
    health: float = 100
    max_health: float = 100
    stamina: float = 100
    max_stamina: float = 100
    mana: float = 50
    max_mana: float = 50

    def add_xp(self, amount: int):
        self.xp += amount
        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            self.xp_to_next = int(self.xp_to_next * 1.35 + 25)
            self.max_health += 10
            self.max_stamina += 10
            self.max_mana += 5
            self.health = self.max_health
            self.stamina = self.max_stamina
            self.mana = min(self.max_mana, self.mana + 10)

    def regen(self, dt: float):
        self.stamina = min(self.max_stamina, self.stamina + 8 * dt)
        self.mana = min(self.max_mana, self.mana + 3 * dt)


@dataclass
class Inventory:
    selected_index: int = 0
    slots: Any = None

    def __post_init__(self):
        if self.slots is None:
            self.slots = [
                { 'id': 'grass', 'count': 999 },
                { 'id': 'dirt', 'count': 999 },
                { 'id': 'stone', 'count': 999 },
                { 'id': 'log', 'count': 999 },
                { 'id': 'plank', 'count': 999 },
            ]


def save_game(data: Dict[str, Any]):
    try:
        with open(SAVE_PATH, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print('Failed to save game:', e)


def load_game() -> Dict[str, Any]:
    try:
        if SAVE_PATH.exists():
            with open(SAVE_PATH, 'r') as f:
                return json.load(f)
    except Exception as e:
        print('Failed to load game:', e)
    return {}