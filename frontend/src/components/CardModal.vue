<script setup lang="ts">
import { computed } from 'vue'
import type { CardIndex } from '@/types/card'
import { DOMAIN_META } from '@/types/card'

const props = defineProps<{
  card: CardIndex | null
  baseUrl?: string
  selected?: boolean
}>()

const emit = defineEmits<{
  close: []
  toggle: [card: CardIndex]
}>()

const imgSrc = computed(() =>
  props.card ? `${props.baseUrl ?? ''}cards/${props.card.img}` : ''
)

const domainMeta = computed(() =>
  props.card?.dominio ? DOMAIN_META[props.card.dominio] : null
)

function onBackdrop(e: MouseEvent) {
  if (e.target === e.currentTarget) emit('close')
}
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition-opacity duration-200"
      enter-from-class="opacity-0"
      leave-active-class="transition-opacity duration-200"
      leave-to-class="opacity-0"
    >
      <div
        v-if="card"
        class="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4"
        @click="onBackdrop"
      >
        <div class="glass rounded-2xl max-w-sm w-full overflow-hidden shadow-2xl">
          <!-- Domain header -->
          <div
            v-if="domainMeta"
            :class="['px-4 py-2 flex items-center justify-between', domainMeta.color]"
          >
            <span class="text-white font-bold text-sm flex items-center gap-1.5">
              {{ domainMeta.icon }} {{ domainMeta.label }}
            </span>
            <button @click="emit('close')" class="text-white/70 hover:text-white text-lg leading-none">×</button>
          </div>
          <div v-else class="px-4 py-2 flex justify-end bg-stone-800">
            <button @click="emit('close')" class="text-stone-400 hover:text-white text-lg leading-none">×</button>
          </div>

          <!-- Card image -->
          <img :src="imgSrc" :alt="card.nome" class="w-full h-auto" />

          <!-- Card info -->
          <div class="p-4 space-y-2">
            <div class="flex items-start justify-between gap-2">
              <div>
                <p class="font-bold text-stone-100">{{ card.nome }}</p>
                <p class="text-stone-400 text-sm">
                  {{ card.tipo_carta }}
                  <span v-if="card.livello != null"> · Livello {{ card.livello }}</span>
                  <span v-if="card.soglia != null"> · Soglia {{ card.soglia }}</span>
                </p>
              </div>
              <span v-if="card.id" class="text-stone-600 text-xs shrink-0">{{ card.id }}</span>
            </div>

            <!-- Toggle button -->
            <button
              v-if="card.sottocategoria === 'abilita'"
              @click="emit('toggle', card)"
              :class="[
                'w-full py-2 rounded-lg font-bold text-sm transition-colors duration-150',
                selected
                  ? 'bg-yellow-400 text-stone-900 hover:bg-yellow-300'
                  : 'bg-stone-700 text-stone-200 hover:bg-stone-600',
              ]"
            >
              {{ selected ? '✓ Selezionata' : '+ Aggiungi al mazzo' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
