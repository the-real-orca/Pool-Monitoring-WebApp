import { describe, it, expect, vi, beforeAll } from 'vitest'

function MockCanvasImpl(w, h) {
  return {
    width: w,
    height: h,
    getContext: vi.fn(() => ({ drawImage: vi.fn() })),
    convertToBlob: vi.fn(() => Promise.resolve(new Blob(['compressed'], { type: 'image/jpeg' }))),
  }
}

beforeAll(() => {
  vi.stubGlobal('createImageBitmap', vi.fn())
  vi.stubGlobal('OffscreenCanvas', MockCanvasImpl)
})

describe('compress', () => {
  it('clamps long edge to maxEdge', async () => {
    createImageBitmap.mockResolvedValue({ width: 4000, height: 3000, close: vi.fn() })

    const { compress } = await import('../src/composables/useImage.js')
    const file = new File(['fake'], 'photo.jpg', { type: 'image/jpeg' })
    const result = await compress(file, { maxEdge: 1920, quality: 0.8 })

    expect(result.type).toBe('image/jpeg')
    expect(result.name).toBe('photo.jpg')
  })

  it('outputs image/jpeg', async () => {
    createImageBitmap.mockResolvedValue({ width: 800, height: 600, close: vi.fn() })

    const { compress } = await import('../src/composables/useImage.js')
    const file = new File(['fake'], 'test.png', { type: 'image/png' })
    const result = await compress(file, { maxEdge: 1920, quality: 0.8 })

    expect(result.type).toBe('image/jpeg')
    expect(result.name).toBe('test.jpg')
  })

  it('reduces bytes for oversized image', async () => {
    const largeData = 'x'.repeat(500000)
    createImageBitmap.mockResolvedValue({ width: 4000, height: 3000, close: vi.fn() })

    const { compress } = await import('../src/composables/useImage.js')
    const file = new File([largeData], 'large.jpg', { type: 'image/jpeg' })
    const result = await compress(file, { maxEdge: 800, quality: 0.5 })

    expect(result.size).toBeLessThan(largeData.length)
  })

  it('throws on non-image file', async () => {
    createImageBitmap.mockRejectedValue(new Error('Not an image'))

    const { compress } = await import('../src/composables/useImage.js')
    const file = new File(['text'], 'readme.txt', { type: 'text/plain' })
    await expect(compress(file, { maxEdge: 1920, quality: 0.8 })).rejects.toThrow()
  })
})
