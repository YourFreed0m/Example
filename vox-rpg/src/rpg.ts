export type PlayerStats = {
  level: number;
  xp: number;
  xpToNext: number;
  health: number;
  maxHealth: number;
  stamina: number;
  maxStamina: number;
  mana: number;
  maxMana: number;
};

export type Inventory = {
  selectedIndex: number;
  slots: { id: string; count: number }[];
};

export type SaveState = {
  stats: PlayerStats;
  inventory: Inventory;
  position: { x: number; y: number; z: number };
};

const STORAGE_KEY = 'vox_rpg_save_v1';

export function createInitialStats(): PlayerStats {
  return {
    level: 1,
    xp: 0,
    xpToNext: 50,
    health: 100,
    maxHealth: 100,
    stamina: 100,
    maxStamina: 100,
    mana: 50,
    maxMana: 50,
  };
}

export function addXp(stats: PlayerStats, amount: number): void {
  stats.xp += amount;
  while (stats.xp >= stats.xpToNext) {
    stats.xp -= stats.xpToNext;
    stats.level += 1;
    // Scale next level requirement and increase stats slightly
    stats.xpToNext = Math.floor(stats.xpToNext * 1.35 + 25);
    stats.maxHealth += 10;
    stats.maxStamina += 10;
    stats.maxMana += 5;
    stats.health = stats.maxHealth;
    stats.stamina = stats.maxStamina;
    stats.mana = Math.min(stats.maxMana, stats.mana + 10);
  }
}

export function regenTick(stats: PlayerStats, dt: number): void {
  // Stamina regen
  stats.stamina = Math.min(stats.maxStamina, stats.stamina + 8 * dt);
  // Mana regen
  stats.mana = Math.min(stats.maxMana, stats.mana + 3 * dt);
}

export function saveGame(state: SaveState): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {}
}

export function loadGame(): SaveState | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as SaveState;
  } catch {
    return null;
  }
}