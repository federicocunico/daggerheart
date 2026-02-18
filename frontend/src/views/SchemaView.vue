<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCharacterStore } from '@/stores/character'
import { DOMAIN_META, CLASS_DOMAIN_MAP, SUBCLASS_TO_CLASS } from '@/types/card'
import type { Dominio, CardIndex } from '@/types/card'
import CardThumbnail from '@/components/CardThumbnail.vue'
import CardModal from '@/components/CardModal.vue'

// Lazy-load ECharts to keep initial bundle small
let echarts: typeof import('echarts') | null = null

const router = useRouter()
const store  = useCharacterStore()

// ── Side panel ────────────────────────────────────────────────────────────────
const selectedClass = ref<string | null>(null)
const previewCard   = ref<CardIndex | null>(null)
const previewCtx    = ref<CardIndex[]>([])

const selectedClassInfo = computed(() =>
  selectedClass.value
    ? store.classes.find(c => c.nome === selectedClass.value) ?? null
    : null
)

// Group class cards by their subclass name
const subclassGroups = computed(() => {
  if (!selectedClassInfo.value) return []
  const groups: { name: string; cards: CardIndex[] }[] = []
  const seen = new Set<string>()
  for (const card of selectedClassInfo.value.cards) {
    if (!seen.has(card.nome)) {
      seen.add(card.nome)
      groups.push({ name: card.nome, cards: [] })
    }
    groups.find(g => g.name === card.nome)!.cards.push(card)
  }
  return groups
})

function openCard(card: CardIndex, ctx: CardIndex[]) {
  previewCard.value = card
  previewCtx.value  = ctx
}

function pickClass() {
  if (selectedClass.value) {
    store.selectClass(selectedClass.value)
    router.push('/')
  }
}

// ── ECharts layout ────────────────────────────────────────────────────────────
// Domain order clockwise from top, matching the schema image
const DOMAIN_ORDER: Dominio[] = [
  'codice', 'splendore', 'valore', 'lama', 'osso', 'saggio', 'arcano', 'mezzanotte', 'grazia',
]

// Logical canvas 900×900; node symbolSize is in screen-pixels (does not scale)
const CX = 450, CY = 450, R_DOM = 165, R_CLS = 293, R_SUB = 422

function polar(deg: number, r: number): [number, number] {
  const rad = (deg - 90) * Math.PI / 180
  return [CX + r * Math.cos(rad), CY + r * Math.sin(rad)]
}

// Subclass→class grouping (deduplicated)
const subclassByClass: Record<string, string[]> = {}
for (const [sub, cls] of Object.entries(SUBCLASS_TO_CLASS)) {
  if (!subclassByClass[cls]) subclassByClass[cls] = []
  subclassByClass[cls].push(sub)
}
for (const cls of Object.keys(subclassByClass)) {
  subclassByClass[cls] = [...new Set(subclassByClass[cls])]
}

const CLASS_NAMES = Object.keys(CLASS_DOMAIN_MAP)

