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
  nome: string          // e.g. "TROVATORE"
  dominio: Dominio
  cards: CardIndex[]    // the 3 class-feature cards
}

export interface DomainMeta {
  name: Dominio
  label: string   // Italian display label
  color: string   // tailwind bg colour token
  accent: string  // tailwind text colour token
  icon: string    // emoji-style symbol
}

export const DOMAIN_META: Record<Dominio, DomainMeta> = {
  arcano:     { name: 'arcano',     label: 'Arcano',     color: 'bg-violet-600',  accent: 'text-violet-300', icon: '👁' },
  lama:       { name: 'lama',       label: 'Lama',       color: 'bg-red-600',     accent: 'text-red-300',    icon: '⚔️' },
  osso:       { name: 'osso',       label: 'Osso',       color: 'bg-amber-700',   accent: 'text-amber-200',  icon: '💀' },
  codice:     { name: 'codice',     label: 'Codice',     color: 'bg-blue-600',    accent: 'text-blue-300',   icon: '📖' },
  grazia:     { name: 'grazia',     label: 'Grazia',     color: 'bg-pink-600',    accent: 'text-pink-300',   icon: '🦢' },
  mezzanotte: { name: 'mezzanotte', label: 'Mezzanotte', color: 'bg-yellow-700',  accent: 'text-yellow-200', icon: '🌙' },
  saggio:     { name: 'saggio',     label: 'Saggio',     color: 'bg-green-700',   accent: 'text-green-300',  icon: '🍃' },
  splendore:  { name: 'splendore',  label: 'Splendore',  color: 'bg-yellow-500',  accent: 'text-yellow-900', icon: '☀️' },
  valore:     { name: 'valore',     label: 'Valore',     color: 'bg-orange-600',  accent: 'text-orange-200', icon: '🛡️' },
}

// All classes per domain (hard-coded from extraction)
export const CLASS_DOMAIN_MAP: Record<string, Dominio> = {
  'TROVATORE': 'grazia',
  'ORATORE': 'grazia',
  'CUSTODE DEGLI ELEMENTI': 'saggio',
  'CUSTODE DEL RINNOVAMENTO': 'saggio',
  'VALOROSO': 'valore',
  'VENDICATORE': 'valore',
  'FERALE': 'osso',
  'APRIPISTA': 'osso',
  'OMBRA NOTTURNA': 'mezzanotte',
  'LADRO': 'mezzanotte',
  'EMISSARIO DIVINO': 'splendore',
  'SENTINELLA ALATA': 'splendore',
  'POTERE ELEMENTALE': 'arcano',
  'POTERE PRIMORDIALE': 'arcano',
  'CHIAMATA DEL CORAGGIO': 'lama',
  'CHIAMATA DELLO STERMINATORE': 'lama',
  'SCUOLA DELLA CONOSCENZA': 'codice',
  'SCUOLA DELLA GUERRA': 'codice',
}

// Saved character format (for upload/download)
export interface CharacterSave {
  version: 1
  exportDate: string
  className: string
  classCardIds: string[]
  selectedDomains: Dominio[]
  selectedAbilities: string[]   // card IDs
}
