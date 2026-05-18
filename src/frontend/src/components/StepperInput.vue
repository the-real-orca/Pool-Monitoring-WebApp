<script setup>
import { computed } from 'vue'

const props = defineProps(['modelValue', 'min', 'max', 'step', 'decimals', 'unit'])
const emit = defineEmits(['update:modelValue'])

const inputValue = computed({
  get: () => props.modelValue.toFixed(props.decimals),
  set: (val) => {
    const cleaned = String(val).replace(',', '.')
    const num = parseFloat(cleaned)
    if (!isNaN(num)) {
      const clamped = Math.max(props.min, Math.min(props.max, num))
      emit('update:modelValue', parseFloat(clamped.toFixed(props.decimals)))
    }
  },
})

function step(dir) {
  const next = parseFloat((props.modelValue + dir * props.step).toFixed(props.decimals))
  if (next >= props.min && next <= props.max) emit('update:modelValue', next)
}
</script>

<template>
  <div class="flex items-center gap-2">
    <button
      type="button"
      @click="step(-1)"
      :disabled="modelValue <= min"
      class="flex size-11 shrink-0 mr-6 items-center justify-center rounded-lg bg-primary text-white text-xl font-bold disabled:opacity-30 disabled:cursor-not-allowed active:bg-primary/80"
    >−</button>
    <input
      v-model="inputValue"
      type="text"
      inputmode="decimal"
      class="w-20 rounded-lg border border-slate-300 px-2 py-1 text-center text-lg font-semibold tabular-nums focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
    />
    <span class="text-sm text-slate-500 w-8">{{ unit }}</span>
    <button
      type="button"
      @click="step(+1)"
      :disabled="modelValue >= max"
      class="flex size-11 shrink-0 items-center justify-center rounded-lg bg-primary text-white text-xl font-bold disabled:opacity-30 disabled:cursor-not-allowed active:bg-primary/80"
    >+</button>
  </div>
</template>