function buildOption() {
  const nodes: Record<string, unknown>[] = []
  const links: Record<string, unknown>[] = []

  // ── Domain nodes (inner ring) ───────────────────────────────────────────────
  DOMAIN_ORDER.forEach((d, i) => {
    const [x, y] = polar((i * 360) / DOMAIN_ORDER.length, R_DOM)
    nodes.push({
      id: `d:${d}`,
      name: DOMAIN_META[d].label,
      x, y,
      _type: 'domain', _key: d,
      symbolSize: 80,
      itemStyle: {
        color: DOMAIN_META[d].hex,
        shadowColor: DOMAIN_META[d].hex,
        shadowBlur: 22,
      },
      label: {
        show: true,
        formatter: `{ico|${DOMAIN_META[d].icon}}\n{lbl|${DOMAIN_META[d].label.toUpperCase()}}`,
        rich: {
          ico: { fontSize: 22, lineHeight: 26, color: '#fff' },
          lbl: { fontSize: 10, fontFamily: 'Cinzel, serif', fontWeight: 'bold', color: '#fff', lineHeight: 14 },
        },
      },
    })
  })

  // ── Class nodes (middle ring) ────────────────────────────────────────────────
  CLASS_NAMES.forEach(c => {
    const dom = (CLASS_DOMAIN_MAP[c] ?? 'arcano') as Dominio
    const di  = DOMAIN_ORDER.indexOf(dom)
    const [x, y] = polar((di * 360) / DOMAIN_ORDER.length, R_CLS)
    nodes.push({
      id: `c:${c}`,
      name: c,
      x, y,
      _type: 'class', _key: c,
      symbolSize: 66,
      itemStyle: {
        color: '#0e0e18',
        borderColor: DOMAIN_META[dom].hex,
        borderWidth: 3,
        shadowColor: DOMAIN_META[dom].hex,
        shadowBlur: 12,
      },
      label: {
        show: true,
        fontSize: 12,
        fontFamily: 'Cinzel, serif',
        fontWeight: 'bold',
        color: DOMAIN_META[dom].hex,
      },
    })
    links.push({
      source: `d:${dom}`,
      target: `c:${c}`,
      lineStyle: { color: DOMAIN_META[dom].hex, opacity: 0.55, width: 2 },
    })
  })

  // ── Subclass nodes (outer ring) — label placed outside below the circle ──────
  CLASS_NAMES.forEach(c => {
    const dom   = (CLASS_DOMAIN_MAP[c] ?? 'arcano') as Dominio
    const di    = DOMAIN_ORDER.indexOf(dom)
    const baseA = (di * 360) / DOMAIN_ORDER.length
    const subs  = subclassByClass[c] ?? []
    subs.forEach((s, i) => {
      const offset = subs.length === 1 ? 0 : (i === 0 ? -17 : 17)
      const [x, y] = polar(baseA + offset, R_SUB)
      nodes.push({
        id: `s:${s}`,
        name: s,           // full name, no truncation
        x, y,
        _type: 'subclass', _key: s, _class: c,
        symbolSize: 44,
        itemStyle: {
          color: DOMAIN_META[dom].hex + '30',
          borderColor: DOMAIN_META[dom].hex,
          borderWidth: 2,
          shadowColor: DOMAIN_META[dom].hex,
          shadowBlur: 5,
        },
        // Label OUTSIDE the circle: offset downward from node centre
        label: {
          show: true,
          position: [0, 30],   // 30px below node centre → sits just outside the 44px node
          fontSize: 9,
          fontFamily: 'Cinzel, serif',
          color: '#c9a84c',
          width: 84,
          overflow: 'break',
          lineHeight: 13,
          align: 'center',
        },
      })
      links.push({
        source: `c:${c}`,
        target: `s:${s}`,
        lineStyle: { color: DOMAIN_META[dom].hex, opacity: 0.35, width: 1.5 },
      })
    })
  })

  return {
    backgroundColor: 'transparent',
    series: [{
      type: 'graph',
      layout: 'none',
      animation: true,
      animationDuration: 500,
      data: nodes,
      links,
      roam: true,
      zoom: 1,
      scaleLimit: { min: 0.35, max: 4 },
      emphasis: {
        focus: 'adjacency',
        scale: true,
        scaleSize: 10,
        lineStyle: { width: 2.5 },
      },
      edgeSymbol: ['none', 'none'],
      lineStyle: { curveness: 0 },
    }],
  }
}

// ── Chart lifecycle ───────────────────────────────────────────────────────────
const chartRef = ref<HTMLDivElement | null>(null)
let chart: import('echarts').ECharts | null = null
let resizeHandler: (() => void) | null = null

onMounted(async () => {
  echarts = await import('echarts')
  if (!chartRef.value) return

  chart = echarts.init(chartRef.value, null, { renderer: 'svg' })
  chart.setOption(buildOption() as never)

  chart.on('click', 'series.graph.data', (params: Record<string, unknown>) => {
    const data = params.data as { _type: string; _key: string; _class?: string }
    if (data._type === 'class') {
      selectedClass.value = data._key
    } else if (data._type === 'subclass' && data._class) {
      selectedClass.value = data._class
    }
  })

  resizeHandler = () => chart?.resize()
  window.addEventListener('resize', resizeHandler)
})

onUnmounted(() => {
  if (resizeHandler) window.removeEventListener('resize', resizeHandler)
  chart?.dispose()
  chart = null
})
</script>

