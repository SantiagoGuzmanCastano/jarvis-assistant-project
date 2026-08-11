type Constellation = {
  name: string
  path: string
  nodes: readonly (readonly [number, number])[]
}

const constellations: readonly Constellation[] = [
  {
    name: 'orion',
    path: 'M 82 190 L 148 144 L 207 204 L 250 264 L 293 326 L 347 285 L 405 350 M 207 204 L 293 326',
    nodes: [[82, 190], [148, 144], [207, 204], [250, 264], [293, 326], [347, 285], [405, 350]],
  },
  {
    name: 'lyra',
    path: 'M 452 76 L 501 131 L 560 101 L 579 168 L 525 204 L 475 170 L 501 131',
    nodes: [[452, 76], [501, 131], [560, 101], [579, 168], [525, 204], [475, 170]],
  },
  {
    name: 'cygnus',
    path: 'M 754 127 L 798 194 L 850 265 L 903 206 M 850 265 L 910 324 L 949 383',
    nodes: [[754, 127], [798, 194], [850, 265], [903, 206], [910, 324], [949, 383]],
  },
  {
    name: 'pegasus',
    path: 'M 134 525 L 211 477 L 285 535 L 253 614 L 174 600 Z M 285 535 L 367 480 L 430 528',
    nodes: [[134, 525], [211, 477], [285, 535], [253, 614], [174, 600], [367, 480], [430, 528]],
  },
  {
    name: 'ursa',
    path: 'M 650 517 L 714 468 L 779 502 L 824 452 L 883 491 L 923 562 L 860 608',
    nodes: [[650, 517], [714, 468], [779, 502], [824, 452], [883, 491], [923, 562], [860, 608]],
  },
]

const stars = Array.from({ length: 96 }, (_, index) => {
  const x = 18 + ((Math.sin(index * 68.91) + 1) / 2) * 964
  const y = 14 + ((Math.sin(index * 127.7 + 1.4) + 1) / 2) * 672
  return { x, y, radius: 0.55 + ((index * 17) % 9) / 10, tier: index % 4 }
})

export function ConstellationBackground() {
  return (
    <div className="constellation-background" aria-hidden="true">
      <svg aria-hidden="true" focusable="false" role="presentation" viewBox="0 0 1000 700" preserveAspectRatio="xMidYMid slice">
        <defs>
          <linearGradient id="celestial-line" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#80dcff" />
            <stop offset=".52" stopColor="#a99dff" />
            <stop offset="1" stopColor="#6572c9" />
          </linearGradient>
          <radialGradient id="celestial-haze" cx="50%" cy="50%" r="50%">
            <stop stopColor="#5a50c8" stopOpacity=".16" />
            <stop offset="1" stopColor="#5a50c8" stopOpacity="0" />
          </radialGradient>
          <filter id="star-glow" x="-100%" y="-100%" width="300%" height="300%">
            <feGaussianBlur stdDeviation="2.2" />
          </filter>
        </defs>
        <ellipse className="celestial-haze haze-one" cx="180" cy="180" rx="230" ry="180" fill="url(#celestial-haze)" />
        <ellipse className="celestial-haze haze-two" cx="816" cy="530" rx="250" ry="180" fill="url(#celestial-haze)" />
        <g className="star-field">
          {stars.map((star, index) => <circle key={index} className={`star tier-${star.tier}`} cx={star.x} cy={star.y} r={star.radius} />)}
        </g>
        {constellations.map((constellation) => (
          <g key={constellation.name} className={`constellation constellation-${constellation.name}`}>
            <path pathLength="1" d={constellation.path} />
            {constellation.nodes.map(([cx, cy], nodeIndex) => (
              <g key={`${cx}-${cy}`}>
                <circle className="node-halo" cx={cx} cy={cy} r="5" filter="url(#star-glow)" />
                <circle className={`node node-${nodeIndex % 3}`} cx={cx} cy={cy} r={nodeIndex % 3 === 0 ? '2.35' : '1.65'} />
              </g>
            ))}
            <text x={constellation.nodes[0][0] + 10} y={constellation.nodes[0][1] - 9}>{constellation.name}</text>
          </g>
        ))}
      </svg>
    </div>
  )
}
