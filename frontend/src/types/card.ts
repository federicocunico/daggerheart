export type Categoria = 'origine' | 'comunità' | 'dominio'
export type Sottocategoria = 'classi' | 'abilita' | null
export type Dominio =
  | 'arcano' | 'lama' | 'osso' | 'codice'
  | 'grazia' | 'mezzanotte' | 'saggio' | 'splendore' | 'valore'

export interface CardIndex {
  id: string
  nome: string
  categoria: Categoria
  dominio: Dominio | null
  sottocategoria: Sottocategoria
  tipo_carta: string | null
  livello: number | null
  soglia: number | null
  pagina: number
  img: string
  json: string
}

export interface ClassInfo {
  nome: string          // Italian class name e.g. "Bardo"
  dominio: Dominio
  cards: CardIndex[]    // all 6 cards (2 subclasses × 3 cards)
  baseCard?: CardIndex  // first card for thumbnail
}

export interface DomainMeta {
  name: Dominio
  label: string   // Italian display label
  color: string   // Tailwind bg class (for DomainBadge)
  accent: string  // Tailwind text class
  hex: string     // CSS hex color for inline styles
  icon: string    // Unicode symbol
}

export const DOMAIN_META: Record<Dominio, DomainMeta> = {
  arcano:     { name: 'arcano',     label: 'Arcano',     color: 'bg-violet-600',  accent: 'text-violet-300', hex: '#9b5db8', icon: '✦' },
  lama:       { name: 'lama',       label: 'Lama',       color: 'bg-red-600',     accent: 'text-red-300',    hex: '#c84444', icon: '⚔' },
  osso:       { name: 'osso',       label: 'Osso',       color: 'bg-amber-700',   accent: 'text-amber-200',  hex: '#c9a84c', icon: '☽' },
  codice:     { name: 'codice',     label: 'Codice',     color: 'bg-blue-600',    accent: 'text-blue-300',   hex: '#4477b8', icon: '✒' },
  grazia:     { name: 'grazia',     label: 'Grazia',     color: 'bg-pink-600',    accent: 'text-pink-300',   hex: '#c84477', icon: '✿' },
  mezzanotte: { name: 'mezzanotte', label: 'Mezzanotte', color: 'bg-yellow-700',  accent: 'text-yellow-200', hex: '#8b7a32', icon: '◆' },
  saggio:     { name: 'saggio',     label: 'Saggio',     color: 'bg-green-700',   accent: 'text-green-300',  hex: '#44885e', icon: '❧' },
  splendore:  { name: 'splendore',  label: 'Splendore',  color: 'bg-yellow-500',  accent: 'text-yellow-900', hex: '#c9b800', icon: '☀' },
  valore:     { name: 'valore',     label: 'Valore',     color: 'bg-orange-600',  accent: 'text-orange-200', hex: '#c87028', icon: '⬡' },
}

// ── Class name mapping ────────────────────────────────────────────────────────
// The PDF stores subclass names (e.g. TROVATORE) as the card nome.
// These are grouped under the proper Italian class name.
export const SUBCLASS_TO_CLASS: Record<string, string> = {
  // Bardo (Bard) — Grazia
  'TROVATORE':                  'Bardo',
  'ORATORE':                    'Bardo',
  // Mago (Wizard) — Codice
  'SCUOLA DELLA CONOSCENZA':    'Mago',
  'SCUOLA DELLA GUERRA':        'Mago',
  // Serafino (Seraph) — Splendore
  'EMISSARIO DIVINO':           'Serafino',
  'SENTINELLA ALATA':           'Serafino',
  // Guardiano (Guardian) — Valore
  'VALOROSO':                   'Guardiano',
  'VENDICATORE':                'Guardiano',
  // Guerriero (Warrior) — Lama
  'CHIAMATA DEL CORAGGIO':      'Guerriero',
  'CHIAMATA DELLO STERMINATORE':'Guerriero',
  // Ranger — Osso
  'FERALE':                     'Ranger',
  'APRIPISTA':                  'Ranger',
  // Druido (Druid) — Saggio
  'CUSTODE DEGLI ELEMENTI':     'Druido',
  'CUSTODE DEL RINNOVAMENTO':   'Druido',
  // Stregone (Sorcerer) — Arcano
  'POTERE ELEMENTALE':          'Stregone',
  'POTERE PRIMORDIALE':         'Stregone',
  // Ladro (Rogue) — Mezzanotte
  'OMBRA NOTTURNA':             'Ladro',
  'LADRO':                      'Ladro',
}

// Italian class name → primary domain
export const CLASS_DOMAIN_MAP: Record<string, Dominio> = {
  'Bardo':     'grazia',
  'Mago':      'codice',
  'Serafino':  'splendore',
  'Guardiano': 'valore',
  'Guerriero': 'lama',
  'Ranger':    'osso',
  'Druido':    'saggio',
  'Stregone':  'arcano',
  'Ladro':     'mezzanotte',
}

// The 2 domains each class has access to (they form a circular chain).
// Source: official Daggerheart SRD — each domain appears in exactly 2 adjacent classes.
export const CLASS_DOMAINS: Record<string, [Dominio, Dominio]> = {
  'Bardo':     ['grazia',     'codice'],
  'Mago':      ['codice',     'splendore'],
  'Serafino':  ['splendore',  'valore'],
  'Guardiano': ['valore',     'lama'],
  'Guerriero': ['lama',       'osso'],
  'Ranger':    ['osso',       'saggio'],
  'Druido':    ['saggio',     'arcano'],
  'Stregone':  ['arcano',     'mezzanotte'],
  'Ladro':     ['mezzanotte', 'grazia'],
}

// Saved character format (for upload/download)
export interface CharacterSave {
  version: 1
  exportDate: string
  characterName: string
  className: string
  selectedSubclass: string | null
  classCardIds: string[]
  selectedDomains: Dominio[]
  selectedAbilities: string[]   // card IDs
  selectedOrigin: string | null
  selectedCommunity: string | null
}
