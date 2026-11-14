import { useEffect, useRef, useState } from 'react'
import { Pause, Play, RotateCcw } from 'lucide-react'
import * as THREE from 'three'
import { Button } from '@/components/ui/button'

/** Arma el modelo del promotor (medidas aproximadas, en metros) a partir de las fotos del prototipo. */
function buildPrototype(): THREE.Group {
  const g = new THREE.Group()
  const mat = (color: number, rough = 0.6, metal = 0) =>
    new THREE.MeshStandardMaterial({ color, roughness: rough, metalness: metal })
  const add = (geo: THREE.BufferGeometry, m: THREE.Material, x: number, y: number, z: number) => {
    const mesh = new THREE.Mesh(geo, m)
    mesh.position.set(x, y, z)
    g.add(mesh)
    return mesh
  }

  const black = mat(0x16181b, 0.55)
  const wood = mat(0xa8703a, 0.85)
  const white = mat(0xf2f3f4, 0.35)

  // Báscula (tablero de madera) y los tres topes negros.
  add(new THREE.BoxGeometry(0.4, 0.02, 0.36), wood, 0, 0.01, 0)
  add(new THREE.BoxGeometry(0.07, 0.035, 0.1), black, -0.235, 0.0175, 0.04)
  add(new THREE.BoxGeometry(0.07, 0.035, 0.1), black, 0.235, 0.0175, 0.04)
  add(new THREE.BoxGeometry(0.1, 0.035, 0.07), black, 0, 0.0175, 0.215)

  // Base de los tubos, atrás del tablero.
  add(new THREE.BoxGeometry(0.34, 0.07, 0.07), black, 0, 0.055, -0.15)

  // Dos tubos blancos.
  const tube = new THREE.CylinderGeometry(0.013, 0.013, 1.0, 24)
  add(tube, white, -0.13, 0.57, -0.15)
  add(tube, white, 0.13, 0.57, -0.15)

  // Cabezal con la electrónica.
  add(new THREE.BoxGeometry(0.4, 0.05, 0.14), black, 0, 1.095, -0.15)
  add(new THREE.BoxGeometry(0.06, 0.05, 0.07), black, -0.13, 1.06, -0.15)
  add(new THREE.BoxGeometry(0.06, 0.05, 0.07), black, 0.13, 1.06, -0.15)

  // Cara superior: botón rojo, semáforo de LEDs y rejilla del zumbador.
  const top = 1.12
  add(new THREE.CylinderGeometry(0.018, 0.018, 0.014, 24), mat(0x0c0c0c), -0.13, top + 0.007, -0.17)
  const button = add(new THREE.CylinderGeometry(0.014, 0.014, 0.012, 24), mat(0xd42a2a, 0.4), -0.13, top + 0.016, -0.17)
  button.name = 'boton'
  const led = (color: number, x: number) =>
    add(
      new THREE.SphereGeometry(0.009, 16, 12),
      new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: 0.55, roughness: 0.3 }),
      x,
      top + 0.004,
      -0.17,
    )
  led(0xd42a2a, 0.02)
  led(0xe6c829, 0.055)
  led(0x2fa84f, 0.09)
  for (const dz of [-0.01, 0, 0.01]) add(new THREE.BoxGeometry(0.03, 0.002, 0.003), mat(0x050505), 0.15, top, -0.15 + dz)

  // Cara frontal: pantalla OLED y sensor de oxígeno.
  const front = -0.15 + 0.071
  add(new THREE.BoxGeometry(0.06, 0.03, 0.002), mat(0x0a1030, 0.2, 0.3), 0.1, 1.095, front)
  add(new THREE.BoxGeometry(0.022, 0.022, 0.002), mat(0x2a2d33, 0.3, 0.4), -0.05, 1.095, front)

  g.position.y = -0.55
  return g
}

