import { reactive } from 'vue'

const toast = reactive({ message: '', type: 'success', visible: false })
let _timer = null

export function useToast() {
  function show(message, type = 'success', duration = 4000) {
    clearTimeout(_timer)
    Object.assign(toast, { message, type, visible: true })
    _timer = setTimeout(() => { toast.visible = false }, duration)
  }
  return { toast, show }
}
