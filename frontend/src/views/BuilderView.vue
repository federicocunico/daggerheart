<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useCharacterStore } from '@/stores/character'
import { DOMAIN_META } from '@/types/card'
import type { Dominio, CardIndex } from '@/types/card'
import CardThumbnail from '@/components/CardThumbnail.vue'
import CardModal from '@/components/CardModal.vue'
import { useDownload } from '@/composables/useDownload'
import { usePrint } from '@/composables/usePrint'

const store = useCharacterStore()
const { downloadSet, downloadSave, loadSave } = useDownload()
const { printCards } = usePrint()

// ── Class dropdown ────────────────────────────────────────────────────────────
const allDomains = Object.keys(DOMAIN_META) as Dominio[]

const classesByDomain = computed(() =>
  allDomains
    .map(d => ({
      dominio: d,
      nomi: store.classes
        .filter(c => c.dominio === d)
        .map(c => c.nome)
        .sort(),
    }))
    .filter(g => g.nomi.length)
)

function onClassChange(e: Event) {
  const val = (e.target as HTMLSelectElement).value
  if (val) {
    store.selectClass(val)
    filterLevel.value = 'all'
  }
}

// ── Domain selection ──────────────────────────────────────────────────────────
const MAX_DOMAINS = 2

function toggleDomain(d: Dominio) {
  if (store.selectedDomains.includes(d)) {
    store.toggleDomain(d)
  } else if (store.selectedDomains.length < MAX_DOMAINS) {
    store.toggleDomain(d)
  }
}

// ── Card modal with navigation context ───────────────────────────────────────
const previewCard    = ref<CardIndex | null>(null)
const previewContext = ref<CardIndex[]>([])

function openCard(card: CardIndex, context: CardIndex[]) {
  previewCard.value    = card
  previewContext.value = context
}

// ── Level filter ──────────────────────────────────────────────────────────────
const filterLevel = ref<number | 'all'>('all')

watch(() => store.className, () => { filterLevel.value = 'all' })

const filteredAbilities = computed(() => {
  const cards = store.abilityCards
  if (filterLevel.value === 'all') return cards
  return cards.filter(c => c.livello === filterLevel.value)
})

const groupedByDomain = computed(() => {
  const map: Record<string, CardIndex[]> = {}
  for (const c of filteredAbilities.value) {
    const d = c.dominio ?? 'altro'
    if (!map[d]) map[d] = []
    map[d].push(c)
  }
  return map
})

// ── Selection helpers ─────────────────────────────────────────────────────────
const originCard = computed(() =>
  store.selectedOrigin
    ? store.allCards.find(c => c.id === store.selectedOrigin) ?? null
    : null
)

const communityCard = computed(() =>
  store.selectedCommunity
    ? store.allCards.find(c => c.id === store.selectedCommunity) ?? null
    : null
)

const selectedAbilityCards = computed(() =>
  store.allCards.filter(c => store.selectedAbilities.has(c.id))
)

const hasAnyCard = computed(() =>
  !!(originCard.value || communityCard.value ||
     store.classCards.length || selectedAbilityCards.value.length)
)

// ── Download / Print ──────────────────────────────────────────────────────────
const downloading = ref(false)
const fileInput   = ref<HTMLInputElement | null>(null)

async function onDownloadZip() {
  downloading.value = true
  try {
    await downloadSet(
      store.toSave(),
      originCard.value,
      communityCard.value,
      store.classCards,
      selectedAbilityCards.value,
    )
  } finally {
    downloading.value = false
  }
}

function onDownloadJson() { downloadSave(store.toSave()) }

async function onLoadFile(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  try {
    store.fromSave(await loadSave(file))
  } catch (err) {
    alert(String(err))
  }
  ;(e.target as HTMLInputElement).value = ''
}

function onPrint() {
  printCards(originCard.value, communityCard.value, store.classCards, selectedAbilityCards.value)
}

function domainDividerStyle(d: Dominio) {
  return `background: linear-gradient(90deg, transparent, ${DOMAIN_META[d].hex}80, transparent)`
}
</script>

