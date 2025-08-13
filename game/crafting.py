from __future__ import annotations
from typing import List, Tuple, Dict

# 3x3 grid positions: row-major indices 0..8

Recipe = Tuple[Tuple[str | None, ...], Tuple[str, int]]

RECIPES: List[Recipe] = [
    # Planks from log (anywhere 1x1)
    ((("log", None, None,
       None, None, None,
       None, None, None), ("planks", 4))),
    # Sticks from planks (column)
    (((None, "planks", None,
       None, "planks", None,
       None, None, None), ("stick", 4))),
]


def match_recipe(grid: Tuple[str | None, ...]) -> Tuple[str, int] | None:
    for pattern, result in RECIPES:
        ok = True
        for i in range(9):
            p = pattern[i]
            if p is None:
                continue
            if grid[i] != p:
                ok = False
                break
        if ok:
            return result
    return None