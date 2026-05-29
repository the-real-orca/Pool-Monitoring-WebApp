<script setup>
import { ref } from 'vue'

const emit = defineEmits(['back'])

// Shared state for all variants
const temp1 = ref(24.5)
const temp2 = ref(24.5)
const temp3 = ref(24.5)
const temp4 = ref(24.5)
const temp5 = ref(24.5)
const temp6 = ref(24.5)

const showSlider3 = ref(false)
const showSlider4 = ref(false)
const showSlider6 = ref(false)

const MIN = 10
const MAX = 40
const STEP = 0.1

function clamp(val) {
  return Math.max(MIN, Math.min(MAX, parseFloat(val.toFixed(1))))
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-center text-xl font-bold text-slate-800">Slider Varianten</h1>
      <button
        type="button"
        @click="emit('back')"
        class="rounded-lg px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-slate-100"
      >
        Zurück
      </button>
    </div>

    <!-- Variante 1: Native HTML Range -->
    <div class="rounded-xl border border-slate-200 bg-slate-50 p-4">
      <p class="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Variante 1 – Native Range</p>
      <div class="flex items-center gap-3">
        <span class="w-16 text-lg font-bold text-slate-800">{{ temp1.toFixed(1) }}°C</span>
        <input
          v-model.number="temp1"
          type="range"
          :min="MIN"
          :max="MAX"
          :step="STEP"
          class="flex-1 accent-primary"
        />
      </div>
    </div>

    <!-- Variante 2: Custom styled range mit Track-Highlight -->
    <div class="rounded-xl border border-slate-200 bg-slate-50 p-4">
      <p class="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Variante 2 – Custom Track</p>
      <div class="flex items-center gap-3">
        <span class="w-16 text-lg font-bold text-slate-800">{{ temp2.toFixed(1) }}°C</span>
        <div class="relative flex-1">
          <input
            v-model.number="temp2"
            type="range"
            :min="MIN"
            :max="MAX"
            :step="STEP"
            class="slider-v2 w-full"
          />
        </div>
      </div>
    </div>

    <!-- Variante 3: Click-to-expand (Inline) -->
    <div class="rounded-xl border border-slate-200 bg-slate-50 p-4">
      <p class="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Variante 3 – Click to Expand (inline)</p>
      <div>
        <button
          type="button"
          @click="showSlider3 = !showSlider3"
          class="flex w-full items-center justify-between rounded-lg bg-white px-4 py-3 shadow-sm transition hover:shadow-md"
        >
          <span class="text-sm font-medium text-slate-600">Temperatur</span>
          <span class="text-lg font-bold text-primary">{{ temp3.toFixed(1) }}°C</span>
        </button>
        <div
          v-if="showSlider3"
          class="mt-3 overflow-hidden transition-all"
        >
          <div class="flex items-center gap-3 px-1">
            <span class="w-8 text-xs text-slate-400">{{ MIN }}°</span>
            <input
              v-model.number="temp3"
              type="range"
              :min="MIN"
              :max="MAX"
              :step="STEP"
              class="flex-1 accent-primary"
            />
            <span class="w-8 text-right text-xs text-slate-400">{{ MAX }}°</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Variante 4: Click-to-expand mit animiertem Slider -->
    <div class="rounded-xl border border-slate-200 bg-slate-50 p-4">
      <p class="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Variante 4 – Expand + Animate</p>
      <div>
        <button
          type="button"
          @click="showSlider4 = !showSlider4"
          class="flex w-full items-center justify-between rounded-lg bg-white px-4 py-3 shadow-sm transition hover:shadow-md"
        >
          <div class="flex items-center gap-2">
            <svg class="h-5 w-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
            <span class="text-sm font-medium text-slate-600">Temperatur</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-lg font-bold text-primary">{{ temp4.toFixed(1) }}°C</span>
            <svg
              class="h-4 w-4 text-slate-400 transition-transform"
              :class="{ 'rotate-180': showSlider4 }"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="2"
            >
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </button>
        <Transition name="slide">
          <div v-if="showSlider4" class="mt-3 px-1">
            <div class="rounded-lg bg-white p-3 shadow-inner">
              <input
                v-model.number="temp4"
                type="range"
                :min="MIN"
                :max="MAX"
                :step="STEP"
                class="slider-v4 w-full"
              />
              <div class="mt-1 flex justify-between text-xs text-slate-400">
                <span>{{ MIN }}°C</span>
                <span>{{ MAX }}°C</span>
              </div>
            </div>
          </div>
        </Transition>
      </div>
    </div>

    <!-- Variante 5: Immer sichtbar mit großem Slider + Farbzone -->
    <div class="rounded-xl border border-slate-200 bg-slate-50 p-4">
      <p class="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Variante 5 – Large + Color Zones</p>
      <div class="rounded-lg bg-white p-4 shadow-sm">
        <div class="mb-3 flex items-center justify-between">
          <span class="text-sm font-medium text-slate-600">Temperatur</span>
          <span
            class="rounded-full px-2.5 py-0.5 text-sm font-bold"
            :class="{
              'bg-blue-100 text-blue-700': temp5 < 20,
              'bg-green-100 text-green-700': temp5 >= 20 && temp5 <= 28,
              'bg-orange-100 text-orange-700': temp5 > 28 && temp5 <= 32,
              'bg-red-100 text-red-700': temp5 > 32,
            }"
          >
            {{ temp5.toFixed(1) }}°C
          </span>
        </div>
        <input
          v-model.number="temp5"
          type="range"
          :min="MIN"
          :max="MAX"
          :step="STEP"
          class="slider-v5 w-full"
        />
        <div class="mt-2 flex h-2 overflow-hidden rounded-full">
          <div class="bg-blue-400" style="width: 33%"></div>
          <div class="bg-green-400" style="width: 34%"></div>
          <div class="bg-orange-400" style="width: 17%"></div>
          <div class="bg-red-400" style="width: 16%"></div>
        </div>
        <div class="mt-1 flex justify-between text-xs text-slate-400">
          <span>kalt</span>
          <span>optimal</span>
          <span>warm</span>
          <span>heiß</span>
        </div>
      </div>
    </div>

    <!-- Variante 6: Compact Row – Klick öffnet Slider darunter -->
    <div class="rounded-xl border border-slate-200 bg-slate-50 p-4">
      <p class="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Variante 6 – Compact Row + Expand</p>
      <div class="space-y-2">
        <button
          type="button"
          @click="showSlider6 = !showSlider6"
          class="flex w-full items-center justify-between rounded-lg bg-white px-4 py-2.5 shadow-sm transition hover:shadow-md"
        >
          <div class="flex items-center gap-3">
            <div class="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10">
              <svg class="h-5 w-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            </div>
            <span class="text-sm font-medium text-slate-700">Temperatur</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-xl font-bold tabular-nums text-slate-800">{{ temp6.toFixed(1) }}</span>
            <span class="text-sm text-slate-400">°C</span>
          </div>
        </button>
        <Transition name="slide">
          <div v-if="showSlider6" class="rounded-lg bg-white p-3 shadow-inner">
            <input
              v-model.number="temp6"
              type="range"
              :min="MIN"
              :max="MAX"
              :step="STEP"
              class="slider-v6 w-full"
            />
          </div>
        </Transition>
      </div>
    </div>

  </div>
