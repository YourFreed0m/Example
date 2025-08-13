import * as THREE from 'three';

const appEl = document.getElementById('app')!;
const fileInput = document.getElementById('file') as HTMLInputElement;
const startBtn = document.getElementById('start') as HTMLButtonElement;

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
appEl.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0b0e13);

const camera = new THREE.PerspectiveCamera(70, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(0, 2, 5);

const light = new THREE.DirectionalLight(0xffffff, 1.2);
light.position.set(1, 2, 1);
scene.add(light);
scene.add(new THREE.AmbientLight(0x666666));

// Lanes (3 lanes: -1, 0, 1)
const trackGroup = new THREE.Group();
scene.add(trackGroup);
const laneZ = 0;
const laneWidth = 1.2;
for (let i = -1; i <= 1; i++) {
  const geom = new THREE.PlaneGeometry(1000, laneWidth);
  const mat = new THREE.MeshBasicMaterial({ color: 0x1c2430, side: THREE.DoubleSide });
  const mesh = new THREE.Mesh(geom, mat);
  mesh.rotation.x = -Math.PI / 2;
  mesh.position.set(i * laneWidth, 0, -500);
  trackGroup.add(mesh);
}

// Player
const riderGeom = new THREE.TorusGeometry(0.3, 0.12, 8, 16);
const riderMat = new THREE.MeshStandardMaterial({ color: 0xffcc00, emissive: 0x331a00, metalness: 0.3, roughness: 0.6 });
const rider = new THREE.Mesh(riderGeom, riderMat);
rider.position.set(0, 0.35, 0);
scene.add(rider);

let lane = 0; // -1, 0, 1
let speed = 10; // units per second
let jumpV = 0;

// Pickups
const pickups: THREE.Mesh[] = [];
const pickupGeom = new THREE.SphereGeometry(0.15, 12, 12);
const pickupMat = new THREE.MeshStandardMaterial({ color: 0x00d1ff, emissive: 0x002233 });

// Audio
let audioCtx: AudioContext | null = null;
let analyser: AnalyserNode | null = null;
let srcNode: AudioBufferSourceNode | MediaElementAudioSourceNode | null = null;
let dataArray: Uint8Array | null = null;

function setupAudio(buffer: AudioBuffer) {
  audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
  analyser = audioCtx.createAnalyser();
  analyser.fftSize = 1024;
  const source = audioCtx.createBufferSource();
  source.buffer = buffer;
  source.connect(analyser);
  analyser.connect(audioCtx.destination);
  srcNode = source;
  dataArray = new Uint8Array(analyser.frequencyBinCount);
}

async function decodeSelectedFile(file: File): Promise<AudioBuffer> {
  const arrayBuffer = await file.arrayBuffer();
  const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
  const buffer = await ctx.decodeAudioData(arrayBuffer.slice(0));
  ctx.close();
  return buffer;
}

startBtn.onclick = async () => {
  if (!fileInput.files || fileInput.files.length === 0) return;
  const buffer = await decodeSelectedFile(fileInput.files[0]);
  setupAudio(buffer);
  (srcNode as AudioBufferSourceNode).start();
  startBtn.disabled = true;
};

function spawnPickup(zPos: number) {
  const m = new THREE.Mesh(pickupGeom, pickupMat.clone());
  const laneIndex = (-1 + Math.floor(Math.random() * 3));
  m.position.set(laneIndex * laneWidth, 0.2, zPos);
  pickups.push(m);
  scene.add(m);
}

let last = performance.now();
let beatTimer = 0;

function tick(now: number) {
  const dt = Math.min(0.05, (now - last) / 1000);
  last = now;

  // Input
  if ((window as any).keys) {
    const keys = (window as any).keys as Set<string>;
    if (keys.has('KeyA')) lane = Math.max(-1, lane - 1);
    if (keys.has('KeyD')) lane = Math.min(1, lane + 1);
    if (keys.has('KeyW')) speed = Math.min(40, speed + 20 * dt);
    if (keys.has('KeyS')) speed = Math.max(4, speed - 20 * dt);
    if (keys.has('Space') && rider.position.y <= 0.351) jumpV = 6;
  }

  // Rider movement
  const targetX = lane * laneWidth;
  rider.position.x += (targetX - rider.position.x) * Math.min(1, dt * 10);

  // Jump physics
  if (jumpV > 0 || rider.position.y > 0.35) {
    rider.position.y += jumpV * dt;
    jumpV -= 18 * dt;
    if (rider.position.y <= 0.35) { rider.position.y = 0.35; jumpV = 0; }
  }

  // Move world backwards to simulate forward motion
  scene.traverse((obj) => {
    if (obj !== rider && obj !== camera) {
      (obj as any).position && ((obj as any).position.z += speed * dt);
    }
  });

  // Spawn pickups based on beat intensity
  if (analyser && dataArray) {
    analyser.getByteFrequencyData(dataArray);
    const bass = dataArray[1] + dataArray[2] + dataArray[3];
    const intensity = bass / (3 * 255);
    beatTimer += dt * (0.5 + intensity * 4);
    if (beatTimer >= 1) {
      beatTimer = 0;
      spawnPickup(-60 - Math.random() * 30);
    }
  }

  // Collect pickups
  for (let i = pickups.length - 1; i >= 0; i--) {
    const p = pickups[i];
    if (p.position.distanceTo(rider.position) < 0.5 && p.position.z > -1) {
      scene.remove(p);
      pickups.splice(i, 1);
    }
    // Cleanup passed pickups
    if (p.position.z > 10) {
      scene.remove(p);
      pickups.splice(i, 1);
    }
  }

  // Camera follow
  camera.position.z = rider.position.z + 6;
  camera.position.x += (rider.position.x - camera.position.x) * 0.1;
  camera.lookAt(new THREE.Vector3(rider.position.x, rider.position.y, rider.position.z - 2));

  renderer.render(scene, camera);
  requestAnimationFrame(tick);
}

// Simple keyboard tracking
(function installKeys(){
  const set = new Set<string>();
  (window as any).keys = set;
  window.addEventListener('keydown', (e) => set.add(e.code));
  window.addEventListener('keyup', (e) => set.delete(e.code));
})();

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

requestAnimationFrame(tick);