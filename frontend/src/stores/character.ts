import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { CardIndex, Dominio, CharacterSave } from '@/types/card'
import { CLASS_DOMAIN_MAP, CLASS_DOMAINS, SUBCLASS_TO_CLASS } from '@/types/card'

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
  const characterName     = ref<string>('')
  const className         = ref<string | null>(null)
  const selectedSubclass  = ref<string | null>(null)
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

  // The 2 subclass names for the active class (in page order)
  const subclasses = computed((): string[] => {
    if (!activeClass.value) return []
    const seen = new Set<string>()
    const result: string[] = []
    for (const c of activeClass.value.cards) {
      if (!seen.has(c.nome)) {
        seen.add(c.nome)
        result.push(c.nome)
      }
    }
    return result
  })

  // All class cards; if a subclass is selected, filtered to its 3 cards only
  const classCards = computed(() => {
    const all = activeClass.value?.cards ?? []
    if (selectedSubclass.value) {
      return all.filter(c => c.nome === selectedSubclass.value)
    }
    return all
  })

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

  // The 2 domains compatible with the chosen class (or empty if no class)
  const classDomains = computed((): [Dominio, Dominio] | [] =>
    className.value ? (CLASS_DOMAINS[className.value] ?? []) : []
  )

  // ── Actions ──────────────────────────────────────────────────────────────────
  function selectClass(nome: string) {
    className.value     = nome
    selectedSubclass.value = null
    selectedAbilities.value = new Set()
    // Auto-select the 2 domains for this class
    selectedDomains.value = [...(CLASS_DOMAINS[nome] ?? [])]
  }

  function selectSubclass(nome: string | null) {
    selectedSubclass.value = nome
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

  function setCharacterName(name: string) {
    characterName.value = name
  }

  function reset() {
    characterName.value = ''
    className.value = null
    selectedSubclass.value = null
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
      characterName: characterName.value,
      className: className.value ?? '',
      selectedSubclass: selectedSubclass.value,
      classCardIds: classCards.value.map(c => c.id),
      selectedDomains: [...selectedDomains.value],
      selectedAbilities: [...selectedAbilities.value],
      selectedOrigin: selectedOrigin.value,
      selectedCommunity: selectedCommunity.value,
    }
  }

  function fromSave(save: CharacterSave) {
    characterName.value = save.characterName ?? ''
    className.value = save.className
    selectedSubclass.value = save.selectedSubclass ?? null
    selectedDomains.value = save.selectedDomains
    selectedAbilities.value = new Set(save.selectedAbilities)
    selectedOrigin.value = save.selectedOrigin ?? null
    selectedCommunity.value = save.selectedCommunity ?? null
  }

  return {
    allCards, loading, error, loadCards,
    classes, activeClass, subclasses, classCards, abilityCards, cardsByLevel, levels,
    originCards, communityCards, classDomains,
    characterName,
    className, selectedSubclass, selectedDomains, selectedAbilities,
    selectedOrigin, selectedCommunity,
    selectClass, selectSubclass, toggleDomain, toggleAbility, isSelected,
    selectOrigin, selectCommunity, setCharacterName, reset,
    toSave, fromSave,
  }
})
