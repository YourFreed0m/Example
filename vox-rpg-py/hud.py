from ursina import *
from typing import List, Dict


class Bar(Entity):
    def __init__(self, color=color.rgb(255, 0, 0), **kwargs):
        super().__init__(parent=camera.ui, model='quad', color=color.rgba(255,255,255,30), origin=(-.5,0), scale=(.22,.02), **kwargs)
        self.fill = Entity(parent=self, model='quad', origin=(-.5,0), color=color, scale_x=0)

    def set_value(self, value: float, max_value: float):
        pct = 0 if max_value <= 0 else clamp(value / max_value, 0, 1)
        self.fill.scale_x = pct * .22


class HUD:
    def __init__(self, inventory_labels: List[str]):
        self.hp = Bar(color=color.rgb(255, 70, 70), position=(-.35,-.45))
        self.stamina = Bar(color=color.rgb(70, 200, 70), position=(-.35,-.48))
        self.mana = Bar(color=color.rgb(70, 140, 255), position=(-.35,-.51))
        self.xp = Bar(color=color.rgb(240, 200, 50), position=(-.35,-.54))
        self.level = Text(text='Lv 1', position=(-.5,-.44), origin=(-.5,-.5), scale=1)

        # Hotbar
        self.hotbar_slots: List[Button] = []
        for i, label in enumerate(inventory_labels):
            b = Button(text=label, parent=camera.ui, position=(-.25 + i*.12, -.42), scale=(.1,.06), color=color.rgba(0,0,0,80))
            self.hotbar_slots.append(b)
        self.set_selected(0)

        # Tooltip
        self.tooltip = Text(text='ЛКМ: ломать  ПКМ: ставить  1-5: слот  Esc: курсор', position=(0,-.47), origin=(0,0), scale=.8)

    def set_selected(self, index: int):
        for i, b in enumerate(self.hotbar_slots):
            b.highlight_color = color.white
            b.color = color.rgba(255,255,255,60) if i == index else color.rgba(0,0,0,80)

    def update_stats(self, stats):
        self.level.text = f'Lv {stats.level}'
        self.hp.set_value(stats.health, stats.max_health)
        self.stamina.set_value(stats.stamina, stats.max_stamina)
        self.mana.set_value(stats.mana, stats.max_mana)
        self.xp.set_value(stats.xp, stats.xp_to_next)