</template>

<style scoped>
/* Variante 2 – Custom Track */
input[type="range"].slider-v2 {
  -webkit-appearance: none;
  appearance: none;
  height: 8px;
  border-radius: 4px;
  background: linear-gradient(to right, #0ea5e9 0%, #0ea5e9 var(--val, 50%), #e2e8f0 var(--val, 50%), #e2e8f0 100%);
  outline: none;
}
input[type="range"].slider-v2::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #0ea5e9;
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(14, 165, 233, 0.4);
  border: 2px solid white;
}
input[type="range"].slider-v2::-moz-range-thumb {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #0ea5e9;
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(14, 165, 233, 0.4);
  border: 2px solid white;
}

/* Variante 4 – Expand + Animate */
input[type="range"].slider-v4 {
  -webkit-appearance: none;
  appearance: none;
  height: 10px;
  border-radius: 5px;
  background: #e2e8f0;
  outline: none;
}
input[type="range"].slider-v4::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: #0ea5e9;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.5);
  border: 3px solid white;
  transition: transform 0.15s;
}
input[type="range"].slider-v4::-webkit-slider-thumb:active {
  transform: scale(1.15);
}
input[type="range"].slider-v4::-moz-range-thumb {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: #0ea5e9;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.5);
  border: 3px solid white;
}

/* Variante 5 – Large + Color Zones */
input[type="range"].slider-v5 {
  -webkit-appearance: none;
  appearance: none;
  height: 12px;
  border-radius: 6px;
  background: #e2e8f0;
  outline: none;
}
input[type="range"].slider-v5::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: white;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  border: 3px solid #0ea5e9;
}
input[type="range"].slider-v5::-moz-range-thumb {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: white;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  border: 3px solid #0ea5e9;
}

/* Variante 6 – Compact */
input[type="range"].slider-v6 {
  -webkit-appearance: none;
  appearance: none;
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
  outline: none;
}
input[type="range"].slider-v6::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #0ea5e9;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 4px rgba(14, 165, 233, 0.3);
}
input[type="range"].slider-v6::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #0ea5e9;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 4px rgba(14, 165, 233, 0.3);
}

/* Slide Transition */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.25s ease-out;
}
.slide-enter-from {
  opacity: 0;
  transform: translateY(-8px);
}
.slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
