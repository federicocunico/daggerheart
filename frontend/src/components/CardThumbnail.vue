<script setup lang="ts">
import { computed } from 'vue'
import type { CardIndex } from '@/types/card'
import { DOMAIN_META } from '@/types/card'

const props = defineProps<{
  card: CardIndex
  selected?: boolean
  selectable?: boolean
  baseUrl?: string
}>()

const emit = defineEmits<{
  click: [card: CardIndex]
  preview: [card: CardIndex]
}>()

const imgSrc = computed(() =>
  `${props.baseUrl ?? ''}cards/${props.card.img}`
)

const domainMeta = computed(() =>
  props.card.dominio ? DOMAIN_META[props.card.dominio] : null
)

const levelLabel = computed(() => {
  if (props.card.livello == null) return null
  const labels: Record<number, string> = { 0: 'Liv 0', 1: 'Liv 1', 2: 'Liv 2', 3: 'Liv 3' }
  return labels[props.card.livello] ?? `Liv ${props.card.livello}`
})
</script>

<template>
  <div
    :class="[
      'relative rounded-xl overflow-hidden border-2 transition-all duration-200 cursor-pointer group',
      selected
        ? 'border-yellow-400 shadow-lg shadow-yellow-400/20 scale-[1.02]'
        : 'border-stone-700 hover:border-stone-400 hover:scale-[1.02] hover:shadow-lg hover:shadow-black/50',
    ]"
    @click="emit('click', card)"
  >
    <!-- Card image -->
    <img
      :src="imgSrc"
      :alt="card.nome"
      class="w-full h-auto block bg-stone-800"
      loading="lazy"
    />

    <!-- Selection indicator -->
    <div
      v-if="selectable"
      :class="[
        'absolute top-2 right-2 w-6 h-6 rounded-full border-2 flex items-center justify-center text-xs font-bold transition-all',
        selected
          ? 'bg-yellow-400 border-yellow-400 text-stone-900'
          : 'bg-stone-900/70 border-stone-500 text-transparent',
      ]"
    >
      ✓
    </div>

    <!-- Level badge -->
    <div
      v-if="levelLabel"
      class="absolute top-2 left-2 bg-stone-900/80 text-yellow-400 text-xs font-bold px-1.5 py-0.5 rounded"
    >
      {{ levelLabel }}
    </div>

    <!-- Hover overlay with card name -->
    <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent
                opacity-0 group-hover:opacity-100 transition-opacity duration-200
                flex flex-col justify-end p-2">
      <p class="text-white text-xs font-bold leading-tight line-clamp-2">{{ card.nome }}</p>
      <div class="flex items-center gap-1 mt-0.5">
        <span v-if="domainMeta" class="text-xs">{{ domainMeta.icon }}</span>
        <span class="text-stone-300 text-xs">{{ card.tipo_carta }}</span>
      </div>
    </div>

    <!-- Preview button -->
    <button
      class="absolute bottom-2 right-2 w-6 h-6 bg-stone-900/80 hover:bg-stone-700 rounded-full
             flex items-center justify-center text-xs opacity-0 group-hover:opacity-100
             transition-opacity duration-200 z-10"
      @click.stop="emit('preview', card)"
      title="Anteprima"
    >
      🔍
    </button>
  </div>
</template>