<template>
  <div class="flex flex-col lg:flex-row" style="min-height: calc(100vh - 56px)">

    <!-- ── Graph ──────────────────────────────────────────────────────────── -->
    <div class="relative flex-1">
      <div class="absolute top-3 left-1/2 -translate-x-1/2 text-center z-10 pointer-events-none px-4">
        <p
          class="text-[var(--gold)] text-xs uppercase tracking-[0.2em]"
          style="font-family:'Cinzel',serif"
        >
          Domini &amp; Classi · Clicca una classe
        </p>
      </div>

      <div
        ref="chartRef"
        class="w-full"
        style="height: calc(100vh - 116px); min-height: 380px"
      />
    </div>

    <!-- ── Side panel (slides in when class selected) ─────────────────────── -->
    <Transition
      enter-active-class="transition-all duration-300 ease-out"
      enter-from-class="opacity-0 lg:translate-x-6"
      leave-active-class="transition-all duration-200 ease-in"
      leave-to-class="opacity-0 lg:translate-x-6"
    >
      <aside
        v-if="selectedClass"
        class="lg:w-[420px] xl:w-[480px] border-t lg:border-t-0 lg:border-l border-[var(--border)]
               bg-[var(--bg-panel)] flex flex-col"
        style="max-height: calc(100vh - 56px)"
      >
        <!-- Header -->
        <div class="flex items-start justify-between p-4 border-b border-[var(--border)] flex-shrink-0">
          <div>
            <h3
              class="text-[var(--gold)] font-bold tracking-wider text-xl"
              style="font-family:'Cinzel',serif"
            >{{ selectedClass }}</h3>
            <div
              v-if="selectedClassInfo"
              class="flex items-center gap-1.5 text-sm mt-1"
              :style="`color: ${DOMAIN_META[selectedClassInfo.dominio].hex}`"
            >
              {{ DOMAIN_META[selectedClassInfo.dominio].icon }}
              Dominio {{ DOMAIN_META[selectedClassInfo.dominio].label }}
            </div>
          </div>
          <button
            @click="selectedClass = null"
            class="text-[var(--text-dim)] hover:text-[var(--text)] text-2xl leading-none mt-1"
            aria-label="Chiudi"
          >×</button>
        </div>

        <!-- Subclass card groups (scrollable) -->
        <div class="flex-1 overflow-y-auto p-4 space-y-6">
          <div
            v-for="group in subclassGroups"
            :key="group.name"
            class="space-y-2"
          >
            <div
              class="ornament text-xs"
              :style="selectedClassInfo ? `color: ${DOMAIN_META[selectedClassInfo.dominio].hex}` : ''"
            >
              {{ group.name }}
            </div>
            <div class="grid grid-cols-3 gap-3">
              <div
                v-for="card in group.cards"
                :key="card.id"
                class="space-y-1"
              >
                <CardThumbnail
                  :card="card"
                  :selectable="false"
                  @click="openCard(card, selectedClassInfo?.cards ?? [])"
                  @preview="openCard(card, selectedClassInfo?.cards ?? [])"
                />
                <p class="text-center text-[10px] text-[var(--text-dim)] leading-tight px-0.5 truncate">
                  {{ card.tipo_carta }}
                </p>
              </div>
            </div>
          </div>

          <div
            v-if="!subclassGroups.length"
            class="text-center py-8 text-[var(--text-dim)] text-sm italic"
          >
            Caricamento in corso…
          </div>
        </div>

        <!-- Choose button -->
        <div class="p-4 border-t border-[var(--border)] flex-shrink-0">
          <button class="btn-primary w-full justify-center" @click="pickClass">
            Scegli {{ selectedClass }} →
          </button>
        </div>
      </aside>
    </Transition>

    <!-- Empty state (desktop) -->
    <div
      v-if="!selectedClass"
      class="hidden lg:flex lg:w-52 border-l border-[var(--border)]
             bg-[var(--bg-panel)] items-center justify-center p-6 text-center"
    >
      <p class="text-[var(--text-dim)] text-sm italic leading-relaxed">
        Clicca su una delle
        <strong class="text-[var(--gold)]">classi</strong>
        nel grafico per vederne le carte.
      </p>
    </div>

    <!-- Card preview modal -->
    <CardModal
      :card="previewCard"
      :navCards="previewCtx"
      :selected="false"
      @close="previewCard = null"
      @navigate="card => { previewCard = card }"
    />
  </div>
</template>
