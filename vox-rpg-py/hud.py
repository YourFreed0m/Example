from ursina import Entity, Text, Button, camera, Color
from typing import List


def clamp(v: float, lo: float, hi: float) -> float:
    return lo if v < lo else hi if v > hi else v


class Bar(Entity):
    def __init__(self, bar_color: Color = Color(1, 0, 0, 1), position=(0, 0)):
        super().__init__(
            parent=camera.ui,
            model='quad',
            color=Color(1, 1, 1, 0.12),
            origin=(-.5, 0),
            position=position,
            scale=(.22, .02),
        )
        self.fill = Entity(parent=self, model='quad', origin=(-.5, 0), color=bar_color, scale_x=0)

    def set_value(self, value: float, max_value: float):
        pct = 0.0 if max_value <= 0 else clamp(value / max_value, 0.0, 1.0)
        self.fill.scale_x = pct * .22


class HUD:
    def __init__(self, inventory_labels: List[str]):
        self.hp = Bar(Color(1.0, 70/255, 70/255, 1.0), position=(-.35, -.45))
        self.stamina = Bar(Color(70/255, 200/255, 70/255, 1.0), position=(-.35, -.48))
        self.mana = Bar(Color(70/255, 140/255, 1.0, 1.0), position=(-.35, -.51))
        self.xp = Bar(Color(240/255, 200/255, 50/255, 1.0), position=(-.35, -.54))

        self.level = Text(text='Lv 1', parent=camera.ui, position=(-.5, -.44), origin=(-.5, -.5), scale=1)

        self.hotbar_slots: List[Button] = []
        for i, label in enumerate(inventory_labels):
            b = Button(
                text=str(label),
                parent=camera.ui,
                position=(-.25 + i * .12, -.42),
                scale=(.1, .06),
                color=Color(0, 0, 0, 0.31),
            )
            self.hotbar_slots.append(b)
        self.set_selected(0)

        self.tooltip = Text(
            text='ЛКМ: ломать  ПКМ: ставить  1-5: слот  Esc: курсор',
            parent=camera.ui, position=(0, -.47), origin=(0, 0), scale=.8
        )

    def set_selected(self, index: int):
        for i, b in enumerate(self.hotbar_slots):
            b.color = Color(1, 1, 1, 0.24) if i == index else Color(0, 0, 0, 0.31)

    def update_stats(self, stats):
        self.level.text = f'Lv {stats.level}'
        self.hp.set_value(stats.health, stats.max_health)
        self.stamina.set_value(stats.stamina, stats.max_stamina)
        self.mana.set_value(stats.mana, stats.max_mana)
        self.xp.set_value(stats.xp, stats.xp_to_next)