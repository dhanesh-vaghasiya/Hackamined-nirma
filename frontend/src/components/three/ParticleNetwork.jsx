import { useRef, useMemo } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";

/* ── Particle Network Mesh ─────────────────────────────────────────── */
const PARTICLE_COUNT = 120;
const LINK_DISTANCE = 2.2;
const FOREST_COLOR = new THREE.Color("#97A87A");

function ParticleSystem() {
  const meshRef = useRef();
  const linesRef = useRef();
  const mouse = useRef({ x: 0, y: 0 });
  const { viewport } = useThree();

  // Generate initial positions & velocities
  const { positions, velocities } = useMemo(() => {
    const pos = [];
    const vel = [];
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      pos.push(
        (Math.random() - 0.5) * 14,
        (Math.random() - 0.5) * 10,
        (Math.random() - 0.5) * 6
      );
      vel.push(
        (Math.random() - 0.5) * 0.005,
        (Math.random() - 0.5) * 0.005,
        (Math.random() - 0.5) * 0.003
      );
    }
    return {
      positions: new Float32Array(pos),
      velocities: vel,
    };
  }, []);

  // Point geometry
  const geometry = useMemo(() => {
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    return geo;
  }, [positions]);

  // Track mouse in normalised coords
  useMemo(() => {
    const handler = (e) => {
      mouse.current.x = (e.clientX / window.innerWidth) * 2 - 1;
      mouse.current.y = -(e.clientY / window.innerHeight) * 2 + 1;
    };
    window.addEventListener("mousemove", handler);
    return () => window.removeEventListener("mousemove", handler);
  }, []);

  // Animate particles + rebuild links each frame
  useFrame(() => {
    const posArr = geometry.attributes.position.array;

    // Move particles
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      const ix = i * 3;
      posArr[ix] += velocities[ix];
      posArr[ix + 1] += velocities[ix + 1];
      posArr[ix + 2] += velocities[ix + 2];

      // Gentle mouse parallax
      posArr[ix] += mouse.current.x * 0.0008;
      posArr[ix + 1] += mouse.current.y * 0.0008;

      // Soft bounds
      if (Math.abs(posArr[ix]) > 7) velocities[ix] *= -1;
      if (Math.abs(posArr[ix + 1]) > 5) velocities[ix + 1] *= -1;
      if (Math.abs(posArr[ix + 2]) > 3) velocities[ix + 2] *= -1;
    }
    geometry.attributes.position.needsUpdate = true;

    // Build line segments between nearby particles
    const lineVerts = [];
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      for (let j = i + 1; j < PARTICLE_COUNT; j++) {
        const ix = i * 3, jx = j * 3;
        const dx = posArr[ix] - posArr[jx];
        const dy = posArr[ix + 1] - posArr[jx + 1];
        const dz = posArr[ix + 2] - posArr[jx + 2];
        const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
        if (dist < LINK_DISTANCE) {
          lineVerts.push(posArr[ix], posArr[ix + 1], posArr[ix + 2]);
          lineVerts.push(posArr[jx], posArr[jx + 1], posArr[jx + 2]);
        }
      }
    }

    if (linesRef.current) {
      const lineGeo = linesRef.current.geometry;
      lineGeo.setAttribute(
        "position",
        new THREE.BufferAttribute(new Float32Array(lineVerts), 3)
      );
      lineGeo.attributes.position.needsUpdate = true;
    }
  });

  return (
    <group>
      <points ref={meshRef} geometry={geometry}>
        <pointsMaterial
          color={FOREST_COLOR}
          size={0.06}
          transparent
          opacity={0.7}
          sizeAttenuation
        />
      </points>
      <lineSegments ref={linesRef}>
        <bufferGeometry />
        <lineBasicMaterial color={FOREST_COLOR} transparent opacity={0.12} />
      </lineSegments>
    </group>
  );
}

/* ── Exported 3D Background ────────────────────────────────────────── */
export default function ParticleNetwork() {
  return (
    <div className="fixed inset-0 z-0" style={{ background: "#121412" }}>
      <Canvas
        camera={{ position: [0, 0, 8], fov: 60 }}
        dpr={[1, 1.5]}
        gl={{ antialias: true, alpha: false }}
        style={{ background: "#121412" }}
      >
        <ambientLight intensity={0.3} />
        <ParticleSystem />
      </Canvas>
    </div>
  );
}
