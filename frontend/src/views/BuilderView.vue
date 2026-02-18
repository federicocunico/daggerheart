<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useCharacterStore } from '@/stores/character'
import { DOMAIN_META } from '@/types/card'
import type { Dominio, CardIndex } from '@/types/card'
import DomainBadge from '@/components/DomainBadge.vue'
import CardThumbnail from '@/components/CardThumbnail.vue'
import CardModal from '@/components/CardModal.vue'
import { useDownload } from '@/composables/useDownload'

const router = useRouter()
const store  = useCharacterStore()
const { downloadSet, downloadSave, loadSave } = useDownload()

// Redirect home if no class selected
watch(() => store.className, v => { if (!v) router.replace('/') }, { immediate: true })

// ── Tabs ─────────────────────────────────────────────────────────────────────
type Tab = 'classe' | 'abilita' | 'origine' | 'comunita'
const activeTab = ref<Tab>('classe')

// ── Domain selection ─────────────────────────────────────────────────────────
const allDomains = Object.keys(DOMAIN_META) as Dominio[]
const MAX_DOMAINS = 2

function toggleDomain(d: Dominio) {
  if (store.selectedDomains.includes(d)) {
    store.toggleDomain(d)
  } else if (store.selectedDomains.length < MAX_DOMAINS) {
    store.toggleDomain(d)
  }
}

// ── Card preview ─────────────────────────────────────────────────────────────
const previewCard = ref<CardIndex | null>(null)

// ── Level filter ─────────────────────────────────────────────────────────────
const filterLevel = ref<number | 'all'>('all')
const filterType  = ref<string>('all')

const availableTypes = computed(() => {
  const types = new Set<string>()
  for (const c of store.abilityCards) {
    if (c.tipo_carta) types.add(c.tipo_carta)
  }
  return [...types].sort()
})

