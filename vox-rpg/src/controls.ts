import * as THREE from 'three';
import { VoxelWorld } from './world';

export class FirstPersonController {
  public camera: THREE.PerspectiveCamera;
  public domElement: HTMLElement;

  private yaw = 0;
  private pitch = 0;
  private velocity = new THREE.Vector3();
  private onGround = false;

  private keyState: Record<string, boolean> = {};

  // Player AABB (width x depth x height)
  private halfWidth = 0.3;
  private halfDepth = 0.3;
  private height = 1.8;
  private gravity = 18;
  private moveSpeed = 6;
  private jumpSpeed = 7.5;

  constructor(fov: number, aspect: number, domElement: HTMLElement, initialPos: THREE.Vector3, private world: VoxelWorld) {
    this.camera = new THREE.PerspectiveCamera(fov, aspect, 0.1, 1000);
    this.camera.position.copy(initialPos);
    this.domElement = domElement;

    this.bindEvents();
  }

  bindEvents() {
    document.addEventListener('keydown', (e) => { this.keyState[e.code] = true; });
    document.addEventListener('keyup', (e) => { this.keyState[e.code] = false; });

    this.domElement.addEventListener('click', () => {
      this.domElement.requestPointerLock();
    });

    document.addEventListener('pointerlockchange', () => {
      if (document.pointerLockElement === this.domElement) {
        document.addEventListener('mousemove', this.onMouseMove);
      } else {
        document.removeEventListener('mousemove', this.onMouseMove);
      }
    });
  }

  private onMouseMove = (e: MouseEvent) => {
    const sensitivity = 0.002;
    this.yaw -= e.movementX * sensitivity;
    this.pitch -= e.movementY * sensitivity;
    const maxPitch = Math.PI / 2 - 0.01;
    this.pitch = Math.max(-maxPitch, Math.min(maxPitch, this.pitch));
  };

  getDirection(): THREE.Vector3 {
    const dir = new THREE.Vector3(0, 0, -1);
    const euler = new THREE.Euler(this.pitch, this.yaw, 0, 'YXZ');
    dir.applyEuler(euler);
    return dir.normalize();
  }

  update(dt: number) {
    // Update camera rotation
    this.camera.rotation.set(this.pitch, this.yaw, 0, 'YXZ');

    // Movement input
    const dir = this.getDirection();
    const right = new THREE.Vector3().crossVectors(dir, new THREE.Vector3(0, 1, 0)).normalize();
    const forward = new THREE.Vector3(dir.x, 0, dir.z).normalize();

    const wish = new THREE.Vector3();
    if (this.keyState['KeyW']) wish.add(forward);
    if (this.keyState['KeyS']) wish.add(forward.clone().multiplyScalar(-1));
    if (this.keyState['KeyA']) wish.add(right.clone().multiplyScalar(-1));
    if (this.keyState['KeyD']) wish.add(right);

    if (wish.lengthSq() > 0) wish.normalize().multiplyScalar(this.moveSpeed);

    // Apply to velocity on xz
    this.velocity.x = wish.x;
    this.velocity.z = wish.z;

    // Gravity and jumping
    this.velocity.y -= this.gravity * dt;
    if (this.onGround && (this.keyState['Space'] || this.keyState['KeyZ'])) {
      this.velocity.y = this.jumpSpeed;
      this.onGround = false;
    }

    // Integrate and collide
    let next = this.camera.position.clone();
    next.x += this.velocity.x * dt;
    next = this.resolveCollisions(next, new THREE.Vector3(this.velocity.x * dt, 0, 0));

    next.z += this.velocity.z * dt;
    next = this.resolveCollisions(next, new THREE.Vector3(0, 0, this.velocity.z * dt));

    next.y += this.velocity.y * dt;
    const beforeY = next.y;
    next = this.resolveCollisions(next, new THREE.Vector3(0, this.velocity.y * dt, 0));

    this.onGround = this.velocity.y <= 0 && Math.abs(next.y - beforeY) < 1e-6 && this.isStandingOnBlock(next);

    this.camera.position.copy(next);
  }

  private isVoxelSolidAt(x: number, y: number, z: number): boolean {
    return this.world.isSolid(Math.floor(x), Math.floor(y), Math.floor(z));
  }

  private isStandingOnBlock(pos: THREE.Vector3): boolean {
    const feetY = pos.y - this.height / 2 - 0.01;
    for (let dx of [-this.halfWidth, this.halfWidth]) {
      for (let dz of [-this.halfDepth, this.halfDepth]) {
        if (this.isVoxelSolidAt(Math.floor(pos.x + dx), Math.floor(feetY), Math.floor(pos.z + dz))) return true;
      }
    }
    return false;
  }

  private resolveCollisions(pos: THREE.Vector3, delta: THREE.Vector3): THREE.Vector3 {
    const newPos = pos.clone();
    const minX = newPos.x - this.halfWidth;
    const maxX = newPos.x + this.halfWidth;
    const minY = newPos.y - this.height / 2;
    const maxY = newPos.y + this.height / 2;
    const minZ = newPos.z - this.halfDepth;
    const maxZ = newPos.z + this.halfDepth;

    const checkMinX = Math.floor(minX) - 1;
    const checkMaxX = Math.floor(maxX) + 1;
    const checkMinY = Math.floor(minY) - 1;
    const checkMaxY = Math.floor(maxY) + 1;
    const checkMinZ = Math.floor(minZ) - 1;
    const checkMaxZ = Math.floor(maxZ) + 1;

    // Only resolve along the axis of movement (delta)
    const axes: Array<'x' | 'y' | 'z'> = [];
    if (Math.abs(delta.x) > 1e-6) axes.push('x');
    if (Math.abs(delta.y) > 1e-6) axes.push('y');
    if (Math.abs(delta.z) > 1e-6) axes.push('z');

    for (let ax of axes) {
      for (let x = checkMinX; x <= checkMaxX; x++) {
        for (let y = checkMinY; y <= checkMaxY; y++) {
          for (let z = checkMinZ; z <= checkMaxZ; z++) {
            if (!this.world.isSolid(x, y, z)) continue;
            // Voxel AABB
            const vxMinX = x;
            const vxMaxX = x + 1;
            const vxMinY = y;
            const vxMaxY = y + 1;
            const vxMinZ = z;
            const vxMaxZ = z + 1;

            if (
              maxX > vxMinX && minX < vxMaxX &&
              maxY > vxMinY && minY < vxMaxY &&
              maxZ > vxMinZ && minZ < vxMaxZ
            ) {
              // Collision; push out along axis
              if (ax === 'x') {
                if (delta.x > 0) newPos.x = vxMinX - this.halfWidth - 1e-6; else newPos.x = vxMaxX + this.halfWidth + 1e-6;
                this.velocity.x = 0;
              } else if (ax === 'y') {
                if (delta.y > 0) newPos.y = vxMinY - this.height / 2 - 1e-6; else newPos.y = vxMaxY + this.height / 2 + 1e-6;
                this.velocity.y = 0;
              } else if (ax === 'z') {
                if (delta.z > 0) newPos.z = vxMinZ - this.halfDepth - 1e-6; else newPos.z = vxMaxZ + this.halfDepth + 1e-6;
                this.velocity.z = 0;
              }
            }
          }
        }
      }
    }

    return newPos;
  }
}