import { ref, onMounted } from 'vue'

export function useCamera() {
  const hasCamera = ref(false)

  onMounted(async () => {
    if (!navigator.mediaDevices?.enumerateDevices) return
    try {
      const devices = await navigator.mediaDevices.enumerateDevices()
      hasCamera.value = devices.some(d => d.kind === 'videoinput')
    } catch {
      hasCamera.value = false
    }
  })

  return { hasCamera }
}