<template>
  <div class="max-w-5xl mx-auto px-4 sm:px-6 py-8 pb-32 space-y-12">

    <!-- Hero text before any selection -->
    <div v-if="!store.className" class="text-center py-2">
      <p class="text-[var(--text-dim)] text-lg italic max-w-lg mx-auto leading-relaxed">
        Forgia il tuo destino. Scegli una classe per costruire il mazzo del tuo personaggio.
      </p>
    </div>

    <!-- ══════════════════════════════════════════════════════════════════════
         I · ORIGINE
         ══════════════════════════════════════════════════════════════════════ -->
    <section class="space-y-4">
      <div class="ornament">I · Origine</div>
      <p class="text-[var(--text-dim)] text-sm">
        Scegli la tua carta Origine (facoltativa).
        <span v-if="store.selectedOrigin" class="text-[var(--gold)] ml-1">✓ Selezionata</span>
      </p>
      <div class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-2">
        <CardThumbnail
          v-for="card in store.originCards"
          :key="card.id"
          :card="card"
          :selected="store.selectedOrigin === card.id"
          :selectable="true"
          @click="store.selectOrigin(store.selectedOrigin === card.id ? null : card.id)"
          @preview="openCard($event, store.originCards)"
        />
      </div>
    </section>

    <!-- ══════════════════════════════════════════════════════════════════════
         II · CLASSE
         ══════════════════════════════════════════════════════════════════════ -->
    <section class="space-y-4">
      <div class="ornament">II · Classe</div>

      <div class="panel-gold p-5 sm:p-6 space-y-5">
        <div class="space-y-2">
          <label
            class="block text-[var(--text-dim)] text-xs uppercase tracking-[0.15em]"
            style="font-family: 'Cinzel', serif"
          >
            Scegli la tua classe
          </label>
          <select
            class="select-gold w-full sm:max-w-md"
            :value="store.className ?? ''"
            @change="onClassChange"
          >
            <option value="" disabled>— Seleziona —</option>
            <optgroup
              v-for="{ dominio, nomi } in classesByDomain"
              :key="dominio"
              :label="`${DOMAIN_META[dominio].icon}  ${DOMAIN_META[dominio].label}`"
            >
              <option v-for="nome in nomi" :key="nome" :value="nome">{{ nome }}</option>
            </optgroup>
          </select>
        </div>

        <!-- Class feature cards (6 cards, 2 subclasses × 3) -->
        <template v-if="store.classCards.length">
          <div class="h-px bg-[var(--border)]" />
          <p
            class="text-[var(--text-dim)] text-xs uppercase tracking-[0.15em]"
            style="font-family: 'Cinzel', serif"
          >
            Carte di classe
          </p>
          <div class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-2">
            <CardThumbnail
              v-for="card in store.classCards"
              :key="card.id"
              :card="card"
              :selectable="false"
              @click="openCard(card, store.classCards)"
              @preview="openCard(card, store.classCards)"
            />
          </div>
        </template>
      </div>
    </section>

    <!-- ══════════════════════════════════════════════════════════════════════
         III · DOMINI
         ══════════════════════════════════════════════════════════════════════ -->
    <section v-if="store.className" class="space-y-4">
      <div class="ornament">III · Domini</div>

      <div class="panel p-5 space-y-4">
        <p class="text-[var(--text)] text-sm">
          Scegli <strong class="text-[var(--gold)]">2 domini</strong>
          per le tue carte abilità.
          <span class="text-[var(--text-dim)]">({{ store.selectedDomains.length }}/{{ MAX_DOMAINS }})</span>
        </p>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="d in allDomains"
            :key="d"
            class="domain-chip"
            :class="{ active: store.selectedDomains.includes(d) }"
            :style="store.selectedDomains.includes(d)
              ? `border-color: ${DOMAIN_META[d].hex}; color: ${DOMAIN_META[d].hex}; background: ${DOMAIN_META[d].hex}22`
              : ''"
            :disabled="!store.selectedDomains.includes(d) && store.selectedDomains.length >= MAX_DOMAINS"
            @click="toggleDomain(d)"
          >
            {{ DOMAIN_META[d].icon }} {{ DOMAIN_META[d].label }}
          </button>
        </div>
      </div>
    </section>

    <!-- ══════════════════════════════════════════════════════════════════════
         IV · ABILITÀ
         ══════════════════════════════════════════════════════════════════════ -->
    <section v-if="store.selectedDomains.length" class="space-y-4">
      <div class="ornament">IV · Abilità</div>

      <!-- Level filter pills -->
      <div class="flex flex-wrap gap-2 items-center">
        <button
          class="domain-chip"
          :class="{ active: filterLevel === 'all' }"
          @click="filterLevel = 'all'"
        >Tutte</button>
        <button
          v-for="lvl in store.levels"
          :key="lvl"
          class="domain-chip"
          :class="{ active: filterLevel === lvl }"
          @click="filterLevel = lvl"
        >Liv. {{ lvl }}</button>
        <span class="text-[var(--text-dim)] text-xs ml-auto">
          {{ store.selectedAbilities.size }} selezionate
        </span>
      </div>

      <div
        v-for="d in store.selectedDomains"
        :key="d"
        class="space-y-3"
      >
        <!-- Colored domain divider -->
        <div class="flex items-center gap-3" :style="`color: ${DOMAIN_META[d].hex}`">
          <div class="h-px flex-1" :style="domainDividerStyle(d)" />
          <span
            class="text-xs uppercase tracking-[0.2em] flex-shrink-0"
            style="font-family: 'Cinzel', serif"
          >
            {{ DOMAIN_META[d].icon }} {{ DOMAIN_META[d].label }}
          </span>
          <div class="h-px flex-1" :style="domainDividerStyle(d)" />
        </div>

        <div
          v-if="groupedByDomain[d]?.length"
          class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-2"
        >
          <CardThumbnail
            v-for="card in groupedByDomain[d]"
            :key="card.id"
            :card="card"
            :selected="store.isSelected(card.id)"
            :selectable="true"
            @click="store.toggleAbility(card.id)"
            @preview="openCard(card, groupedByDomain[d])"
          />
        </div>
        <p v-else class="text-[var(--text-dim)] text-sm italic pl-1">
          Nessuna carta con i filtri attivi.
        </p>
      </div>
    </section>

    <!-- ══════════════════════════════════════════════════════════════════════
         V · COMUNITÀ
         ══════════════════════════════════════════════════════════════════════ -->
    <section v-if="store.className" class="space-y-4">
      <div class="ornament">V · Comunità</div>
      <p class="text-[var(--text-dim)] text-sm">
        Scegli la tua carta Comunità (facoltativa).
        <span v-if="store.selectedCommunity" class="text-[var(--gold)] ml-1">✓ Selezionata</span>
      </p>
      <div class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-2">
        <CardThumbnail
          v-for="card in store.communityCards"
          :key="card.id"
          :card="card"
          :selected="store.selectedCommunity === card.id"
          :selectable="true"
          @click="store.selectCommunity(store.selectedCommunity === card.id ? null : card.id)"
          @preview="openCard(card, store.communityCards)"
        />
      </div>
    </section>

    <div class="h-2" />

    <!-- ══════════════════════════════════════════════════════════════════════
         STICKY BOTTOM BAR
         ══════════════════════════════════════════════════════════════════════ -->
    <Teleport to="body">
      <div
        v-if="store.className || store.selectedOrigin"
        class="fixed bottom-0 left-0 right-0 z-30 border-t border-[var(--border)] bg-[var(--bg-panel)]/97 backdrop-blur-sm"
      >
        <div class="max-w-5xl mx-auto px-4 sm:px-6 py-3 flex flex-wrap items-center gap-3">
          <div class="text-xs text-[var(--text-dim)] flex-1 min-w-0 leading-relaxed">
            <span
              v-if="store.className"
              class="text-[var(--gold)] font-semibold"
              style="font-family: 'Cinzel', serif"
            >{{ store.className }}</span>
            <template v-if="store.selectedDomains.length">
              <span class="mx-1">·</span>
              <span
                v-for="(d, i) in store.selectedDomains"
                :key="d"
                :style="`color: ${DOMAIN_META[d].hex}`"
              >{{ i ? ' · ' : '' }}{{ DOMAIN_META[d].icon }} {{ DOMAIN_META[d].label }}</span>
            </template>
            <template v-if="store.selectedAbilities.size">
              <span class="mx-1">·</span>
              <span class="text-[var(--gold)]">{{ store.selectedAbilities.size }}</span> abilità
            </template>
            <span v-if="store.selectedOrigin"> · Origine ✓</span>
            <span v-if="store.selectedCommunity"> · Comunità ✓</span>
          </div>

          <div class="flex gap-2 flex-shrink-0 flex-wrap">
            <button
              class="btn-secondary"
              style="font-size:0.75rem; padding:0.4rem 1rem"
              @click="fileInput?.click()"
            >Carica</button>
            <button
              class="btn-secondary"
              style="font-size:0.75rem; padding:0.4rem 1rem"
              @click="onDownloadJson"
              :disabled="!store.className"
            >Salva</button>
            <button
              class="btn-primary"
              style="font-size:0.75rem; padding:0.4rem 1rem"
              @click="onPrint"
              :disabled="!hasAnyCard"
            >Stampa</button>
            <button
              class="btn-primary"
              style="font-size:0.75rem; padding:0.4rem 1rem"
              @click="onDownloadZip"
              :disabled="downloading || !hasAnyCard"
            >{{ downloading ? '…' : 'Scarica' }}</button>
          </div>
        </div>

        <input
          ref="fileInput"
          type="file"
          accept=".json"
          class="hidden"
          @change="onLoadFile"
        />
      </div>
    </Teleport>

    <!-- ── Card Preview Modal with navigation ────────────────────────────── -->
    <CardModal
      :card="previewCard"
      :navCards="previewContext"
      :selected="previewCard ? store.isSelected(previewCard.id) : false"
      @close="previewCard = null"
      @toggle="card => store.toggleAbility(card.id)"
      @navigate="card => { previewCard = card }"
    />
  </div>
</template>
