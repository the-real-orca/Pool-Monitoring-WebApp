// Runs before any test file is evaluated. Provides minimal stubs for
// browser APIs that jsdom does not implement but our deps need.

if (typeof window !== 'undefined' && !window.matchMedia) {
  window.matchMedia = (query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => {},
  })
}

// jsdom does not ship a real canvas implementation; uPlot and any other
// canvas-based lib expects getContext('2d') to return at least a stub.
// Provide a no-op 2d context that satisfies the methods uPlot touches.
if (typeof HTMLCanvasElement !== 'undefined') {
  HTMLCanvasElement.prototype.getContext = function () {
    const noop = () => {}
    return {
      canvas: this,
      save: noop, restore: noop, beginPath: noop,
      moveTo: noop, lineTo: noop, closePath: noop, clip: noop,
      translate: noop, rotate: noop, scale: noop,
      fillRect: noop, clearRect: noop, strokeRect: noop,
      fillText: noop, strokeText: noop, measureText: () => ({ width: 0 }),
      drawImage: noop,
      putImageData: noop, getImageData: () => ({ data: [] }),
      createImageData: () => ({}),
      setTransform: noop, resetTransform: noop,
      arc: noop, ellipse: noop, rect: noop,
      fill: noop, stroke: noop,
      setLineDash: noop, getLineDash: () => [],
      createLinearGradient: () => ({ addColorStop: noop }),
      createRadialGradient: () => ({ addColorStop: noop }),
      createPattern: () => ({}),
      bezierCurveTo: noop, quadraticCurveTo: noop,
      isPointInPath: () => false, isPointInStroke: () => false,
    }
  }
}

// jsdom also lacks Path2D, which uPlot uses internally to build series
// paths. Provide a minimal stub.
if (typeof window !== 'undefined' && !window.Path2D) {
  class Path2DStub {
    constructor() { this._ops = [] }
    moveTo() {} lineTo() {} closePath() {} arc() {} ellipse() {}
    rect() {} bezierCurveTo() {} quadraticCurveTo() {}
  }
  window.Path2D = Path2DStub
  if (typeof globalThis !== 'undefined') globalThis.Path2D = Path2DStub
}

// ResizeObserver is used by TrendChart for container-based resizing.
// jsdom has no native ResizeObserver; provide a passive stub.
if (typeof window !== 'undefined' && !window.ResizeObserver) {
  window.ResizeObserver = class {
    observe() {} unobserve() {} disconnect() {}
  }
}
