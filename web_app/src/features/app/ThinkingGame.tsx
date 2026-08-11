import { useState } from 'react'

type SceneProps = { className?: string }

const scenes = [BirdScene, RoverScene, SatelliteScene, ShipScene]
const sceneLabels = ['Vuelo orbital', 'Rover urbano', 'Satélite', 'Nave']
let sceneQueue: number[] = []
let previousSceneIndex: number | null = null

function nextSceneIndex() {
  if (sceneQueue.length === 0) {
    sceneQueue = scenes.map((_, index) => index)
    for (let index = sceneQueue.length - 1; index > 0; index -= 1) {
      const randomIndex = Math.floor(Math.random() * (index + 1))
      ;[sceneQueue[index], sceneQueue[randomIndex]] = [sceneQueue[randomIndex], sceneQueue[index]]
    }
    if (sceneQueue[0] === previousSceneIndex) {
      ;[sceneQueue[0], sceneQueue[1]] = [sceneQueue[1], sceneQueue[0]]
    }
  }

  const sceneIndex = sceneQueue.shift()!
  previousSceneIndex = sceneIndex
  return sceneIndex
}

export function ThinkingGame({ assistantName }: { assistantName: string }) {
  const [sceneIndex] = useState(nextSceneIndex)
  const Scene = scenes[sceneIndex]

  return <div className="thinking-game" role="status">
    <div className="thinking-game-top"><span className="thinking-game-dot" />{assistantName} está pensando</div>
    <div className={`thinking-track thinking-scene-${sceneIndex}`} aria-hidden="true"><Scene /></div>
  </div>
}

function BirdScene({ className }: SceneProps) {
  return <>
    <span className="orbital-starfield" />
    <span className="orbital-nebula" />
    <span className="orbital-planet"><i /></span>
    <span className="orbital-ring orbital-ring-one" />
    <span className="orbital-ring orbital-ring-two" />
    <span className="orbital-satellite"><i /><b /></span>
    <span className="orbital-trail" />
    <svg className={`thinking-bird ${className ?? ''}`} viewBox="0 0 42 28">
      <path className="bird-tail" d="M11 15 4 11l3 7-3 6 8-3Z" />
      <ellipse className="bird-body" cx="20" cy="16" rx="10" ry="7" />
      <path className="bird-wing" d="M17 13c6 1 9 5 7 9-5-1-8-4-9-8Z" />
      <path className="bird-beak" d="m29 15 7 2-7 3Z" />
      <circle className="bird-eye" cx="25.5" cy="13.5" r="1.25" />
    </svg>
    <span className="thinking-orbital-gate gate-one"><i className="gate-upper" /><i className="gate-lower" /></span>
    <span className="thinking-orbital-gate gate-two"><i className="gate-upper" /><i className="gate-lower" /></span>
    <span className="energy-orb orb-one" />
    <span className="energy-orb orb-two" />
    <span className="speed-line speed-line-one" />
    <span className="speed-line speed-line-two" />
  </>
}

function RoverScene({ className }: SceneProps) {
  return <>
    <span className="rover-atmosphere" />
    <span className="rover-starfield" />
    <span className="city-horizon" />
    <span className="city-road" />
    <div className="city-skyline city-back">
      <i /><i /><i /><i /><i /><i />
    </div>
    <div className="city-skyline city-front">
      <i /><i /><i /><i /><i />
    </div>
    <span className="city-moon" />
    <svg className={`thinking-rover ${className ?? ''}`} viewBox="0 0 48 28">
      <path className="rover-body" d="M8 13h25l5 7H9Z" />
      <path className="rover-window" d="M15 11h12l3 4H12Z" />
      <path className="rover-antenna" d="M29 11 33 5" />
      <circle className="rover-signal" cx="34" cy="4" r="1.6" />
      <circle className="rover-headlamp" cx="37" cy="17.5" r="1.35" />
      <circle className="rover-wheel rover-wheel-left" cx="16" cy="22" r="3.4" />
      <circle className="rover-wheel rover-wheel-right" cx="32" cy="22" r="3.4" />
    </svg>
    <span className="rover-headlight" />
    <span className="street-lamp lamp-one" />
    <span className="street-lamp lamp-two" />
    <span className="thinking-desert-line rover-ground" />
  </>
}

