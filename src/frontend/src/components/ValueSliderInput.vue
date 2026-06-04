<script setup>
import { computed, ref, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({
  modelValue: { type: Number, default: null },
  min: { type: Number, required: true },
  max: { type: Number, required: true },
  step: { type: Number, required: true },
  decimals: { type: Number, required: true },
  unit: { type: String, default: '' },
  emptyValue: { type: Number, default: null },
})
const emit = defineEmits(['update:modelValue'])

const showSlider = ref(false)
const idleTimer = ref(null)
const releaseTimer = ref(null)
const isDragging = ref(false)
const overlayRef = ref(null)
const holdTimer = ref(null)

const hasValue = computed(() => typeof props.modelValue === 'number' && !Number.isNaN(props.modelValue))
const displayValue = computed(() => hasValue.value ? props.modelValue.toFixed(props.decimals) : '')

const rangeSteps = computed(() => {
  return Math.round((props.max - props.min) / props.step)
})

function valueToRange(val) {
  return Math.round((val - props.min) / props.step)
}

function rangeToValue(rangeVal) {
  const val = props.min + rangeVal * props.step
  return parseFloat(val.toFixed(props.decimals))
}

const sliderRangeValue = computed(() => hasValue.value ? valueToRange(props.modelValue) : 0)

const canDecrease = computed(() => hasValue.value && props.modelValue > props.min)
const canIncrease = computed(() => !hasValue.value || props.modelValue < props.max)

function openSlider() {
  showSlider.value = true
  resetIdleTimer()
}

function closeSlider() {
  showSlider.value = false
  clearTimers()
}

function resetIdleTimer() {
  clearTimers()
  idleTimer.value = setTimeout(() => {
    if (!isDragging.value) closeSlider()
  }, 5000)
}

function clearTimers() {
  if (idleTimer.value) clearTimeout(idleTimer.value)
  if (releaseTimer.value) clearTimeout(releaseTimer.value)
  idleTimer.value = null
  releaseTimer.value = null
  onHoldEnd()
}

function onDragStart() {
  isDragging.value = true
  clearTimers()
}

function onDragEnd() {
  isDragging.value = false
  releaseTimer.value = setTimeout(() => closeSlider(), 1000)
}

function onSliderInput(event) {
  const rangeVal = parseInt(event.target.value, 10)
  const val = rangeToValue(rangeVal)
  const clamped = Math.max(props.min, Math.min(props.max, val))
  emit('update:modelValue', clamped)
  resetIdleTimer()
}

function step(dir) {
  if (!hasValue.value) {
    if (dir > 0) {
      emit('update:modelValue', props.emptyValue ?? props.min)
    }
    return
  }

  const next = parseFloat((props.modelValue + dir * props.step).toFixed(props.decimals))
  if (next >= props.min && next <= props.max) {
    emit('update:modelValue', next)
  }
}

function onHoldStart(dir) {
  step(dir)
  holdTimer.value = setTimeout(() => {
    holdTimer.value = setInterval(() => step(dir), 100)
  }, 500)
}

function onHoldEnd() {
  if (holdTimer.value) {
    clearInterval(holdTimer.value)
    clearTimeout(holdTimer.value)
    holdTimer.value = null
  }
}

function onClickOutside(event) {
  if (showSlider.value && overlayRef.value && !overlayRef.value.contains(event.target)) {
    closeSlider()
  }
}

onMounted(() => {
  document.addEventListener('mousedown', onClickOutside)
  document.addEventListener('touchstart', onClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('mousedown', onClickOutside)
  document.removeEventListener('touchstart', onClickOutside)
  clearTimers()
})
</script>

<template>
  <div class="relative w-full">
    <!-- Normal stepper view -->
    <div class="flex items-center justify-center gap-6">
      <button
        type="button"
        @mousedown.prevent="onHoldStart(-1)"
        @mouseup="onHoldEnd"
        @mouseleave="onHoldEnd"
        @touchstart.prevent="onHoldStart(-1)"
        @touchend="onHoldEnd"
        @touchcancel="onHoldEnd"
        :disabled="!canDecrease"
        class="select-none flex size-11 items-center justify-center rounded-lg bg-primary text-white text-xl font-bold disabled:opacity-30 disabled:cursor-not-allowed active:bg-primary/80"
      >−</button>
      <button
        type="button"
        @click="openSlider"
        class="w-24 rounded-lg border-2 border-primary/30 px-3 py-1.5 text-center text-lg font-bold text-primary hover:border-primary hover:bg-primary/5 transition"
      >
        {{ displayValue }}<span v-if="unit" class="ml-0.5 text-xs font-normal">{{ unit }}</span>
      </button>
      <button
        type="button"
        @mousedown.prevent="onHoldStart(+1)"
        @mouseup="onHoldEnd"
        @mouseleave="onHoldEnd"
        @touchstart.prevent="onHoldStart(+1)"
        @touchend="onHoldEnd"
        @touchcancel="onHoldEnd"
        :disabled="!canIncrease"
        class="select-none flex size-11 items-center justify-center rounded-lg bg-primary text-white text-xl font-bold disabled:opacity-30 disabled:cursor-not-allowed active:bg-primary/80"
      >+</button>
    </div>

    <!-- Overlay slider positioned above the value -->
      <Transition name="slider-popover">
        <div v-if="showSlider" ref="overlayRef" class="slider-popover">
        <div class="slider-value">{{ displayValue }}<span v-if="unit" class="unit">{{ unit }}</span></div>
        <input
          type="range"
          :min="0"
          :max="rangeSteps"
          :step="1"
          :value="sliderRangeValue"
          @input="onSliderInput"
          @mousedown="onDragStart"
          @touchstart="onDragStart"
          @mouseup="onDragEnd"
          @touchend="onDragEnd"
          @mouseleave="onDragEnd"
          class="slider-range"
        />
        <div class="slider-labels">
          <span>{{ min }}</span>
          <span>{{ max }}</span>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.slider-popover {
  position: absolute;
  bottom: calc(100% + 0.5rem);
  left: 0;
  right: 0;
  z-index: 50;
  background: white;
  border-radius: 0.75rem;
  padding: 1rem 1.25rem;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
  pointer-events: auto;
}

.slider-value {
  text-align: center;
  font-size: 1.75rem;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 0.5rem;
  user-select: none;
}

.slider-value .unit {
  font-size: 1rem;
  font-weight: 400;
  color: #94a3b8;
  margin-left: 0.125rem;
}

.slider-range {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 10px;
  border-radius: 5px;
  background: #e2e8f0;
  outline: none;
  cursor: pointer;
}

.slider-range::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #0ea5e9;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.4);
  border: 3px solid white;
}

.slider-range::-moz-range-thumb {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #0ea5e9;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.4);
  border: 3px solid white;
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 0.5rem;
  font-size: 0.75rem;
  color: #94a3b8;
  user-select: none;
}

/* Transitions */
.slider-popover-enter-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.slider-popover-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.slider-popover-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.slider-popover-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
