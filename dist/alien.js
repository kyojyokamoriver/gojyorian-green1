import * as THREE from 'three';
import {GLTFLoader} from './assets/three/GLTFLoader.js';

const COUNT = 3;
const TURNS = 48;
const ATLAS_COLUMNS = 8;
const ATLAS_PADDING = 1.16;
const image = name => {
  const img = new Image();
  img.src = new URL('./assets/' + name, import.meta.url);
  return img;
};

export class AlienLayer {
  constructor(canvas) {
    this.open = image('alien-open.png');
    this.closed = image('alien-closed.png');
    this.turntable = image('alien-turntable.webp');
    this.sprites = [];
    this.ready = false;
    try {
      this.renderer = new THREE.WebGLRenderer({canvas, alpha:true, antialias:true});
    } catch {
      return;
    }
    this.renderer.setClearColor(0x000000, 0);
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.NoToneMapping;
    this.scene = new THREE.Scene();
    this.camera = new THREE.OrthographicCamera(0, 1, 0, -1, 1, 3000);
    this.camera.position.z = 1200;
    this.textures = new THREE.TextureLoader();
    const asset = path => new URL('./assets/' + path, import.meta.url).href;
    Promise.all([
      new GLTFLoader().loadAsync(asset('alien.glb')),
      ...[0,1].map(i => this.textures.loadAsync(asset('lid-' + i + '.png')))
    ]).then(([gltf, left, right]) => this.build(gltf.scene, left, right))
      .catch(() => { this.renderer.clear(); });
    canvas.addEventListener('webglcontextlost', () => { this.ready = false; });
    canvas.addEventListener('webglcontextrestored', () => { this.ready = this.sprites.length === COUNT; });
  }

  build(model, left, right) {
    const bounds = new THREE.Box3().setFromObject(model);
    const center = bounds.getCenter(new THREE.Vector3());
    const width = bounds.getSize(new THREE.Vector3()).x;
    const eyes = [];
    model.traverse(mesh => {
      if (mesh.isMesh && /polySurface[56]$/.test(mesh.name)) eyes.push(mesh);
    });
    if (eyes.length !== 2) return;
    for (const mesh of eyes) {
      const box = new THREE.Box3().setFromObject(mesh);
      const eyeCenter = box.getCenter(new THREE.Vector3());
      const texture = eyeCenter.x < center.x ? left : right;
      texture.colorSpace = THREE.SRGBColorSpace;
      const lid = new THREE.Mesh(
        new THREE.PlaneGeometry(.034, .0257),
        new THREE.MeshBasicMaterial({map:texture, transparent:true, alphaTest:.05})
      );
      lid.position.set(eyeCenter.x, eyeCenter.y - .0016, box.max.z + .0015);
      lid.name = mesh.name + '_lid';
      lid.visible = false;
      model.add(lid);
    }
    const centered = new THREE.Group();
    model.position.copy(center).multiplyScalar(-1);
    centered.add(model);
    centered.scale.setScalar(1 / width);
    for (let i = 0; i < COUNT; i++) {
      const item = centered.clone(true);
      const eyeMeshes = eyes.map(eye => item.getObjectByName(eye.name));
      const lids = eyes.map(eye => item.getObjectByName(eye.name + '_lid'));
      const group = new THREE.Group();
      group.visible = false;
      group.add(item);
      this.scene.add(group);
      this.sprites.push({group, eyeMeshes, lids});
    }
    this.ready = true;
  }

  resize(width, height, ratio) {
    if (!this.renderer) return;
    this.renderer.setPixelRatio(ratio);
    this.renderer.setSize(width, height, false);
    this.camera.right = width;
    this.camera.bottom = -height;
    this.camera.updateProjectionMatrix();
  }

  draw(objects, ctx) {
    if (!this.ready) {
      for (const obj of objects) {
        if (obj.turntable && this.turntable.naturalWidth) {
          const normalized = obj.yaw / (2*Math.PI);
          const frame = ((Math.round(normalized*TURNS)%TURNS)+TURNS)%TURNS;
          const tile = this.turntable.naturalWidth / ATLAS_COLUMNS;
          const size = obj.size * ATLAS_PADDING;
          ctx.drawImage(this.turntable, (frame%ATLAS_COLUMNS)*tile, Math.floor(frame/ATLAS_COLUMNS)*tile,
            tile, tile, obj.x-size/2, obj.y-size/2, size, size);
          continue;
        }
        const img = obj.blink && this.closed.complete ? this.closed : this.open;
        if (!img.naturalWidth) continue;
        const height = obj.size * img.naturalHeight / img.naturalWidth;
        ctx.save();
        ctx.translate(obj.x, obj.y);
        ctx.rotate(obj.roll);
        ctx.drawImage(img, -obj.size/2, -height/2, obj.size, height);
        ctx.restore();
      }
      return;
    }
    this.sprites.forEach(({group, eyeMeshes, lids}, i) => {
      const obj = objects[i];
      group.visible = Boolean(obj);
      if (!obj) return;
      group.position.set(obj.x, -obj.y, 3-i);
      group.rotation.set(obj.pitch, obj.yaw, -obj.roll);
      group.scale.setScalar(obj.size);
      eyeMeshes.forEach(mesh => { mesh.visible = !obj.blink; });
      lids.forEach(mesh => { mesh.visible = obj.blink; });
    });
    this.renderer.render(this.scene, this.camera);
  }

  capture(ctx, width, height) {
    if (!this.ready) return;
    this.renderer.render(this.scene, this.camera);
    ctx.drawImage(this.renderer.domElement, 0, 0, width, height);
  }
}