const filteredAbilities = computed(() => {
  let cards = store.abilityCards
  if (filterLevel.value !== 'all') cards = cards.filter(c => c.livello === filterLevel.value)
  if (filterType.value  !== 'all') cards = cards.filter(c => c.tipo_carta === filterType.value)
  return cards
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

// ── Download ─────────────────────────────────────────────────────────────────
const downloading = ref(false)
const fileInput   = ref<HTMLInputElement | null>(null)

async function onDownloadZip() {
  downloading.value = true
  try {
    const selectedCards = store.allCards.filter(c => store.selectedAbilities.has(c.id))
    await downloadSet(store.toSave(), store.classCards, selectedCards)
  } finally {
    downloading.value = false
  }
}

function onDownloadJson() {
  downloadSave(store.toSave())
}

async function onLoadFile(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  try {
    const save = await loadSave(file)
    store.fromSave(save)
  } catch (err) {
    alert(String(err))
  }
}
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 py-6 space-y-6">
    <!-- Back + class name -->
    <div class="flex items-center gap-3">
      <button @click="router.push('/')" class="btn-ghost text-sm">← Torna</button>
      <h2 class="text-2xl font-bold text-yellow-400 tracking-wider">{{ store.className }}</h2>
      <DomainBadge
        v-if="store.activeClass"
        :dominio="store.activeClass.dominio"
        :active="true"
        size="sm"
      />
    </div>

    <!-- Tabs -->
    <div class="flex gap-0 border-b border-stone-800">
      <button
        v-for="{ id, label } in [
          { id: 'classe',   label: '🎴 Classe' },
          { id: 'abilita',  label: '⚡ Abilità' },
          { id: 'origine',  label: '🌍 Origine' },
          { id: 'comunita', label: '🏘 Comunità' },
        ]"
        :key="id"
        @click="activeTab = id as Tab"
        :class="[
          'px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px',
          activeTab === id
            ? 'border-yellow-500 text-yellow-400'
            : 'border-transparent text-stone-500 hover:text-stone-300',
        ]"
      >
        {{ label }}
      </button>
    </div>

    <!-- ── CLASSE tab ────────────────────────────────────────────────────── -->
    <div v-show="activeTab === 'classe'" class="space-y-6">
      <!-- Domain selection -->
      <div class="glass rounded-xl p-4 space-y-3">
        <div class="flex items-center justify-between">
          <p class="font-bold text-stone-200">Scegli i tuoi domini (max {{ MAX_DOMAINS }})</p>
          <span class="text-stone-500 text-sm">{{ store.selectedDomains.length }}/{{ MAX_DOMAINS }}</span>
        </div>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="d in allDomains"
            :key="d"
            @click="toggleDomain(d)"
            :disabled="!store.selectedDomains.includes(d) && store.selectedDomains.length >= MAX_DOMAINS"
            class="transition-all duration-150"
          >
            <DomainBadge
              :dominio="d"
              :active="store.selectedDomains.includes(d)"
              size="md"
            />
          </button>
        </div>
        <p class="text-stone-500 text-xs">
          In Daggerheart ogni classe accede a 2 domini per le carte abilità.
        </p>
      </div>

      <!-- Class feature cards -->
      <div>
        <p class="text-stone-400 text-sm uppercase tracking-widest mb-3">Carte di classe</p>
        <div class="grid grid-cols-2 sm:grid-cols-3 gap-3 max-w-2xl">
          <CardThumbnail
            v-for="card in store.classCards"
            :key="card.id"
            :card="card"
            :selectable="false"
            @click="previewCard = card"
            @preview="previewCard = card"
          />
        </div>
      </div>

      <!-- Action -->
      <button
        v-if="store.selectedDomains.length"
        @click="activeTab = 'abilita'"
        class="btn-gold"
      >
        Vai alle abilità →
      </button>
    </div>

    <!-- ── ABILITÀ tab ───────────────────────────────────────────────────── -->
    <div v-show="activeTab === 'abilita'" class="space-y-4">
      <!-- Domain check -->
      <div v-if="!store.selectedDomains.length" class="glass rounded-xl p-6 text-center">
        <p class="text-stone-400">Seleziona prima i tuoi domini nella tab <strong>Classe</strong>.</p>
        <button @click="activeTab = 'classe'" class="btn-ghost mt-3 text-sm">← Vai a Classe</button>
      </div>

      <template v-else>
        <!-- Filters -->
        <div class="flex flex-wrap gap-3 items-center">
          <select
            v-model="filterLevel"
            class="bg-stone-800 border border-stone-700 text-stone-200 rounded-lg px-3 py-1.5 text-sm"
          >
            <option value="all">Tutti i livelli</option>
            <option v-for="lvl in store.levels" :key="lvl" :value="lvl">Livello {{ lvl }}</option>
          </select>
          <select
            v-model="filterType"
            class="bg-stone-800 border border-stone-700 text-stone-200 rounded-lg px-3 py-1.5 text-sm"
          >
            <option value="all">Tutti i tipi</option>
            <option v-for="t in availableTypes" :key="t" :value="t">{{ t }}</option>
          </select>
          <span class="text-stone-500 text-sm">
            {{ filteredAbilities.length }} carte
            · {{ store.selectedAbilities.size }} selezionate
          </span>
        </div>

        <!-- Cards grouped by domain -->
        <div
          v-for="d in store.selectedDomains"
          :key="d"
          class="space-y-3"
        >
          <div v-if="groupedByDomain[d]?.length" class="space-y-2">
            <div class="flex items-center gap-2">
              <DomainBadge :dominio="d" :active="true" size="sm" />
              <span class="text-stone-500 text-xs">{{ groupedByDomain[d].length }} carte</span>
              <div class="h-px flex-1 bg-stone-800" />
            </div>
            <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-2">
              <CardThumbnail
                v-for="card in groupedByDomain[d]"
                :key="card.id"
                :card="card"
                :selected="store.isSelected(card.id)"
                :selectable="true"
                @click="store.toggleAbility(card.id)"
                @preview="previewCard = card"
              />
            </div>
          </div>
          <div v-else class="text-stone-600 text-sm italic">
            Nessuna carta per questo dominio con i filtri attivi.
          </div>
        </div>
      </template>
    </div>

    <!-- ── ORIGINE tab ──────────────────────────────────────────────────── -->
    <div v-show="activeTab === 'origine'" class="space-y-3">
      <p class="text-stone-400 text-sm">
        Carte Origine (per informazione, non vengono incluse nel download del mazzo).
      </p>
      <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
        <CardThumbnail
          v-for="card in store.originCards"
          :key="card.id"
          :card="card"
          :selectable="false"
          @click="previewCard = card"
          @preview="previewCard = card"
        />
      </div>
    </div>

    <!-- ── COMUNITÀ tab ─────────────────────────────────────────────────── -->
    <div v-show="activeTab === 'comunita'" class="space-y-3">
      <p class="text-stone-400 text-sm">
        Carte Comunità (per informazione, non vengono incluse nel download del mazzo).
      </p>
      <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
        <CardThumbnail
          v-for="card in store.communityCards"
          :key="card.id"
          :card="card"
          :selectable="false"
          @click="previewCard = card"
          @preview="previewCard = card"
        />
      </div>
    </div>

    <!-- ── Download bar (sticky bottom) ─────────────────────────────────── -->
    <Teleport to="body">
      <div
        v-if="store.className"
        class="fixed bottom-0 left-0 right-0 z-30 border-t border-stone-700 bg-stone-950/95 backdrop-blur"
      >
        <div class="max-w-7xl mx-auto px-4 py-3 flex flex-wrap items-center gap-3 justify-between">
          <div class="text-sm text-stone-400">
            <span class="text-yellow-400 font-bold">{{ store.selectedAbilities.size }}</span>
            abilità selezionate
            <span v-if="store.selectedDomains.length" class="text-stone-600">
              · {{ store.selectedDomains.map(d => DOMAIN_META[d].icon + ' ' + DOMAIN_META[d].label).join(', ') }}
            </span>
          </div>
          <div class="flex gap-2 flex-wrap">
            <button
              class="btn-ghost text-xs"
              @click="fileInput?.click()"
            >
              📂 Carica
            </button>
            <button
              class="btn-ghost text-xs"
              @click="onDownloadJson"
              :disabled="!store.className"
            >
              💾 Salva JSON
            </button>
            <button
              class="btn-gold text-sm"
              @click="onDownloadZip"
              :disabled="downloading || store.selectedAbilities.size === 0"
            >
              {{ downloading ? '⏳ Preparando…' : '⬇ Scarica mazzo ZIP' }}
            </button>
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

    <!-- Spacer for sticky bar -->
    <div class="h-20" />

    <CardModal
      :card="previewCard"
      :selected="previewCard ? store.isSelected(previewCard.id) : false"
      @close="previewCard = null"
      @toggle="card => { store.toggleAbility(card.id); previewCard = null }"
    />
  </div>
</template>
