export async function compress(file, { maxEdge = 1920, quality = 0.8 } = {}) {
  const img = await createImageBitmap(file)
  let { width, height } = img
  if (width > height && width > maxEdge) {
    height = Math.round((height * maxEdge) / width)
    width = maxEdge
  } else if (height > maxEdge) {
    width = Math.round((width * maxEdge) / height)
    height = maxEdge
  }
  const canvas = new OffscreenCanvas(width, height)
  const ctx = canvas.getContext('2d')
  ctx.drawImage(img, 0, 0, width, height)
  const blob = await canvas.convertToBlob({ type: 'image/jpeg', quality })
  img.close()
  return new File([blob], file.name.replace(/\.[^.]+$/, '.jpg'), { type: 'image/jpeg' })
}
