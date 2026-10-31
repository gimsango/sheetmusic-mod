// 파티클(불꽃/먼지/부스트) 풀
import * as THREE from 'three';

export class Particles {
  constructor(max = 700) {
    this.max = max; this.i = 0;
    this.pos = new Float32Array(max * 3); this.col = new Float32Array(max * 3); this.size = new Float32Array(max);
    this.vel = new Float32Array(max * 3); this.life = new Float32Array(max); this.maxLife = new Float32Array(max); this.base = new Float32Array(max);
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(this.pos, 3)); g.setAttribute('color', new THREE.BufferAttribute(this.col, 3));
    g.setAttribute('size', new THREE.BufferAttribute(this.size, 1));
    this.mat = new THREE.ShaderMaterial({
      transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
      uniforms: { scale: { value: 600 } },
      vertexShader: 'attribute float size; attribute vec3 color; varying vec3 vC; uniform float scale; void main(){ vC=color; vec4 mv = modelViewMatrix*vec4(position,1.0); gl_PointSize = size*scale/-mv.z; gl_Position = projectionMatrix*mv; }',
      fragmentShader: 'varying vec3 vC; void main(){ float d = length(gl_PointCoord-0.5); if(d>0.5) discard; float a = smoothstep(0.5,0.0,d); gl_FragColor = vec4(vC*a, a); }',
    });
    this.points = new THREE.Points(g, this.mat); this.points.frustumCulled = false; this.geo = g;
  }
  emit(x, y, z, vx, vy, vz, color, size, life) {
    const k = this.i; this.i = (this.i + 1) % this.max;
    this.pos[k * 3] = x; this.pos[k * 3 + 1] = y; this.pos[k * 3 + 2] = z;
    this.vel[k * 3] = vx; this.vel[k * 3 + 1] = vy; this.vel[k * 3 + 2] = vz;
    const c = new THREE.Color(color); this.col[k * 3] = c.r; this.col[k * 3 + 1] = c.g; this.col[k * 3 + 2] = c.b;
    this.base[k] = size; this.size[k] = size; this.life[k] = this.maxLife[k] = life;
  }
  update(dt, height) {
    this.mat.uniforms.scale.value = height * 0.9;
    for (let k = 0; k < this.max; k++) {
      if (this.life[k] <= 0) { this.size[k] = 0; continue; }
      this.life[k] -= dt;
      const f = Math.max(0, this.life[k] / this.maxLife[k]);
      this.pos[k * 3] += this.vel[k * 3] * dt; this.pos[k * 3 + 1] += this.vel[k * 3 + 1] * dt; this.pos[k * 3 + 2] += this.vel[k * 3 + 2] * dt;
      this.vel[k * 3 + 1] -= 6 * dt;
      this.size[k] = this.base[k] * (0.3 + f);
      const c = f; this.col[k * 3] *= 0.985; this.col[k * 3 + 1] *= 0.975; this.col[k * 3 + 2] *= 0.97; void c;
    }
    this.geo.attributes.position.needsUpdate = true; this.geo.attributes.color.needsUpdate = true; this.geo.attributes.size.needsUpdate = true;
  }
}
