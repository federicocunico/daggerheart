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

// ── Subclass hierarchy ────────────────────────────────────────────────────────
// Card-type display order within each subclass: base → specialisation → mastery
const TIPO_TIER: Record<string, number> = {
  tratto: 0, privilegio: 0, caratteristica: 0,
  specializzazione: 1, azione: 1, incantesimo: 1,
  maestria: 2,
}

const TIPO_LABEL: Record<string, string> = {
  tratto: 'Tratto', privilegio: 'Privilegio', caratteristica: 'Caratteristica',
  specializzazione: 'Specializzazione', azione: 'Azione', incantesimo: 'Incantesimo',
  maestria: 'Maestria',
}

const subclassData = computed(() => {
  if (!store.activeClass) return []
  return store.subclasses.map(subName => ({
    name: subName,
    cards: store.activeClass!.cards
      .filter(c => c.nome === subName)
      .sort((a, b) => (TIPO_TIER[a.tipo_carta ?? ''] ?? 99) - (TIPO_TIER[b.tipo_carta ?? ''] ?? 99)),
    selected: store.selectedSubclass === subName,
  }))
})

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

function domainHex(d: Dominio) {
  return DOMAIN_META[d].hex
}
</script>

<template>
  <div class="max-w-5xl mx-auto px-4 sm:px-6 py-8 pb-32 space-y-12">

    <!-- Hero text before any selection -->
    <div v-if="!store.className && !store.selectedOrigin && !store.selectedCommunity" class="text-center py-2">
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
         II · COMUNITÀ
         ══════════════════════════════════════════════════════════════════════ -->
    <section class="space-y-4">
      <div class="ornament">II · Comunità</div>
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

    <!-- ══════════════════════════════════════════════════════════════════════
         III · CLASSE
         ══════════════════════════════════════════════════════════════════════ -->
    <section class="space-y-4">
      <div class="ornament">III · Classe</div>

      <div class="panel-gold p-5 sm:p-6 space-y-6">

        <!-- Class selector dropdown -->
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

        <!-- Subclass selection + card hierarchy -->
        <template v-if="store.activeClass">
          <div class="h-px bg-[var(--border)]" />

          <div>
            <p
              class="text-[var(--text-dim)] text-xs uppercase tracking-[0.15em] mb-3"
              style="font-family: 'Cinzel', serif"
            >
              Scegli la tua sottoclasse
            </p>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div
                v-for="sub in subclassData"
                :key="sub.name"
                class="rounded-lg border-2 cursor-pointer transition-all duration-200 overflow-hidden"
                :class="sub.selected
                  ? 'border-[var(--gold)] bg-[var(--gold-glow)]'
                  : 'border-[var(--border)] hover:border-[var(--gold-dim)] bg-[var(--bg-card)]'"
                @click="store.selectSubclass(sub.selected ? null : sub.name)"
              >
                <!-- Subclass header -->
                <div
                  class="px-3 py-2 flex items-center justify-between border-b border-[var(--border)]"
                  :style="`background: ${domainHex(store.activeClass!.dominio)}18`"
                >
                  <span
                    class="text-xs font-bold tracking-wider truncate"
                    :style="`font-family:'Cinzel',serif; color: ${domainHex(store.activeClass!.dominio)}`"
                  >{{ sub.name }}</span>
                  <span
                    v-if="sub.selected"
                    class="text-[var(--gold)] text-xs ml-2 flex-shrink-0"
                  >✓</span>
                </div>

                <!-- Cards in tier order -->
                <div class="p-3 space-y-2">
                  <div
                    v-for="card in sub.cards"
                    :key="card.id"
                    class="flex items-center gap-2"
                    @click.stop="openCard(card, sub.cards)"
                  >
                    <CardThumbnail
                      :card="card"
                      :selectable="false"
                      class="w-12 flex-shrink-0 pointer-events-none"
                    />
                    <div class="min-w-0">
                      <p
                        class="text-[10px] uppercase tracking-wider font-semibold"
                        :style="`color: ${domainHex(store.activeClass!.dominio)}; font-family:'Cinzel',serif`"
                      >{{ TIPO_LABEL[card.tipo_carta ?? ''] ?? card.tipo_carta }}</p>
                    </div>
                  </div>
                </div>

                <!-- Select button -->
                <div class="px-3 pb-3">
                  <div
                    class="w-full text-center text-xs py-1.5 rounded border transition-all"
                    :class="sub.selected
                      ? 'border-[var(--gold)] text-[var(--gold)] bg-[var(--gold-glow)]'
                      : 'border-[var(--border)] text-[var(--text-dim)]'"
                    style="font-family:'Cinzel',serif; letter-spacing:0.08em; text-transform:uppercase"
                  >
                    {{ sub.selected ? '✓ Selezionata' : 'Scegli' }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>
    </section>

    <!-- ══════════════════════════════════════════════════════════════════════
         IV · DOMINI  (auto-selected from class, shown as info)
         ══════════════════════════════════════════════════════════════════════ -->
    <section v-if="store.className" class="space-y-4">
      <div class="ornament">IV · Domini</div>

      <div class="panel p-5 space-y-4">
        <p class="text-[var(--text)] text-sm">
          La classe <strong class="text-[var(--gold)]">{{ store.className }}</strong>
          ha accesso a questi due domini:
        </p>
        <div class="flex flex-wrap gap-3">
          <div
            v-for="d in store.classDomains"
            :key="d"
            class="flex items-center gap-2 px-4 py-2 rounded-lg border-2 text-sm font-bold"
            :style="`border-color: ${DOMAIN_META[d].hex}; color: ${DOMAIN_META[d].hex}; background: ${DOMAIN_META[d].hex}18; font-family:'Cinzel',serif`"
          >
            {{ DOMAIN_META[d].icon }} {{ DOMAIN_META[d].label }}
          </div>
        </div>
        <p class="text-[var(--text-dim)] text-xs italic">
          Le carte abilità disponibili qui sotto provengono da questi due domini.
        </p>
      </div>
    </section>

    <!-- ══════════════════════════════════════════════════════════════════════
         V · ABILITÀ
         ══════════════════════════════════════════════════════════════════════ -->
    <section v-if="store.selectedDomains.length" class="space-y-4">
      <div class="ornament">V · Abilità</div>

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
         VI · NOME PERSONAGGIO
         ══════════════════════════════════════════════════════════════════════ -->
    <section class="space-y-4">
      <div class="ornament">Nome del personaggio</div>
      <div class="panel p-4 space-y-2">
        <input
          type="text"
          :value="store.characterName"
          @input="store.setCharacterName(($event.target as HTMLInputElement).value)"
          placeholder="Inserisci il nome del personaggio…"
          class="w-full bg-transparent border border-[var(--border)] rounded-lg px-3 py-2.5
                 text-[var(--text)] placeholder-[var(--text-dim)]
                 focus:border-[var(--gold)] focus:outline-none transition-colors"
          style="font-family:'Cinzel',serif"
        />
        <p class="text-[var(--text-dim)] text-xs">
          Usato come nome del file al salvataggio e download.
        </p>
      </div>
    </section>

    <div class="h-2" />

    <!-- ══════════════════════════════════════════════════════════════════════
         STICKY BOTTOM BAR  (always visible — Carica è sempre accessibile)
         ══════════════════════════════════════════════════════════════════════ -->
    <Teleport to="body">
      <div
        class="fixed bottom-0 left-0 right-0 z-30 border-t border-[var(--border)] bg-[var(--bg-panel)]/97 backdrop-blur-sm"
      >
        <div class="max-w-5xl mx-auto px-4 sm:px-6 py-3 flex flex-wrap items-center gap-3">
          <!-- Character summary (shown when there's something to summarise) -->
          <div class="text-xs text-[var(--text-dim)] flex-1 min-w-0 leading-relaxed">
            <template v-if="store.characterName">
              <span
                class="text-[var(--gold)] font-semibold"
                style="font-family:'Cinzel',serif"
              >{{ store.characterName }}</span>
              <span v-if="store.className" class="mx-1 opacity-50">·</span>
            </template>
            <span
              v-if="store.className"
              class="text-[var(--gold)] font-semibold"
              style="font-family: 'Cinzel', serif"
            >{{ store.className }}</span>
            <template v-if="store.selectedSubclass">
              <span class="mx-1 opacity-50">·</span>
              <span class="text-[var(--text-dim)]">{{ store.selectedSubclass }}</span>
            </template>
            <template v-if="store.selectedDomains.length">
              <span class="mx-1">·</span>
              <span
                v-for="(d, i) in store.selectedDomains"
                :key="d"
                :style="`color: ${DOMAIN_META[d].hex}`"
              >{{ i ? ' · ' : '' }}{{ DOMAIN_META[d].icon }}</span>
            </template>
            <template v-if="store.selectedAbilities.size">
              <span class="mx-1">·</span>
              <span class="text-[var(--gold)]">{{ store.selectedAbilities.size }}</span>
              <span class="hidden sm:inline"> abilità</span>
            </template>
            <span v-if="!store.className && !store.selectedOrigin && !store.characterName"
                  class="italic opacity-60">Nessun personaggio — carica un file o inizia a costruire</span>
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
