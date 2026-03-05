<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import { useCharacterStore } from '@/stores/character'
import { DOMAIN_META } from '@/types/card'
import type { Dominio, CardIndex } from '@/types/card'
import CardThumbnail from '@/components/CardThumbnail.vue'
import CardModal from '@/components/CardModal.vue'
import { useDownload } from '@/composables/useDownload'
import { usePrint } from '@/composables/usePrint'
import { useI18n } from '@/composables/useI18n'

const store = useCharacterStore()
const { t } = useI18n()
const { downloadSet, downloadSave, loadSave } = useDownload()
const { printCards } = usePrint()

// ── Card grid size ───────────────────────────────────────────────────────────
const GRID_LEVELS = [
  'grid-cols-1 sm:grid-cols-2 md:grid-cols-2 lg:grid-cols-3',                   // 0  largest
  'grid-cols-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4',                   // 1
  'grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5',                   // 2
  'grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6',    // 3
  'grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-7',    // 4  default
  'grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-7 xl:grid-cols-8',    // 5
  'grid-cols-4 sm:grid-cols-5 md:grid-cols-6 lg:grid-cols-8 xl:grid-cols-9',    // 6
  'grid-cols-4 sm:grid-cols-6 md:grid-cols-7 lg:grid-cols-9 xl:grid-cols-10',   // 7
  'grid-cols-5 sm:grid-cols-6 md:grid-cols-8 lg:grid-cols-10 xl:grid-cols-12',  // 8  smallest
]
const cardSizeLevel = ref(4) // index into GRID_LEVELS, 4 = default
const cardGridClass = computed(() => `grid ${GRID_LEVELS[cardSizeLevel.value]} gap-2`)

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

// ── Reusable confirmation dialog ─────────────────────────────────────────────
const confirmVisible = ref(false)
const confirmTitle   = ref('')
const confirmMessage = ref('')
const confirmYes     = ref('')
const confirmNo      = ref('')
let confirmResolve: ((ok: boolean) => void) | null = null

function showConfirm(opts: { title: string; message: string; yes?: string; no?: string }): Promise<boolean> {
  confirmTitle.value   = opts.title
  confirmMessage.value = opts.message
  confirmYes.value     = opts.yes ?? 'Conferma'
  confirmNo.value      = opts.no  ?? 'Annulla'
  confirmVisible.value = true
  return new Promise(resolve => { confirmResolve = resolve })
}

function onConfirmAnswer(ok: boolean) {
  confirmVisible.value = false
  confirmResolve?.(ok)
  confirmResolve = null
}

