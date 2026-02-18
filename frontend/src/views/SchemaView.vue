<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useCharacterStore } from '@/stores/character'
import { DOMAIN_META, CLASS_DOMAIN_MAP, CLASS_DOMAINS, SUBCLASS_TO_CLASS } from '@/types/card'
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
const DOMAIN_ORDER: Dominio[] = [
  'codice', 'splendore', 'valore', 'lama', 'osso', 'saggio', 'arcano', 'mezzanotte', 'grazia',
]

// Canvas 1400×1400 — 3-ring layout: domains inner, classes middle, subclasses outer
// Gap domain→class is doubled; outer ring further out to avoid overlap
const CX = 700, CY = 700
const R_DOM = 165   // inner ring
const R_CLS = 430   // middle ring  (gap ~265 vs previous ~140)
const R_SUB = 660   // outer ring   (gap ~230)

function polar(deg: number, r: number): [number, number] {
  const rad = (deg - 90) * Math.PI / 180
  return [CX + r * Math.cos(rad), CY + r * Math.sin(rad)]
}

// Angular midpoint between two degree values (handles 0°/360° wraparound correctly)
function circularMidpoint(deg1: number, deg2: number): number {
  const r1 = deg1 * Math.PI / 180
  const r2 = deg2 * Math.PI / 180
  const x = Math.cos(r1) + Math.cos(r2)
  const y = Math.sin(r1) + Math.sin(r2)
  const mid = Math.atan2(y, x) * 180 / Math.PI
  return ((mid % 360) + 360) % 360
}

// Label position radially outward from the canvas centre
function radialLabelPos(angleDeg: number): string {
  const a = ((angleDeg % 360) + 360) % 360
  if (a <= 45 || a > 315) return 'top'
  if (a > 45 && a <= 135) return 'right'
  if (a > 135 && a <= 225) return 'bottom'
  return 'left'
}

