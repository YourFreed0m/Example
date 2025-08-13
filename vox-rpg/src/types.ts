export type Vec3 = { x: number; y: number; z: number };

export type BlockId =
  | 'air'
  | 'grass'
  | 'dirt'
  | 'stone'
  | 'log'
  | 'plank'
  | 'sand'
  | 'water';

export const ALL_PLACEABLE: BlockId[] = ['grass', 'dirt', 'stone', 'log', 'plank'];

export function keyOf(x: number, y: number, z: number): string {
  return `${x},${y},${z}`;
}

export function parseKey(key: string): Vec3 {
  const [x, y, z] = key.split(',').map(Number);
  return { x, y, z };
}