"use client"

import { Center, Float, OrbitControls, useGLTF } from "@react-three/drei"
import { Canvas, useFrame } from "@react-three/fiber"
import { Suspense, useEffect, useMemo, useRef, useState } from "react"
import type { Group, Mesh, MeshStandardMaterial } from "three"

const MODEL_URL = "/models/New_Project_512026.glb"

function HelmetModel() {
  const helmetRef = useRef<Group>(null)
  const { scene: sourceScene } = useGLTF(MODEL_URL)
  const scene = useMemo(() => sourceScene.clone(true), [sourceScene])

  // Tweak materials for a cleaner PBR look.
  useEffect(() => {
    scene.traverse((child) => {
      const mesh = child as Mesh
      if (!mesh.isMesh || !mesh.material) return

      mesh.castShadow = false
      mesh.receiveShadow = false

      const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material]
      for (const material of materials as MeshStandardMaterial[]) {
        if (typeof material.roughness === "number") material.roughness = Math.min(0.45, Math.max(0.08, material.roughness))
        if (typeof material.metalness === "number") material.metalness = Math.min(1, Math.max(0.15, material.metalness))
        if (typeof material.envMapIntensity === "number") material.envMapIntensity = Math.max(0.8, material.envMapIntensity || 1)
        material.needsUpdate = true
      }
    })
  }, [scene])

  useFrame((state) => {
    if (!helmetRef.current) return
    // slower rotation for a more premium, relaxed look
    helmetRef.current.rotation.y = state.clock.elapsedTime * 0.12
    helmetRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.4) * 0.04
  })

  return (
    <group ref={helmetRef} scale={2.25} position={[0, 0.18, 0]}>
      <Center>
        <primitive object={scene} dispose={null} />
      </Center>
    </group>
  )
}

export function HelmetScene() {
  const containerRef = useRef<HTMLDivElement>(null)
  const [inView, setInView] = useState(true)

  // Stop rendering frames while the preview is scrolled out of view.
  useEffect(() => {
    const element = containerRef.current
    if (!element) return
    const observer = new IntersectionObserver(([entry]) => setInView(entry.isIntersecting))
    observer.observe(element)
    return () => observer.disconnect()
  }, [])

  return (
    <div
      ref={containerRef}
      className="relative h-[480px] overflow-hidden rounded-[2rem] border border-white/10 bg-[radial-gradient(circle_at_center,rgba(56,189,248,0.14),rgba(2,6,23,0.98)_58%)] shadow-[0_30px_120px_rgba(2,6,23,0.55)] md:h-[580px]"
    >
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(135deg,rgba(255,255,255,0.08)_0%,transparent_20%,transparent_80%,rgba(255,255,255,0.06)_100%)]" />
      <Canvas
        camera={{ position: [0, 0.1, 4.6], fov: 40 }}
        shadows={false}
        dpr={[1, 1.2]}
        frameloop={inView ? "always" : "never"}
      >
        <color attach="background" args={["#020617"]} />
        <fog attach="fog" args={["#020617", 7, 14]} />
        <ambientLight intensity={0.85} />
        <directionalLight position={[4, 6, 4]} intensity={2.0} color="#dbeafe" />
        <spotLight position={[-4, 5, 2]} intensity={18} angle={0.28} penumbra={0.4} color="#38bdf8" />
        <spotLight position={[4, 1.5, -2]} intensity={12} angle={0.38} penumbra={0.35} color="#f97316" />
        <pointLight position={[-6, 2, -4]} intensity={8} color="#ffffff" />

        <Suspense fallback={null}>
          <Float speed={0.6} rotationIntensity={0.6} floatIntensity={1.1}>
            <HelmetModel />
          </Float>
        </Suspense>
        <OrbitControls enablePan={false} enableZoom={false} autoRotate autoRotateSpeed={0.18} />
      </Canvas>

      <div className="pointer-events-none absolute bottom-5 left-5 right-5 flex items-center justify-between text-xs uppercase tracking-[0.3em] text-white/60">
        <span>Live 3D preview</span>
        <span>Drag to rotate</span>
      </div>
    </div>
  )
}
