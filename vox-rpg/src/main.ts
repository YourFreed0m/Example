import * as THREE from 'three';
import { FirstPersonController } from './controls';
import { VoxelWorld, WorldMesh } from './world';
import { ALL_PLACEABLE, BlockId } from './types';
import { Hud } from './hud';
import { addXp, createInitialStats, loadGame, regenTick, saveGame, type Inventory, type PlayerStats } from './rpg';

const appEl = document.getElementById('app')!;
const startBtn = document.getElementById('startBtn')! as HTMLButtonElement;
const menu = document.getElementById('menu')!;

// Renderer
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
appEl.appendChild(renderer.domElement);

// Scene and lights
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x87ceeb);
const sun = new THREE.DirectionalLight(0xffffff, 1.0);
sun.position.set(1, 1.2, 0.8).multiplyScalar(20);
scene.add(sun);
scene.add(new THREE.AmbientLight(0xffffff, 0.35));

// World
const world = new VoxelWorld({ sizeX: 64, sizeZ: 64, maxHeight: 32, seed: 'vox-demo-seed' });
world.generate();
const worldMesh = new WorldMesh(world);
worldMesh.build();
scene.add(worldMesh.group);

// Player
let saved = loadGame();
let playerStats: PlayerStats = saved?.stats ?? createInitialStats();
let inventory: Inventory = saved?.inventory ?? {
  selectedIndex: 0,
  slots: ALL_PLACEABLE.map((id) => ({ id, count: 999 }))
};
let spawn = saved?.position ?? { x: 32.5, y: 40, z: 32.5 };
const controller = new FirstPersonController(75, window.innerWidth / window.innerHeight, renderer.domElement, new THREE.Vector3(spawn.x, spawn.y, spawn.z), world);

// HUD
const hud = new Hud();
const tooltip = document.getElementById('tooltip')!;
hud.initHotbar(inventory);

startBtn.onclick = () => {
  menu.style.display = 'none';
  hud.show();
  tooltip.style.opacity = '0.8';
  renderer.domElement.requestPointerLock();
};

// Raycaster for block interactions
const raycaster = new THREE.Raycaster();
raycaster.far = 6;

function tryBreakBlock(): void {
  raycaster.setFromCamera(new THREE.Vector2(0, 0), controller.camera);
  const hit = worldMesh.raycast(raycaster);
  if (!hit) return;
  const p = hit.position.clone().addScalar(-0.5);
  const x = Math.floor(p.x), y = Math.floor(p.y), z = Math.floor(p.z);
  world.setBlock(x, y, z, 'air');
  worldMesh.build();
  addXp(playerStats, 5);
}

function tryPlaceBlock(): void {
  raycaster.setFromCamera(new THREE.Vector2(0, 0), controller.camera);
  const hit = worldMesh.raycast(raycaster);
  if (!hit) return;
  const facePoint = hit.position.clone();
  // Find the face normal approximately by rounding delta from camera
  const from = controller.camera.position.clone();
  const dir = facePoint.clone().sub(from).normalize();
  const n = new THREE.Vector3(Math.round(dir.x), Math.round(dir.y), Math.round(dir.z));
  const placePos = facePoint.clone().add(n).addScalar(-0.5);
  const x = Math.floor(placePos.x), y = Math.floor(placePos.y), z = Math.floor(placePos.z);
  const id = inventory.slots[inventory.selectedIndex].id as BlockId;
  if (id === 'air') return;
  world.setBlock(x, y, z, id);
  worldMesh.build();
  addXp(playerStats, 2);
}

window.addEventListener('contextmenu', (e) => e.preventDefault());
renderer.domElement.addEventListener('mousedown', (e) => {
  if (document.pointerLockElement !== renderer.domElement) return;
  if (e.button === 0) tryBreakBlock();
  if (e.button === 2) tryPlaceBlock();
});

window.addEventListener('keydown', (e) => {
  if (e.code === 'Escape') {
    menu.style.display = 'grid';
    document.exitPointerLock();
  }
  if (/Digit[1-9]/.test(e.code)) {
    const idx = parseInt(e.code.replace('Digit', ''), 10) - 1;
    if (idx >= 0 && idx < inventory.slots.length) {
      inventory.selectedIndex = idx;
      hud.setSelected(idx);
    }
  }
});

// Resize
window.addEventListener('resize', () => {
  controller.camera.aspect = window.innerWidth / window.innerHeight;
  controller.camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

// Game loop
let last = performance.now();
const hudUpdater = () => hud.update(playerStats);

function tick(now: number) {
  const dt = Math.min(0.05, (now - last) / 1000);
  last = now;

  controller.update(dt);
  regenTick(playerStats, dt);

  renderer.render(scene, controller.camera);

  hudUpdater();
  requestAnimationFrame(tick);
}

requestAnimationFrame(tick);

// Save periodically
setInterval(() => {
  saveGame({
    stats: playerStats,
    inventory,
    position: controller.camera.position
  });
}, 2000);