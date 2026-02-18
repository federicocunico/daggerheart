import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { CardIndex, Dominio, CharacterSave } from '@/types/card'
import { CLASS_DOMAIN_MAP, SUBCLASS_TO_CLASS } from '@/types/card'

export const useCharacterStore = defineStore('character', () => {
  // ── All cards loaded from index.json ────────────────────────────────────────
  const allCards = ref<CardIndex[]>([])
  const loading  = ref(false)
  const error    = ref<string | null>(null)

  async function loadCards(baseUrl: string = '') {
    if (allCards.value.length) return
    loading.value = true
    try {
      const res = await fetch(`${baseUrl}cards/index.json`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      allCards.value = await res.json()
    } catch (e) {
      error.value = String(e)
    } finally {
      loading.value = false
    }
  }

  // ── Character state ──────────────────────────────────────────────────────────
  const className         = ref<string | null>(null)
  const selectedDomains   = ref<Dominio[]>([])
  const selectedAbilities = ref<Set<string>>(new Set())
  const selectedOrigin    = ref<string | null>(null)
  const selectedCommunity = ref<string | null>(null)

  // ── Derived: classes (grouped by Italian class name) ─────────────────────────
  const classes = computed(() => {
    const map = new Map<string, CardIndex[]>()
    for (const c of allCards.value) {
      if (c.sottocategoria !== 'classi') continue
      const clsName = SUBCLASS_TO_CLASS[c.nome] ?? c.nome
      if (!map.has(clsName)) map.set(clsName, [])
      map.get(clsName)!.push(c)
    }
    return [...map.entries()].map(([nome, cards]) => ({
      nome,
      dominio: (CLASS_DOMAIN_MAP[nome] ?? 'arcano') as Dominio,
      cards: cards.sort((a, b) => a.pagina - b.pagina),
      baseCard: cards.find(c => c.tipo_carta === 'privilegio') ?? cards[0],
    }))
  })

  const activeClass = computed(() =>
    classes.value.find(c => c.nome === className.value) ?? null
  )

  const classCards = computed(() => activeClass.value?.cards ?? [])

  const abilityCards = computed(() =>
    allCards.value.filter(
      c => c.sottocategoria === 'abilita' &&
           selectedDomains.value.includes(c.dominio as Dominio)
    )
  )

  const cardsByLevel = computed(() => {
    const map: Record<number, CardIndex[]> = {}
    for (const c of abilityCards.value) {
      const lvl = c.livello ?? 0
      if (!map[lvl]) map[lvl] = []
      map[lvl].push(c)
    }
    return map
  })

  const levels = computed(() =>
    Object.keys(cardsByLevel.value).map(Number).sort((a, b) => a - b)
  )

  const originCards    = computed(() => allCards.value.filter(c => c.categoria === 'origine'))
  const communityCards = computed(() => allCards.value.filter(c => c.categoria === 'comunità'))

  // ── Actions ──────────────────────────────────────────────────────────────────
  function selectClass(nome: string) {
    className.value = nome
    selectedDomains.value = []
    selectedAbilities.value = new Set()
  }

  function toggleDomain(dominio: Dominio) {
    const idx = selectedDomains.value.indexOf(dominio)
    if (idx >= 0) {
      selectedDomains.value.splice(idx, 1)
      for (const id of selectedAbilities.value) {
        const card = allCards.value.find(c => c.id === id)
        if (card?.dominio === dominio) selectedAbilities.value.delete(id)
      }
      selectedAbilities.value = new Set(selectedAbilities.value)
    } else {
      selectedDomains.value.push(dominio)
    }
  }

  function toggleAbility(id: string) {
    if (selectedAbilities.value.has(id)) {
      selectedAbilities.value.delete(id)
    } else {
      selectedAbilities.value.add(id)
    }
    selectedAbilities.value = new Set(selectedAbilities.value)
  }

  function isSelected(id: string) {
    return selectedAbilities.value.has(id)
  }

  function selectOrigin(id: string | null) {
    selectedOrigin.value = id
  }

  function selectCommunity(id: string | null) {
    selectedCommunity.value = id
  }

  function reset() {
    className.value = null
    selectedDomains.value = []
    selectedAbilities.value = new Set()
    selectedOrigin.value = null
    selectedCommunity.value = null
  }

  // ── Save / Load ───────────────────────────────────────────────────────────────
  function toSave(): CharacterSave {
    return {
      version: 1,
      exportDate: new Date().toISOString(),
      className: className.value ?? '',
      classCardIds: classCards.value.map(c => c.id),
      selectedDomains: [...selectedDomains.value],
      selectedAbilities: [...selectedAbilities.value],
      selectedOrigin: selectedOrigin.value,
      selectedCommunity: selectedCommunity.value,
    }
  }

  function fromSave(save: CharacterSave) {
    className.value = save.className
    selectedDomains.value = save.selectedDomains
    selectedAbilities.value = new Set(save.selectedAbilities)
    selectedOrigin.value = save.selectedOrigin ?? null
    selectedCommunity.value = save.selectedCommunity ?? null
  }

  return {
    allCards, loading, error, loadCards,
    classes, activeClass, classCards, abilityCards, cardsByLevel, levels,
    originCards, communityCards,
    className, selectedDomains, selectedAbilities, selectedOrigin, selectedCommunity,
    selectClass, toggleDomain, toggleAbility, isSelected,
    selectOrigin, selectCommunity, reset,
    toSave, fromSave,
  }
})