// Subclass→class grouping (for tooltip)
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

  // ── Domain nodes (inner ring) ─────────────────────────────────────────────
  DOMAIN_ORDER.forEach((d, i) => {
    const [x, y] = polar((i * 360) / DOMAIN_ORDER.length, R_DOM)
    nodes.push({
      id: `d:${d}`,
      name: DOMAIN_META[d].label,
      x, y,
      _type: 'domain', _key: d,
      symbolSize: 56,
      itemStyle: {
        color: DOMAIN_META[d].hex,
        shadowColor: DOMAIN_META[d].hex,
        shadowBlur: 18,
      },
      label: {
        show: true,
        formatter: `{ico|${DOMAIN_META[d].icon}}\n{lbl|${DOMAIN_META[d].label.toUpperCase()}}`,
        rich: {
          ico: { fontSize: 20, lineHeight: 24, color: '#fff' },
          lbl: { fontSize: 9, fontFamily: 'Cinzel, serif', fontWeight: 'bold', color: '#fff', lineHeight: 12 },
        },
      },
    })
  })

  // ── Class nodes (middle ring) — positioned at midpoint between their 2 domains ──
  CLASS_NAMES.forEach(c => {
    const [dom1, dom2] = (CLASS_DOMAINS[c] ?? [CLASS_DOMAIN_MAP[c] ?? 'arcano', CLASS_DOMAIN_MAP[c] ?? 'arcano']) as [Dominio, Dominio]
    const di1   = DOMAIN_ORDER.indexOf(dom1)
    const di2   = DOMAIN_ORDER.indexOf(dom2)
    const ang1  = (di1 * 360) / DOMAIN_ORDER.length
    const ang2  = (di2 * 360) / DOMAIN_ORDER.length
    const angle = circularMidpoint(ang1, ang2)
    const [x, y] = polar(angle, R_CLS)
    const dom   = dom1  // primary domain for border colour
    nodes.push({
      id: `c:${c}`,
      name: c,
      x, y,
      _type: 'class', _key: c,
      symbolSize: 74,
      itemStyle: {
        color: '#0e0e18',
        borderColor: DOMAIN_META[dom].hex,
        borderWidth: 3,
        shadowColor: DOMAIN_META[dom].hex,
        shadowBlur: 16,
      },
      label: {
        show: true,
        // position default = 'inside' (centered in symbol)
        fontSize: 10,
        fontFamily: 'Cinzel, serif',
        fontWeight: 'bold',
        color: DOMAIN_META[dom].hex,
        overflow: 'breakAll',
        width: 62,
        lineHeight: 14,
        align: 'center',
      },
    })
    // Each class connects to BOTH its domains
    links.push({
      source: `d:${dom1}`,
      target: `c:${c}`,
      lineStyle: { color: DOMAIN_META[dom1].hex, opacity: 0.55, width: 2 },
    })
    links.push({
      source: `d:${dom2}`,
      target: `c:${c}`,
      lineStyle: { color: DOMAIN_META[dom2].hex, opacity: 0.55, width: 2 },
    })
  })

  // ── Subclass nodes (outer ring) — ±9° around the class midpoint angle ─────
  CLASS_NAMES.forEach(c => {
    const [dom1, dom2] = (CLASS_DOMAINS[c] ?? [CLASS_DOMAIN_MAP[c] ?? 'arcano', CLASS_DOMAIN_MAP[c] ?? 'arcano']) as [Dominio, Dominio]
    const di1   = DOMAIN_ORDER.indexOf(dom1)
    const di2   = DOMAIN_ORDER.indexOf(dom2)
    const ang1  = (di1 * 360) / DOMAIN_ORDER.length
    const ang2  = (di2 * 360) / DOMAIN_ORDER.length
    const baseA = circularMidpoint(ang1, ang2)
    const dom   = dom1 as Dominio
    const subs  = subclassByClass[c] ?? []
    subs.forEach((s, i) => {
      const offset = subs.length === 1 ? 0 : (i === 0 ? -9 : 9)
      const angle  = baseA + offset
      const [x, y] = polar(angle, R_SUB)
      nodes.push({
        id: `s:${s}`,
        name: s,
        x, y,
        _type: 'subclass', _key: s, _class: c,
        symbolSize: 52,
        itemStyle: {
          color: DOMAIN_META[dom].hex + '28',
          borderColor: DOMAIN_META[dom].hex,
          borderWidth: 2,
          shadowColor: DOMAIN_META[dom].hex,
          shadowBlur: 6,
        },
        label: {
          show: true,
          // position default = 'inside'
          fontSize: 7,
          fontFamily: 'Cinzel, serif',
          color: '#c9a84c',
          overflow: 'breakAll',
          width: 42,
          lineHeight: 10,
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
    tooltip: {
      trigger: 'item',
      backgroundColor: '#12121f',
      borderColor: '#c9a84c55',
      padding: [8, 12],
      textStyle: { color: '#e8d5a3', fontFamily: 'Cinzel, serif', fontSize: 12 },
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      formatter: (params: any) => {
        const data = params.data as { _type: string; name: string; _key: string; _class?: string }
        if (data._type === 'class') {
          const subs = (subclassByClass[data._key] ?? [])
            .map((s: string) => `<span style="color:#c9a84c">◆</span> ${s}`)
            .join('<br/>')
          return `<b style="color:#e8d5a3">${data.name}</b><br/><span style="font-size:11px;opacity:.8">${subs}</span>`
        }
        if (data._type === 'subclass') {
          return `<b style="color:#e8d5a3">${data.name}</b><br/><span style="color:#c9a84c;font-size:11px">→ ${data._class ?? ''}</span>`
        }
        return `<b>${data.name}</b>`
      },
    },
    series: [{
      type: 'graph',
      layout: 'none',
      animation: true,
      animationDuration: 500,
      data: nodes,
      links,
      roam: true,
      zoom: 0.88,
      scaleLimit: { min: 0.3, max: 4 },
      emphasis: {
        focus: 'adjacency',
        scale: true,
        scaleSize: 6,
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

  // canvas renderer: pointer events are captured over the full canvas area,
  // not just on individual SVG elements — fixes pan/zoom dead zones
  chart = echarts.init(chartRef.value, null, { renderer: 'canvas' })
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

  // Resize chart when side panel opens/closes (it changes the container width)
  watch(selectedClass, async () => {
    await nextTick()
    chart?.resize()
  })
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
          Domini &amp; Classi · Clicca una classe o sottoclasse
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
        o <strong class="text-[var(--gold)]">sottoclassi</strong>
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
