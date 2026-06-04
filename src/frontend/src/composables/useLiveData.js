/**
 * Module-level singleton for polling the live snapshot of one pool.
 *
 * Pattern: this composable owns the polling timer and a single shared
 * snapshot ref. Every component that calls ``useLiveData()`` sees the
 * same state. Only one polling loop is active at a time; calling
 * ``start`` while already polling restarts the timer for the new pool.
 *
 * On fetch error the error is exposed but the polling continues so that
 * a transient network blip does not leave the UI frozen.
 */
import { computed, reactive, ref } from 'vue'
import { useApi } from './useApi.js'

const state = reactive({
  snapshot: null,
  loading: false,
  error: null,
  lastFetch: 0,
  pool: null,
  usingCached: false,
})

let _interval = null
let _running = false

async function _tick(pool) {
  const { fetchLive } = useApi()
  state.loading = true
  const snap = await fetchLive(pool)
  state.loading = false
  state.lastFetch = Date.now()
  if (snap) {
    state.snapshot = snap
    state.usingCached = false
    state.error = null
  } else {
    // Keep showing the last good snapshot, but flag it as cached.
    state.usingCached = state.snapshot !== null
  }
}

export function useLiveData() {
  async function start(pool, { intervalMs = 30000 } = {}) {
    if (!pool) return
    if (state.pool !== pool) {
      state.snapshot = null
      state.usingCached = false
      state.pool = pool
    }
    if (_running) {
      // Already polling; just switch the pool and reset the timer.
      clearInterval(_interval)
    }
    _running = true
    await _tick(pool)
    _interval = setInterval(() => {
      if (state.pool) _tick(state.pool)
    }, intervalMs)
  }

  function stop() {
    if (_interval) {
      clearInterval(_interval)
      _interval = null
    }
    _running = false
    state.pool = null
  }

  const stale = computed(() => {
    if (!state.snapshot) return true
    if (state.snapshot.stale) return true
    return state.usingCached
  })

  return {
    snapshot: computed(() => state.snapshot),
    loading: computed(() => state.loading),
    error: computed(() => state.error),
    usingCached: computed(() => state.usingCached),
    pool: computed(() => state.pool),
    lastFetch: computed(() => state.lastFetch),
    stale,
    start,
    stop,
  }
}
