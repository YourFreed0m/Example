import * as THREE from 'three';

const appEl = document.getElementById('app');
const pickBtn = document.getElementById('pick');

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
appEl.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0b0e13);

const camera = new THREE.PerspectiveCamera(70, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(0, 2, 6);

scene.add(new THREE.DirectionalLight(0xffffff, 1.1)).position.set(1, 2, 1);
scene.add(new THREE.AmbientLight(0x555555));

const laneWidth = 1.2;
for (let i = -1; i <= 1; i++) {
  const geom = new THREE.PlaneGeometry(1000, laneWidth);
  const mat = new THREE.MeshBasicMaterial({ color: 0x1c2430, side: THREE.DoubleSide });
  const mesh = new THREE.Mesh(geom, mat);
  mesh.rotation.x = -Math.PI / 2;
  mesh.position.set(i * laneWidth, 0, -500);
  scene.add(mesh);
}

const riderGeom = new THREE.TorusGeometry(0.3, 0.12, 8, 16);
const riderMat = new THREE.MeshStandardMaterial({ color: 0xffcc00, emissive: 0x331a00, metalness: 0.3, roughness: 0.6 });
const rider = new THREE.Mesh(riderGeom, riderMat);
rider.position.set(0, 0.35, 0);
scene.add(rider);

let speed = 10;
let jumpV = 0;

const pickups = [];
const pickupGeom = new THREE.SphereGeometry(0.15, 12, 12);
const pickupMat = new THREE.MeshStandardMaterial({ color: 0x00d1ff, emissive: 0x002233 });

let audioCtx = null;
let analyser = null;
let dataArray = null;
let audio = null; // HTMLAudioElement to feed MediaElementAudioSourceNode

async function loadAudioFile(filePath) {
  // Use <audio> with file:// path
  if (!audio) {
    audio = new Audio();
    audio.crossOrigin = 'anonymous';
  }
  audio.src = 'file://' + filePath.replace(/\\/g, '/');
  await audio.play().catch(() => {});

  if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  const src = audioCtx.createMediaElementSource(audio);
  analyser = audioCtx.createAnalyser();
  analyser.fftSize = 1024;
  src.connect(analyser);
  analyser.connect(audioCtx.destination);
  dataArray = new Uint8Array(analyser.frequencyBinCount);
}

pickBtn.onclick = async () => {
  const filePath = await window.as.pickAudio();
  if (!filePath) return;
  await loadAudioFile(filePath);
};

// Mouse-only controls
let targetLaneX = 0;
window.addEventListener('mousemove', (e) => {
  const nx = e.clientX / window.innerWidth; // 0..1
  const lane = Math.round(nx * 2) - 1; // -1..1
  targetLaneX = lane * laneWidth;
});
window.addEventListener('wheel', (e) => {
  speed = Math.max(4, Math.min(40, speed + (e.deltaY < 0 ? 2 : -2)));
});
window.addEventListener('mousedown', () => {
  if (rider.position.y <= 0.351) jumpV = 6;
});

function spawnPickup(zPos) {
  const m = new THREE.Mesh(pickupGeom, pickupMat.clone());
  const laneIndex = (-1 + Math.floor(Math.random() * 3));
  m.position.set(laneIndex * laneWidth, 0.2, zPos);
  pickups.push(m);
  scene.add(m);
}

let last = performance.now();
let beatTimer = 0;

function tick(now) {
  const dt = Math.min(0.05, (now - last) / 1000);
  last = now;

  // Move rider towards lane by mouse X
  rider.position.x += (targetLaneX - rider.position.x) * Math.min(1, dt * 10);

  if (jumpV > 0 || rider.position.y > 0.35) {
    rider.position.y += jumpV * dt;
    jumpV -= 18 * dt;
    if (rider.position.y <= 0.35) { rider.position.y = 0.35; jumpV = 0; }
  }

  scene.traverse((obj) => {
    if (obj !== rider && obj !== camera) {
      obj.position && (obj.position.z += speed * dt);
    }
  });

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

  for (let i = pickups.length - 1; i >= 0; i--) {
    const p = pickups[i];
    if (p.position.distanceTo(rider.position) < 0.5 && p.position.z > -1) {
      scene.remove(p);
      pickups.splice(i, 1);
    }
    if (p.position.z > 10) {
      scene.remove(p);
      pickups.splice(i, 1);
    }
  }

  camera.position.z = rider.position.z + 6;
  camera.position.x += (rider.position.x - camera.position.x) * 0.1;
  camera.lookAt(new THREE.Vector3(rider.position.x, rider.position.y, rider.position.z - 2));

  renderer.render(scene, camera);
  requestAnimationFrame(tick);
}

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

requestAnimationFrame(tick);