function SatelliteScene({ className }: SceneProps) {
  return <>
    <span className="satellite-starfield" />
    <span className="satellite-orbit" />
    <span className="planetary-system">
      <i className="system-sun" />
      <i className="system-orbit system-orbit-one"><b /></i>
      <i className="system-orbit system-orbit-two"><b /></i>
    </span>
    <span className="planetary-system planetary-system-secondary">
      <i className="system-sun" />
      <i className="system-orbit system-orbit-one"><b /></i>
      <i className="system-orbit system-orbit-two"><b /></i>
    </span>
    <svg className={`thinking-satellite ${className ?? ''}`} viewBox="0 0 52 34">
      <rect className="satellite-panel" x="1.5" y="13" width="13" height="9" rx="1.5" />
      <rect className="satellite-panel" x="37.5" y="13" width="13" height="9" rx="1.5" />
      <path className="satellite-panel-grid" d="M6 13v9m4-9v9m32-9v9m4-9v9" />
      <path className="satellite-connector" d="M14.5 17.5h4m15 0h4" />
      <path className="satellite-body" d="m18 11 4-3h9l4 3v13l-4 3h-9l-4-3Z" />
      <path className="satellite-cap" d="M21 9V6h11v3" />
      <circle className="satellite-core-ring" cx="26.5" cy="17.5" r="5" />
      <circle className="satellite-core" cx="26.5" cy="17.5" r="3.1" />
      <circle className="satellite-lens" cx="27.5" cy="16.5" r="1" />
      <path className="satellite-dish" d="M22 6c2-5 7-5 9 0M26.5 4V1.5" />
    </svg>
    <span className="scanner-rig">
      <span className="scanner-beam" />
    </span>
    <span className="capture-target target-one"><i /></span>
    <span className="capture-target target-two"><i /></span>
    <span className="capture-target target-three"><i /></span>
    <span className="capture-target target-four"><i /></span>
    <span className="capture-flash" />
    <span className="thinking-spark spark-one">✦</span>
    <span className="thinking-spark spark-three">✦</span>
  </>
}

function ShipScene({ className }: SceneProps) {
  return <>
    <span className="ship-nebula" />
    <span className="ship-starfield" />
    <span className="distant-moon moon-one" />
    <span className="distant-moon moon-two" />
    <span className="asteroid-belt" />
    <span className="ship-streak streak-one" />
    <span className="ship-streak streak-two" />
    <span className="ship-craft">
      <svg className={`thinking-ship ${className ?? ''}`} viewBox="0 0 56 32">
        <path className="ship-flame-outer" d="M13 13C7 11 3 13 1 16c2 3 6 5 12 3Z" />
        <path className="ship-flame-inner" d="M13 15c-4-1-7 0-9 1 2 2 5 2 9 1Z" />
        <path className="ship-wing ship-wing-top" d="m21 12 5-7 10 7Z" />
        <path className="ship-wing ship-wing-bottom" d="m21 20 5 7 10-7Z" />
        <path className="ship-body" d="M12 12c8-6 25-6 38 4-13 10-30 10-38 4Z" />
        <path className="ship-engine" d="M11 12h7v8h-7c-2-2-2-6 0-8Z" />
        <ellipse className="ship-window" cx="34" cy="14.5" rx="8" ry="5" />
        <circle className="ship-window-glint" cx="31.5" cy="12.5" r="1.3" />
        <circle className="ship-cheek-light" cx="45" cy="17" r="1.2" />
      </svg>
      <i className="engine-particle engine-particle-one" />
      <i className="engine-particle engine-particle-two" />
      <i className="engine-particle engine-particle-three" />
    </span>
    <span className="thinking-planet planet-one"><i /></span>
    <span className="thinking-planet planet-two"><i /></span>
    <span className="thinking-planet planet-three"><i /></span>
    <span className="thinking-spark spark-one">✦</span>
    <span className="thinking-spark spark-three">✦</span>
  </>
}

export function ThinkingGamePreview() {
  return <main className="thinking-preview">
    <section className="thinking-preview-card">
      <p className="eyebrow">Vista previa</p>
      <h1>Jarvis está pensando</h1>
      <p>Cuatro pequeñas historias que hacen que la espera se sienta más corta.</p>
      <div className="thinking-preview-grid">
        {scenes.map((Scene, index) => <div className="thinking-preview-scene" key={sceneLabels[index]}>
          <span>{sceneLabels[index]}</span>
          <div className={`thinking-track thinking-scene-${index}`} aria-hidden="true"><Scene /></div>
        </div>)}
      </div>
    </section>
  </main>
}
