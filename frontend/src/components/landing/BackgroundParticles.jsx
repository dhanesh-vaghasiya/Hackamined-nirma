import { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";

const POINTS = 110;
const BOUNDS = { x: 15, y: 8, z: 5 };
const LINK_DISTANCE = 2.3;

function NetworkField() {
  const linesRef = useRef();
  const pointsRef = useRef();

  const { positions, velocity } = useMemo(() => {
    const pos = new Float32Array(POINTS * 3);
    const vel = new Float32Array(POINTS * 3);

    for (let i = 0; i < POINTS; i += 1) {
      const idx = i * 3;
      pos[idx] = (Math.random() - 0.5) * BOUNDS.x * 2;
      pos[idx + 1] = (Math.random() - 0.5) * BOUNDS.y * 2;
      pos[idx + 2] = (Math.random() - 0.5) * BOUNDS.z * 2;
      vel[idx] = (Math.random() - 0.5) * 0.012;
      vel[idx + 1] = (Math.random() - 0.5) * 0.01;
      vel[idx + 2] = (Math.random() - 0.5) * 0.006;
    }

    return { positions: pos, velocity: vel };
  }, []);

  const geometry = useMemo(() => {
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    return g;
  }, [positions]);

  useFrame(() => {
    const pos = geometry.attributes.position.array;

    for (let i = 0; i < POINTS; i += 1) {
      const idx = i * 3;
      pos[idx] += velocity[idx];
      pos[idx + 1] += velocity[idx + 1];
      pos[idx + 2] += velocity[idx + 2];

      if (Math.abs(pos[idx]) > BOUNDS.x) velocity[idx] *= -1;
      if (Math.abs(pos[idx + 1]) > BOUNDS.y) velocity[idx + 1] *= -1;
      if (Math.abs(pos[idx + 2]) > BOUNDS.z) velocity[idx + 2] *= -1;
    }

    geometry.attributes.position.needsUpdate = true;

    const lineVertices = [];
    for (let i = 0; i < POINTS; i += 1) {
      for (let j = i + 1; j < POINTS; j += 1) {
        const a = i * 3;
        const b = j * 3;
        const dx = pos[a] - pos[b];
        const dy = pos[a + 1] - pos[b + 1];
        const dz = pos[a + 2] - pos[b + 2];
        const distance = Math.sqrt(dx * dx + dy * dy + dz * dz);

        if (distance < LINK_DISTANCE) {
          lineVertices.push(pos[a], pos[a + 1], pos[a + 2]);
          lineVertices.push(pos[b], pos[b + 1], pos[b + 2]);
        }
      }
    }

    if (linesRef.current) {
      linesRef.current.geometry.setAttribute(
        "position",
        new THREE.BufferAttribute(new Float32Array(lineVertices), 3)
      );
      linesRef.current.geometry.attributes.position.needsUpdate = true;
    }
  });

  return (
    <group>
      <points ref={pointsRef} geometry={geometry}>
        <pointsMaterial
          color="#9FE870"
          size={0.06}
          transparent
          opacity={0.5}
          sizeAttenuation
        />
      </points>

      <lineSegments ref={linesRef}>
        <bufferGeometry />
        <lineBasicMaterial color="#7BD85A" transparent opacity={0.13} />
      </lineSegments>
    </group>
  );
}

const BackgroundParticles = () => {
  return (
    <div className="pointer-events-none fixed inset-0 z-0">
      <Canvas
        camera={{ position: [0, 0, 12], fov: 54 }}
        dpr={[1, 1.6]}
        gl={{ antialias: true, alpha: true }}
      >
        <ambientLight intensity={0.35} />
        <NetworkField />
      </Canvas>
    </div>
  );
};

export default BackgroundParticles;
