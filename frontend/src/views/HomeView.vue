<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useCharacterStore } from '@/stores/character'
import { DOMAIN_META } from '@/types/card'
import type { Dominio } from '@/types/card'
import DomainBadge from '@/components/DomainBadge.vue'
import CardThumbnail from '@/components/CardThumbnail.vue'
import CardModal from '@/components/CardModal.vue'
import { useDownload } from '@/composables/useDownload'

const router  = useRouter()
const store   = useCharacterStore()
const { loadSave, downloadSave } = useDownload()

// ── Class selection ──────────────────────────────────────────────────────────
const filterDomain   = ref<Dominio | null>(null)
const search         = ref('')
const previewCard    = ref<any>(null)
const fileInput      = ref<HTMLInputElement | null>(null)
const loadingZip     = ref(false)

const filteredClasses = computed(() => {
  let list = store.classes
  if (filterDomain.value) list = list.filter(c => c.dominio === filterDomain.value)
  if (search.value.trim()) {
    const q = search.value.toLowerCase()
    list = list.filter(c => c.nome.toLowerCase().includes(q))
  }
  return list
})

const allDomains = Object.keys(DOMAIN_META) as Dominio[]

function pickClass(nome: string) {
  store.selectClass(nome)
  router.push('/build')
}

async function onFileLoad(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  try {
    const save = await loadSave(file)
    store.fromSave(save)
    router.push('/build')
  } catch (err) {
    alert(String(err))
  }
}
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 py-8 space-y-8">
    <!-- Hero -->
    <div class="text-center space-y-3">
      <h1 class="text-4xl md:text-5xl font-bold text-yellow-500 tracking-widest uppercase">
        Costruisci il tuo Personaggio
      </h1>
      <p class="text-stone-400 text-lg max-w-xl mx-auto">
        Scegli la tua classe, seleziona i domini e costruisci il mazzo di carte del tuo PG.
      </p>

      <!-- Load save -->
      <div class="flex items-center justify-center gap-3 pt-2">
        <button class="btn-ghost text-sm" @click="fileInput?.click()">
          📂 Carica personaggio salvato
        </button>
        <input
          ref="fileInput"
          type="file"
          accept=".json"
          class="hidden"
          @change="onFileLoad"
        />
      </div>
    </div>

    <!-- Domain filter -->
    <div class="space-y-2">
      <p class="text-stone-500 text-xs uppercase tracking-widest">Filtra per dominio</p>
      <div class="flex flex-wrap gap-2">
        <button
          :class="[
            'domain-pill',
            filterDomain === null
              ? 'bg-stone-700 border-stone-500 text-stone-100'
              : 'border-stone-700 text-stone-500 hover:text-stone-300',
          ]"
          @click="filterDomain = null"
        >
          Tutti
        </button>
        <button
          v-for="d in allDomains"
          :key="d"
          class="domain-pill"
          @click="filterDomain = filterDomain === d ? null : d"
        >
          <DomainBadge :dominio="d" :active="filterDomain === d" size="sm" />
        </button>
      </div>
    </div>

    <!-- Search -->
    <div class="relative max-w-xs">
      <input
        v-model="search"
        type="search"
        placeholder="Cerca classe…"
        class="w-full bg-stone-800 border border-stone-700 rounded-lg px-4 py-2 text-sm
               text-stone-100 placeholder:text-stone-500 focus:outline-none focus:border-yellow-500"
      />
    </div>

    <!-- Class grid -->
    <div v-if="filteredClasses.length" class="space-y-6">
      <!-- Group by domain -->
      <template v-for="d in allDomains" :key="d">
        <div v-if="filteredClasses.some(c => c.dominio === d)">
          <div class="flex items-center gap-2 mb-3">
            <DomainBadge :dominio="d" :active="true" size="md" />
            <div class="h-px flex-1 bg-stone-800" />
          </div>
          <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
            <div
              v-for="cls in filteredClasses.filter(c => c.dominio === d)"
              :key="cls.nome"
              class="space-y-1.5"
            >
              <CardThumbnail
                v-if="cls.baseCard"
                :card="cls.baseCard"
                :selectable="false"
                @click="pickClass(cls.nome)"
                @preview="previewCard = $event"
              />
              <p class="text-center text-xs text-stone-400 font-bold truncate px-1">
                {{ cls.nome }}
              </p>
            </div>
          </div>
        </div>
      </template>
    </div>

    <div v-else class="text-center text-stone-600 py-12">
      Nessuna classe trovata
    </div>

    <CardModal
      :card="previewCard"
      @close="previewCard = null"
      @toggle="previewCard = null"
    />
  </div>
</template>
