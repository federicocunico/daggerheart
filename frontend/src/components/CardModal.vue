<script setup lang="ts">
import { computed, ref } from 'vue'
import type { CardIndex } from '@/types/card'
import { DOMAIN_META } from '@/types/card'

const props = defineProps<{
  card: CardIndex | null
  navCards?: CardIndex[]   // list for prev/next navigation (scoped to current section)
  baseUrl?: string
  selected?: boolean
}>()

const emit = defineEmits<{
  close: []
  toggle: [card: CardIndex]
  navigate: [card: CardIndex]
}>()

const imgSrc = computed(() =>
  props.card ? `${props.baseUrl ?? ''}cards/${props.card.img}` : ''
)

const domainMeta = computed(() =>
  props.card?.dominio ? DOMAIN_META[props.card.dominio] : null
)

// ── Navigation ────────────────────────────────────────────────────────────────
const navIndex = computed(() =>
  props.navCards?.findIndex(c => c.id === props.card?.id) ?? -1
)
const hasPrev = computed(() => navIndex.value > 0)
const hasNext = computed(() => navIndex.value !== -1 && navIndex.value < (props.navCards?.length ?? 0) - 1)

function goTo(delta: number) {
  if (!props.navCards || navIndex.value < 0) return
  const idx = navIndex.value + delta
  if (idx >= 0 && idx < props.navCards.length) {
    const target = props.navCards[idx]
    if (target) emit('navigate', target)
  }
}

// ── Touch swipe ───────────────────────────────────────────────────────────────
const touchStartX = ref(0)
const touchStartY = ref(0)

function onTouchStart(e: TouchEvent) {
  touchStartX.value = e.touches[0]?.clientX ?? 0
  touchStartY.value = e.touches[0]?.clientY ?? 0
}

function onTouchEnd(e: TouchEvent) {
  const dx = (e.changedTouches[0]?.clientX ?? 0) - touchStartX.value
  const dy = (e.changedTouches[0]?.clientY ?? 0) - touchStartY.value
  // Only treat as horizontal swipe if horizontal motion is dominant
  if (Math.abs(dx) > Math.abs(dy) && Math.abs(dx) > 45) {
    goTo(dx > 0 ? -1 : 1)  // swipe right = prev, swipe left = next
  }
}

// ── Keyboard ──────────────────────────────────────────────────────────────────
function onKeyDown(e: KeyboardEvent) {
  if (!props.card) return
  if (e.key === 'ArrowLeft')  goTo(-1)
  if (e.key === 'ArrowRight') goTo(1)
  if (e.key === 'Escape')     emit('close')
}

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
        class="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-3 sm:p-6"
        @click="onBackdrop"
        @keydown="onKeyDown"
        @touchstart.passive="onTouchStart"
        @touchend.passive="onTouchEnd"
        tabindex="0"
      >
        <!-- Prev button (outside card, left side) -->
        <button
          v-if="navCards?.length"
          class="absolute left-2 sm:left-4 top-1/2 -translate-y-1/2 z-10
                 w-10 h-10 rounded-full flex items-center justify-center
                 bg-[var(--bg-panel)]/80 border border-[var(--border)]
                 text-[var(--gold)] text-lg transition-all
                 disabled:opacity-25 disabled:cursor-not-allowed hover:enabled:bg-[var(--bg-panel)]"
          :disabled="!hasPrev"
          @click.stop="goTo(-1)"
          aria-label="Carta precedente"
        >‹</button>

        <!-- Card container -->
        <div
          class="panel-gold max-w-sm w-full overflow-hidden shadow-2xl"
          @click.stop
        >
          <!-- Domain header -->
          <div
            v-if="domainMeta"
            :class="['px-4 py-2 flex items-center justify-between', domainMeta.color]"
          >
            <span class="text-white text-sm flex items-center gap-1.5" style="font-family:'Cinzel',serif; font-weight:600">
              {{ domainMeta.icon }} {{ domainMeta.label }}
            </span>
            <!-- Nav counter -->
            <span v-if="navCards?.length && navIndex >= 0" class="text-white/60 text-xs mr-auto ml-3">
              {{ navIndex + 1 }}/{{ navCards.length }}
            </span>
            <button @click="emit('close')" class="text-white/70 hover:text-white text-xl leading-none ml-2">×</button>
          </div>
          <div v-else class="px-4 py-2 flex items-center justify-between bg-[var(--bg-panel)] border-b border-[var(--border)]">
            <span v-if="navCards?.length && navIndex >= 0" class="text-[var(--text-dim)] text-xs">
              {{ navIndex + 1 }}/{{ navCards.length }}
            </span>
            <span v-else />
            <button @click="emit('close')" class="text-[var(--text-dim)] hover:text-[var(--text)] text-xl leading-none">×</button>
          </div>

          <!-- Card image -->
          <img :src="imgSrc" :alt="card.nome" class="w-full h-auto" />

          <!-- Card info -->
          <div class="p-4 space-y-2 bg-[var(--bg-card)]">
            <div class="flex items-start justify-between gap-2">
              <div>
                <p class="font-bold text-[var(--text)]" style="font-family:'Cinzel',serif">{{ card.nome }}</p>
                <p class="text-[var(--text-dim)] text-sm">
                  {{ card.tipo_carta }}
                  <span v-if="card.livello != null"> · Livello {{ card.livello }}</span>
                  <span v-if="card.soglia != null"> · Soglia {{ card.soglia }}</span>
                </p>
              </div>
            </div>

            <!-- Toggle button (only for ability cards) -->
            <button
              v-if="card.sottocategoria === 'abilita'"
              @click="emit('toggle', card)"
              :class="[
                'w-full py-2 rounded-lg text-sm transition-all duration-150',
                selected
                  ? 'bg-[var(--gold)] text-[#1a1000] font-bold'
                  : 'bg-[var(--bg-panel)] text-[var(--text)] border border-[var(--border)] hover:border-[var(--gold)]',
              ]"
              style="font-family:'Cinzel',serif; letter-spacing:0.08em; text-transform:uppercase; font-size:0.75rem"
            >
              {{ selected ? '✓ Selezionata' : '+ Aggiungi al mazzo' }}
            </button>
          </div>
        </div>

        <!-- Next button (outside card, right side) -->
        <button
          v-if="navCards?.length"
          class="absolute right-2 sm:right-4 top-1/2 -translate-y-1/2 z-10
                 w-10 h-10 rounded-full flex items-center justify-center
                 bg-[var(--bg-panel)]/80 border border-[var(--border)]
                 text-[var(--gold)] text-lg transition-all
                 disabled:opacity-25 disabled:cursor-not-allowed hover:enabled:bg-[var(--bg-panel)]"
          :disabled="!hasNext"
          @click.stop="goTo(1)"
          aria-label="Carta successiva"
        >›</button>
      </div>
    </Transition>
  </Teleport>
</template>