/** Maqueta 3D del prototipo: se arrastra para girar, la rueda acerca y aleja. */
export default function PrototypeViewer() {
  const host = useRef<HTMLDivElement>(null)
  const control = useRef<{ reset: () => void; setSpin: (on: boolean) => void } | null>(null)
  const [failed, setFailed] = useState(false)
  const [spin, setSpin] = useState(true)

  useEffect(() => {
    const el = host.current
    if (!el) return

    let renderer: THREE.WebGLRenderer
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    } catch {
      setFailed(true)
      return
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    el.appendChild(renderer.domElement)
    renderer.domElement.style.display = 'block'
    renderer.domElement.style.touchAction = 'none'

    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(32, 1, 0.1, 50)
    scene.add(new THREE.HemisphereLight(0xffffff, 0x8a9a9a, 1.5))
    const sun = new THREE.DirectionalLight(0xffffff, 2.2)
    sun.position.set(2, 3, 2.5)
    scene.add(sun)

    const model = buildPrototype()
    scene.add(model)

    const view = { yaw: -0.6, pitch: 0.18, dist: 2.7 }
    const home = { ...view }
    let spinning = !window.matchMedia('(prefers-reduced-motion: reduce)').matches
    setSpin(spinning)
    let dragging = false
    let last = { x: 0, y: 0 }

    const resize = () => {
      const { clientWidth: w, clientHeight: h } = el
      renderer.setSize(w, h)
      camera.aspect = w / h
      camera.updateProjectionMatrix()
    }
    const ro = new ResizeObserver(resize)
    ro.observe(el)
    resize()

    const down = (e: PointerEvent) => {
      dragging = true
      last = { x: e.clientX, y: e.clientY }
      renderer.domElement.setPointerCapture(e.pointerId)
    }
    const move = (e: PointerEvent) => {
      if (!dragging) return
      view.yaw -= (e.clientX - last.x) * 0.01
      view.pitch = Math.max(-0.2, Math.min(1.2, view.pitch + (e.clientY - last.y) * 0.01))
      last = { x: e.clientX, y: e.clientY }
    }
    const up = () => (dragging = false)
    const wheel = (e: WheelEvent) => {
      e.preventDefault()
      view.dist = Math.max(1.6, Math.min(5, view.dist + e.deltaY * 0.002))
    }
    const key = (e: KeyboardEvent) => {
      if (e.key === 'ArrowLeft') view.yaw -= 0.15
      else if (e.key === 'ArrowRight') view.yaw += 0.15
      else if (e.key === 'ArrowUp') view.pitch = Math.min(1.2, view.pitch + 0.1)
      else if (e.key === 'ArrowDown') view.pitch = Math.max(-0.2, view.pitch - 0.1)
      else return
      e.preventDefault()
    }
    const cv = renderer.domElement
    cv.addEventListener('pointerdown', down)
    cv.addEventListener('pointermove', move)
    cv.addEventListener('pointerup', up)
    cv.addEventListener('pointercancel', up)
    cv.addEventListener('wheel', wheel, { passive: false })
    el.addEventListener('keydown', key)

    control.current = {
      reset: () => Object.assign(view, home),
      setSpin: (on) => (spinning = on),
    }

    let raf = 0
    const tick = () => {
      if (spinning && !dragging) view.yaw += 0.004
      camera.position.set(
        Math.sin(view.yaw) * Math.cos(view.pitch) * view.dist,
        Math.sin(view.pitch) * view.dist,
        Math.cos(view.yaw) * Math.cos(view.pitch) * view.dist,
      )
      camera.lookAt(0, 0, 0)
      renderer.render(scene, camera)
      raf = requestAnimationFrame(tick)
    }
    tick()

    return () => {
      cancelAnimationFrame(raf)
      ro.disconnect()
      el.removeEventListener('keydown', key)
      cv.removeEventListener('wheel', wheel)
      scene.traverse((o) => {
        if (o instanceof THREE.Mesh) {
          o.geometry.dispose()
          ;(o.material as THREE.Material).dispose()
        }
      })
      renderer.dispose()
      cv.remove()
      control.current = null
    }
  }, [])

  if (failed) return null

  return (
    <div className="relative h-80 w-full lg:h-full lg:min-h-96">
      <div
        ref={host}
        tabIndex={0}
        role="img"
        aria-label="Modelo 3D del promotor. Arrastra para girarlo; con el teclado usa las flechas."
        className="focus-visible:ring-ring size-full cursor-grab rounded-md outline-none focus-visible:ring-2 active:cursor-grabbing"
      />
      <div className="absolute right-2 bottom-2 flex gap-1">
        <Button
          type="button"
          variant="secondary"
          size="icon-sm"
          aria-label={spin ? 'Pausar giro' : 'Girar automáticamente'}
          onClick={() => {
            control.current?.setSpin(!spin)
            setSpin(!spin)
          }}
        >
          {spin ? <Pause /> : <Play />}
        </Button>
        <Button
          type="button"
          variant="secondary"
          size="icon-sm"
          aria-label="Restablecer vista"
          onClick={() => control.current?.reset()}
        >
          <RotateCcw />
        </Button>
      </div>
      <p className="text-muted-foreground pointer-events-none absolute bottom-2 left-3 text-xs">
        Arrastra para girar · rueda para acercar
      </p>
    </div>
  )
}
