import * as THREE from 'three';
import { createNoise2D } from 'simplex-noise';
import { BlockId, keyOf, parseKey } from './types';

// Seeded PRNG helpers for deterministic terrain
function hashStringToNumber(str: string): number {
  let h = 2166136261 >>> 0;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

function mulberry32(seed: number): () => number {
  let t = seed >>> 0;
  return function () {
    t += 0x6D2B79F5;
    let r = Math.imul(t ^ (t >>> 15), 1 | t);
    r ^= r + Math.imul(r ^ (r >>> 7), 61 | r);
    return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
  };
}

export type WorldOptions = {
  sizeX: number;
  sizeZ: number;
  maxHeight: number;
  seed: string;
};

type BlockData = Map<string, BlockId>; // key "x,y,z" -> id

export class VoxelWorld {
  public options: WorldOptions;
  public blocks: BlockData = new Map();
  private noise2d: (x: number, y: number) => number;
  private solidSet: Set<string> = new Set();

  constructor(options: WorldOptions) {
    this.options = options;
    const prng = mulberry32(hashStringToNumber(options.seed));
    const noise = createNoise2D(prng);
    this.noise2d = (x, y) => noise(x, y);
  }

  generate(): void {
    const { sizeX, sizeZ, maxHeight } = this.options;
    for (let x = 0; x < sizeX; x++) {
      for (let z = 0; z < sizeZ; z++) {
        const hNoise = this.noise2d(x / 30, z / 30);
        const base = Math.floor((hNoise * 0.5 + 0.5) * (maxHeight - 8)) + 6; // 6..maxHeight
        for (let y = 0; y <= base; y++) {
          const id: BlockId = y === base ? 'grass' : y > base - 3 ? 'dirt' : 'stone';
          this.blocks.set(keyOf(x, y, z), id);
        }
        // Sparse trees
        const treeChance = this.noise2d((x + 1000) / 12, (z - 500) / 12);
        if (treeChance > 0.68 && base + 5 < this.options.maxHeight) {
          for (let ty = 1; ty <= 4; ty++) {
            this.blocks.set(keyOf(x, base + ty, z), 'log');
          }
          for (let dx = -2; dx <= 2; dx++) {
            for (let dz = -2; dz <= 2; dz++) {
              for (let dy = 3; dy <= 5; dy++) {
                if (Math.abs(dx) + Math.abs(dz) + (dy === 5 ? 1 : 0) <= 4) {
                  const px = x + dx, py = base + dy, pz = z + dz;
                  if (px >= 0 && pz >= 0 && px < sizeX && pz < sizeZ) {
                    this.blocks.set(keyOf(px, py, pz), 'plank');
                  }
                }
              }
            }
          }
        }
      }
    }
    this.rebuildSolidSet();
  }

  private rebuildSolidSet(): void {
    this.solidSet.clear();
    for (const [k, id] of this.blocks) {
      if (id !== 'air' && id !== 'water') this.solidSet.add(k);
    }
  }

  isSolid(x: number, y: number, z: number): boolean {
    return this.solidSet.has(keyOf(x, y, z));
  }

  getBlock(x: number, y: number, z: number): BlockId {
    return this.blocks.get(keyOf(x, y, z)) ?? 'air';
  }

  setBlock(x: number, y: number, z: number, id: BlockId): void {
    const k = keyOf(x, y, z);
    if (id === 'air') this.blocks.delete(k); else this.blocks.set(k, id);
    this.rebuildSolidSet();
  }
}

export function createBlockMaterial(id: BlockId): THREE.Material {
  switch (id) {
    case 'grass': return new THREE.MeshStandardMaterial({ color: 0x55aa55 });
    case 'dirt': return new THREE.MeshStandardMaterial({ color: 0x8b5a2b });
    case 'stone': return new THREE.MeshStandardMaterial({ color: 0x888888 });
    case 'log': return new THREE.MeshStandardMaterial({ color: 0x8b6b3b });
    case 'plank': return new THREE.MeshStandardMaterial({ color: 0xcaa472 });
    case 'sand': return new THREE.MeshStandardMaterial({ color: 0xdbc97f });
    case 'water': return new THREE.MeshStandardMaterial({ color: 0x3a71c4, transparent: true, opacity: 0.6 });
    default: return new THREE.MeshStandardMaterial({ color: 0xffffff });
  }
}

export class WorldMesh {
  public group: THREE.Group = new THREE.Group();
  private instancedByType: Map<BlockId, THREE.InstancedMesh> = new Map();
  private idToPositions: Map<BlockId, THREE.Vector3[]> = new Map();
  private box: THREE.BoxGeometry;

  constructor(private world: VoxelWorld) {
    this.box = new THREE.BoxGeometry(1, 1, 1);
  }

  build(): void {
    // Clear old
    this.group.clear();
    this.instancedByType.clear();
    this.idToPositions.clear();

    // Build list of visible blocks (at least one face exposed)
    const dirs = [
      [1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]
    ];

    const positionsByType = new Map<BlockId, THREE.Vector3[]>();

    for (const [k, id] of this.world.blocks) {
      if (id === 'air') continue;
      const { x, y, z } = parseKey(k);
      let visible = false;
      for (const [dx, dy, dz] of dirs) {
        const neighbor = this.world.getBlock(x + dx, y + dy, z + dz);
        if (neighbor === 'air' || neighbor === 'water') { visible = true; break; }
      }
      if (!visible) continue;
      const arr = positionsByType.get(id) ?? [];
      arr.push(new THREE.Vector3(x + 0.5, y + 0.5, z + 0.5));
      positionsByType.set(id, arr as THREE.Vector3[]);
    }

    // Create InstancedMeshes per type
    const dummy = new THREE.Object3D();
    for (const [id, positions] of positionsByType) {
      const material = createBlockMaterial(id);
      const mesh = new THREE.InstancedMesh(this.box, material, positions.length);
      mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
      for (let i = 0; i < positions.length; i++) {
        const p = positions[i];
        dummy.position.copy(p);
        dummy.updateMatrix();
        mesh.setMatrixAt(i, dummy.matrix);
      }
      mesh.computeBoundingSphere();
      this.group.add(mesh);
      this.instancedByType.set(id, mesh);
      this.idToPositions.set(id, positions);
    }
  }

  raycast(raycaster: THREE.Raycaster): { id: BlockId; position: THREE.Vector3; instanceId: number } | null {
    const objects = Array.from(this.instancedByType.values());
    const intersects = raycaster.intersectObjects(objects, false);
    if (intersects.length === 0) return null;
    const first = intersects[0];
    const mesh = first.object as THREE.InstancedMesh;
    const id = [...this.instancedByType.entries()].find(([, m]) => m === mesh)?.[0] as BlockId;
    if (!id || typeof first.instanceId !== 'number') return null;
    const positions = this.idToPositions.get(id)!;
    return { id, position: positions[first.instanceId].clone(), instanceId: first.instanceId };
  }
}