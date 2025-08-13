import { Inventory, PlayerStats } from './rpg';

export class Hud {
  private level = document.getElementById('level')!;
  private hpFill = document.querySelector('#hp .fill') as HTMLElement;
  private stamFill = document.querySelector('#stam .fill') as HTMLElement;
  private manaFill = document.querySelector('#mana .fill') as HTMLElement;
  private xpFill = document.querySelector('#xp .fill') as HTMLElement;
  private hud = document.getElementById('hud')!;
  private hotbar = document.getElementById('hotbar')!;

  initHotbar(inv: Inventory) {
    this.hotbar.innerHTML = '';
    for (let i = 0; i < inv.slots.length; i++) {
      const slot = document.createElement('div');
      slot.className = 'slot' + (i === inv.selectedIndex ? ' active' : '');
      slot.textContent = inv.slots[i].id;
      this.hotbar.appendChild(slot);
    }
  }

  setSelected(index: number) {
    const nodes = Array.from(this.hotbar.children) as HTMLElement[];
    nodes.forEach((n, i) => {
      if (i === index) n.classList.add('active'); else n.classList.remove('active');
    });
  }

  show() { this.hud.setAttribute('style', ''); }

  update(stats: PlayerStats) {
    this.level.textContent = `Lv ${stats.level}`;
    const pct = (v: number, m: number) => `${Math.max(0, Math.min(1, v / m)) * 100}%`;
    this.hpFill.style.width = pct(stats.health, stats.maxHealth);
    this.stamFill.style.width = pct(stats.stamina, stats.maxStamina);
    this.manaFill.style.width = pct(stats.mana, stats.maxMana);
    this.xpFill.style.width = pct(stats.xp, stats.xpToNext);
  }
}