// ── Reset ────────────────────────────────────────────────────────────────────
async function onReset() {
  const ok = await showConfirm({
    title: t('confirm.reset.title'),
    message: t('confirm.reset.message'),
    yes: t('confirm.reset.yes'),
    no: t('confirm.reset.no'),
  })
  if (ok) {
    store.reset()
    filterLevel.value = 'all'
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

// ── Warn before leaving if dirty ─────────────────────────────────────────────
// Browser tab close / refresh — native prompt (browsers block custom UI here)
function onBeforeUnload(e: BeforeUnloadEvent) {
  if (store.isDirty) {
    e.preventDefault()
  }
}

// Push a sentry history entry so pressing Back triggers popstate inside the SPA
// instead of leaving the page entirely. The popstate handler shows our styled dialog.
let sentryPushed = false
function pushSentry() {
  if (!sentryPushed && store.isDirty) {
    history.pushState({ sentry: true }, '')
    sentryPushed = true
  }
}
function removeSentry() {
  if (sentryPushed) {
    sentryPushed = false
  }
}

async function onPopState() {
  if (!store.isDirty) {
    sentryPushed = false
    history.back()
    return
  }
  const ok = await showConfirm({
    title: 'Uscire dalla pagina?',
    message: 'Hai delle selezioni non salvate. Se esci perderai tutte le modifiche.',
    yes: 'Esci',
    no: 'Resta',
  })
  if (ok) {
    sentryPushed = false
    // Remove beforeunload so the native prompt doesn't also fire
    window.removeEventListener('beforeunload', onBeforeUnload)
    history.back()
  } else {
    // User chose to stay — re-push sentry so Back works again
    history.pushState({ sentry: true }, '')
  }
}

// Keep sentry in sync with dirty state
watch(() => store.isDirty, (dirty) => {
  if (dirty) pushSentry()
  else removeSentry()
})

onMounted(() => {
  window.addEventListener('beforeunload', onBeforeUnload)
  window.addEventListener('popstate', onPopState)
  if (store.isDirty) pushSentry()
})
onUnmounted(() => {
  window.removeEventListener('beforeunload', onBeforeUnload)
  window.removeEventListener('popstate', onPopState)
  removeSentry()
})

// Vue Router navigation (links to other pages within the SPA)
onBeforeRouteLeave(async () => {
  if (store.isDirty) {
    const ok = await showConfirm({
      title: t('confirm.leave.title'),
      message: t('confirm.leave.message'),
      yes: t('confirm.leave.yes'),
      no: t('confirm.leave.no'),
    })
    if (!ok) return false
  }
})
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 py-8 pb-32 space-y-12">

    <!-- Hero text before any selection -->
    <div v-if="!store.className && !store.selectedOrigin && !store.selectedCommunity" class="text-center py-2">
      <p class="text-[var(--text-dim)] text-lg italic max-w-lg mx-auto leading-relaxed">
        {{ t('builder.hero') }}
      </p>
    </div>

    <!-- ══════════════════════════════════════════════════════════════════════
         I · ORIGINE
         ══════════════════════════════════════════════════════════════════════ -->
    <section class="space-y-4">
      <div class="ornament">{{ t('section.origin') }}</div>
      <p class="text-[var(--text-dim)] text-sm">
        {{ t('section.origin.desc') }}
        <span v-if="store.selectedOrigin" class="text-[var(--gold)] ml-1">{{ t('section.origin.ok') }}</span>
      </p>
      <div :class="cardGridClass">
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
      <div class="ornament">{{ t('section.community') }}</div>
      <p class="text-[var(--text-dim)] text-sm">
        {{ t('section.community.desc') }}
        <span v-if="store.selectedCommunity" class="text-[var(--gold)] ml-1">{{ t('section.community.ok') }}</span>
      </p>
      <div :class="cardGridClass">
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
      <div class="ornament">{{ t('section.class') }}</div>

      <div class="panel-gold p-5 sm:p-6 space-y-6">

        <!-- Class selector dropdown -->
        <div class="space-y-2">
          <label
            class="block text-[var(--text-dim)] text-xs uppercase tracking-[0.15em]"
            style="font-family: 'Cinzel', serif"
          >
            {{ t('section.class.select') }}
          </label>
          <select
            class="select-gold w-full sm:max-w-md"
            :value="store.className ?? ''"
            @change="onClassChange"
          >
            <option value="" disabled>{{ t('section.class.placeholder') }}</option>
            <optgroup
              v-for="{ dominio, nomi } in classesByDomain"
              :key="dominio"
              :label="`${DOMAIN_META[dominio].icon}  ${DOMAIN_META[dominio].label}`"
            >
              <option v-for="nome in nomi" :key="nome" :value="nome">{{ nome }}</option>
            </optgroup>
          </select>
        </div>

        <!-- Subclass selection + individual card picks -->
        <template v-if="store.activeClass">
          <div class="h-px bg-[var(--border)]" />

          <div class="space-y-4">
            <p
              class="text-[var(--text-dim)] text-xs uppercase tracking-[0.15em]"
              style="font-family: 'Cinzel', serif"
            >
              {{ t('section.subclass') }}
            </p>

            <!-- Subclass tab buttons -->
            <div class="flex gap-3">
              <button
                v-for="sub in subclassData"
                :key="sub.name"
                class="flex-1 px-4 py-2.5 rounded-lg border-2 text-xs font-bold tracking-wider transition-all duration-200"
                :class="sub.selected
                  ? 'border-[var(--gold)] bg-[var(--gold-glow)] text-[var(--gold)]'
                  : 'border-[var(--border)] hover:border-[var(--gold-dim)] bg-[var(--bg-card)] text-[var(--text-dim)]'"
                :style="`font-family:'Cinzel',serif`"
                @click="store.selectSubclass(sub.selected ? null : sub.name)"
              >
                {{ sub.selected ? '✓ ' : '' }}{{ sub.name }}
              </button>
            </div>

            <!-- Cards of the selected subclass (individual toggles) -->
            <template v-if="store.selectedSubclass">
              <p class="text-[var(--text-dim)] text-xs">
                {{ t('section.subclass.pick', { name: store.selectedSubclass ?? '' }) }}
                <span class="text-[var(--gold)] ml-1">{{ store.selectedClassCards.size }}/{{ store.subclassCards.length }}</span>
              </p>

              <div :class="cardGridClass">
                <div
                  v-for="card in subclassData.find(s => s.selected)?.cards ?? []"
                  :key="card.id"
                  class="space-y-1"
                >
                  <CardThumbnail
                    :card="card"
                    :selected="store.isClassCardSelected(card.id)"
                    :selectable="true"
                    @click="store.toggleClassCard(card.id)"
                    @preview="openCard(card, store.subclassCards)"
                  />
                  <p
                    class="text-[10px] text-center uppercase tracking-wider font-semibold"
                    :style="`color: ${domainHex(store.activeClass!.dominio)}; font-family:'Cinzel',serif`"
                  >{{ TIPO_LABEL[card.tipo_carta ?? ''] ?? card.tipo_carta }}</p>
                </div>
              </div>
            </template>
          </div>
        </template>
      </div>
    </section>

    <!-- ══════════════════════════════════════════════════════════════════════
         IV · DOMINI  (auto-selected from class, shown as info)
         ══════════════════════════════════════════════════════════════════════ -->
    <section v-if="store.className" class="space-y-4">
      <div class="ornament">{{ t('section.domains') }}</div>

      <div class="panel p-5 space-y-4">
        <p class="text-[var(--text)] text-sm">
          {{ t('section.domains.info', { name: store.className ?? '' }) }}
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
          {{ t('section.domains.hint') }}
        </p>
      </div>
    </section>

    <!-- ══════════════════════════════════════════════════════════════════════
         V · ABILITÀ
         ══════════════════════════════════════════════════════════════════════ -->
    <section v-if="store.selectedDomains.length" class="space-y-4">
      <div class="ornament">{{ t('section.abilities') }}</div>

      <!-- Level filter pills -->
      <div class="flex flex-wrap gap-2 items-center">
        <button
          class="domain-chip"
          :class="{ active: filterLevel === 'all' }"
          @click="filterLevel = 'all'"
        >{{ t('section.abilities.all') }}</button>
        <button
          v-for="lvl in store.levels"
          :key="lvl"
          class="domain-chip"
          :class="{ active: filterLevel === lvl }"
          @click="filterLevel = lvl"
        >{{ t('section.abilities.level') }} {{ lvl }}</button>
        <span class="text-[var(--text-dim)] text-xs ml-auto">
          {{ store.selectedAbilities.size }} {{ t('section.abilities.selected') }}
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
          :class="cardGridClass"
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
          {{ t('section.abilities.empty') }}
        </p>
      </div>
    </section>

    <!-- ══════════════════════════════════════════════════════════════════════
         VI · NOME PERSONAGGIO
         ══════════════════════════════════════════════════════════════════════ -->
    <section class="space-y-4">
      <div class="ornament">{{ t('section.name') }}</div>
      <div class="panel p-4 space-y-2">
        <input
          type="text"
          :value="store.characterName"
          @input="store.setCharacterName(($event.target as HTMLInputElement).value)"
          :placeholder="t('section.name.placeholder')"
          class="w-full bg-transparent border border-[var(--border)] rounded-lg px-3 py-2.5
                 text-[var(--text)] placeholder-[var(--text-dim)]
                 focus:border-[var(--gold)] focus:outline-none transition-colors"
          style="font-family:'Cinzel',serif"
        />
        <p class="text-[var(--text-dim)] text-xs">
          {{ t('section.name.hint') }}
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
        <div class="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex flex-wrap items-center gap-3">
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
              <span class="hidden sm:inline"> {{ t('status.abilities') }}</span>
            </template>
            <span v-if="!store.className && !store.selectedOrigin && !store.characterName"
                  class="italic opacity-60">{{ t('status.empty') }}</span>
          </div>

          <!-- Card size controls -->
          <div class="flex items-center gap-1 flex-shrink-0">
            <button
              class="w-7 h-7 rounded flex items-center justify-center border border-[var(--border)] text-[var(--text-dim)] hover:text-[var(--gold)] hover:border-[var(--gold-dim)] transition-colors text-sm disabled:opacity-25 disabled:cursor-not-allowed"
              :disabled="cardSizeLevel <= 0"
              @click="cardSizeLevel--"
              :title="t('size.bigger')"
            >+</button>
            <button
              class="w-7 h-7 rounded flex items-center justify-center border border-[var(--border)] text-[var(--text-dim)] hover:text-[var(--gold)] hover:border-[var(--gold-dim)] transition-colors text-sm disabled:opacity-25 disabled:cursor-not-allowed"
              :disabled="cardSizeLevel >= GRID_LEVELS.length - 1"
              @click="cardSizeLevel++"
              :title="t('size.smaller')"
            >−</button>
          </div>

          <div class="flex gap-2 flex-shrink-0 flex-wrap">
            <button
              class="btn-secondary"
              style="font-size:0.75rem; padding:0.4rem 1rem"
              @click="fileInput?.click()"
            >{{ t('btn.load') }}</button>
            <button
              class="btn-secondary"
              style="font-size:0.75rem; padding:0.4rem 1rem"
              @click="onReset"
              :disabled="!store.isDirty"
            >{{ t('btn.reset') }}</button>
            <button
              class="btn-secondary"
              style="font-size:0.75rem; padding:0.4rem 1rem"
              @click="onDownloadJson"
              :disabled="!store.className"
            >{{ t('btn.save') }}</button>
            <button
              class="btn-primary"
              style="font-size:0.75rem; padding:0.4rem 1rem"
              @click="onPrint"
              :disabled="!hasAnyCard"
            >{{ t('btn.print') }}</button>
            <button
              class="btn-primary"
              style="font-size:0.75rem; padding:0.4rem 1rem"
              @click="onDownloadZip"
              :disabled="downloading || !hasAnyCard"
            >{{ downloading ? '…' : t('btn.download') }}</button>
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

    <!-- ── Reusable confirmation dialog ───────────────────────────────────── -->
    <Teleport to="body">
      <Transition
        enter-active-class="transition-opacity duration-200"
        enter-from-class="opacity-0"
        leave-active-class="transition-opacity duration-200"
        leave-to-class="opacity-0"
      >
        <div
          v-if="confirmVisible"
          class="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4"
          @click.self="onConfirmAnswer(false)"
        >
          <div class="panel-gold max-w-sm w-full p-6 space-y-4 text-center">
            <p
              class="text-[var(--gold)] text-lg font-bold"
              style="font-family:'Cinzel',serif"
            >{{ confirmTitle }}</p>
            <p class="text-[var(--text)] text-sm leading-relaxed">
              {{ confirmMessage }}
            </p>
            <div class="flex gap-3 justify-center pt-2">
              <button
                class="btn-secondary"
                style="font-size:0.8rem; padding:0.5rem 1.5rem"
                @click="onConfirmAnswer(false)"
              >{{ confirmNo }}</button>
              <button
                class="btn-primary"
                style="font-size:0.8rem; padding:0.5rem 1.5rem"
                @click="onConfirmAnswer(true)"
              >{{ confirmYes }}</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>
