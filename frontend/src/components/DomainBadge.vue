<script setup lang="ts">
import type { Dominio } from '@/types/card'
import { DOMAIN_META } from '@/types/card'

const props = defineProps<{
  dominio: Dominio
  active?: boolean
  size?: 'sm' | 'md' | 'lg'
}>()

const meta = DOMAIN_META[props.dominio]
const sizeClass = {
  sm:  'text-xs px-2 py-0.5 gap-1',
  md:  'text-sm px-3 py-1 gap-1.5',
  lg:  'text-base px-4 py-1.5 gap-2',
}[props.size ?? 'md']
</script>

<template>
  <span
    :class="[
      'inline-flex items-center font-bold rounded-full border transition-all duration-150',
      sizeClass,
      active
        ? `${meta.color} border-transparent text-white shadow-lg`
        : 'bg-transparent border-stone-600 text-stone-400 hover:border-stone-400 hover:text-stone-200',
    ]"
  >
    <span>{{ meta.icon }}</span>
    <span>{{ meta.label }}</span>
  </span>
</template>
