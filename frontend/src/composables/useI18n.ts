import { ref, computed } from 'vue'

export type Locale = 'it' | 'en'

const locale = ref<Locale>('it')

const messages: Record<Locale, Record<string, string>> = {
  it: {
    // Header
    'header.schema': 'Schema',

    // Loading / error
    'loading': 'Caricamento carte…',
    'error.title': 'Errore nel caricamento',
    'error.hint': 'Esegui {cmd} e verifica che la cartella {dir} sia accessibile.',

    // Footer
    'footer': 'Daggerheart © Darrington Press · Interfaccia non ufficiale',

    // Home
    'home.title': 'Daggerheart',
    'home.subtitle': 'Costruttore di Personaggi',
    'home.desc': 'Strumento non ufficiale per costruire e gestire i mazzi di carte del tuo personaggio Daggerheart, basato sull\'edizione italiana.',
    'home.start': 'Costruisci il tuo Personaggio',
    'home.start.desc': 'Scegli la tua classe, seleziona i domini e costruisci il mazzo di carte del tuo PG.',
    'home.schema': 'Visualizza lo Schema',
    'home.schema.desc': 'Esplora le relazioni tra classi, domini e sottoclassi in un grafico interattivo.',

    // Builder hero
    'builder.hero': 'Forgia il tuo destino. Scegli una classe per costruire il mazzo del tuo personaggio.',

    // Sections
    'section.origin': 'I · Origine',
    'section.origin.desc': 'Scegli la tua carta Origine (facoltativa).',
    'section.origin.ok': '✓ Selezionata',
    'section.community': 'II · Comunità',
    'section.community.desc': 'Scegli la tua carta Comunità (facoltativa).',
    'section.community.ok': '✓ Selezionata',
    'section.class': 'III · Classe',
    'section.class.select': 'Scegli la tua classe',
    'section.class.placeholder': '— Seleziona —',
    'section.subclass': 'Scegli la tua sottoclasse',
    'section.subclass.pick': 'Seleziona le carte di {name} da includere nel mazzo.',
    'section.domains': 'IV · Domini',
    'section.domains.info': 'La classe {name} ha accesso a questi due domini:',
    'section.domains.hint': 'Le carte abilità disponibili qui sotto provengono da questi due domini.',
    'section.abilities': 'V · Abilità',
    'section.abilities.all': 'Tutte',
    'section.abilities.level': 'Liv.',
    'section.abilities.selected': 'selezionate',
    'section.abilities.empty': 'Nessuna carta con i filtri attivi.',
    'section.name': 'Nome del personaggio',
    'section.name.placeholder': 'Inserisci il nome del personaggio…',
    'section.name.hint': 'Usato come nome del file al salvataggio e download.',

    // Buttons
    'btn.load': 'Carica',
    'btn.reset': 'Reset',
    'btn.save': 'Salva',
    'btn.print': 'Stampa',
    'btn.download': 'Scarica',
    'btn.choose': 'Scegli',

    // Status bar
    'status.empty': 'Nessun personaggio — carica un file o inizia a costruire',
    'status.abilities': 'abilità',

    // Confirm dialogs
    'confirm.reset.title': 'Conferma Reset',
    'confirm.reset.message': 'Tutte le selezioni e i dati del personaggio verranno cancellati. Vuoi continuare?',
    'confirm.reset.yes': 'Conferma',
    'confirm.reset.no': 'Annulla',
    'confirm.leave.title': 'Uscire dalla pagina?',
    'confirm.leave.message': 'Hai delle selezioni non salvate. Se esci perderai tutte le modifiche.',
    'confirm.leave.yes': 'Esci',
    'confirm.leave.no': 'Resta',

    // Card modal
    'modal.prev': 'Carta precedente',
    'modal.next': 'Carta successiva',
    'modal.level': 'Livello',
    'modal.cost': 'Costo',
    'modal.add': '+ Aggiungi al mazzo',
    'modal.added': '✓ Selezionata',

    // Card thumbnail
    'thumb.level': 'Liv',
    'thumb.inspect': 'Ispeziona',

    // Size controls
    'size.bigger': 'Carte più grandi',
    'size.smaller': 'Carte più piccole',
  },

  en: {
    // Header
    'header.schema': 'Schema',

    // Loading / error
    'loading': 'Loading cards…',
    'error.title': 'Loading error',
    'error.hint': 'Run {cmd} and verify the {dir} folder is accessible.',

    // Footer
    'footer': 'Daggerheart © Darrington Press · Unofficial tool',

    // Home
    'home.title': 'Daggerheart',
    'home.subtitle': 'Character Builder',
    'home.desc': 'Unofficial tool to build and manage your Daggerheart character card decks, based on the Italian edition.',
    'home.start': 'Build your Character',
    'home.start.desc': 'Choose your class, select domains, and build your PC\'s card deck.',
    'home.schema': 'View the Schema',
    'home.schema.desc': 'Explore relationships between classes, domains, and subclasses in an interactive graph.',

    // Builder hero
    'builder.hero': 'Forge your destiny. Choose a class to build your character\'s deck.',

    // Sections
    'section.origin': 'I · Origin',
    'section.origin.desc': 'Choose your Origin card (optional).',
    'section.origin.ok': '✓ Selected',
    'section.community': 'II · Community',
    'section.community.desc': 'Choose your Community card (optional).',
    'section.community.ok': '✓ Selected',
    'section.class': 'III · Class',
    'section.class.select': 'Choose your class',
    'section.class.placeholder': '— Select —',
    'section.subclass': 'Choose your subclass',
    'section.subclass.pick': 'Select cards from {name} to include in your deck.',
    'section.domains': 'IV · Domains',
    'section.domains.info': 'The class {name} has access to these two domains:',
    'section.domains.hint': 'The ability cards below come from these two domains.',
    'section.abilities': 'V · Abilities',
    'section.abilities.all': 'All',
    'section.abilities.level': 'Lvl.',
    'section.abilities.selected': 'selected',
    'section.abilities.empty': 'No cards match the active filters.',
    'section.name': 'Character name',
    'section.name.placeholder': 'Enter your character\'s name…',
    'section.name.hint': 'Used as the file name when saving and downloading.',

    // Buttons
    'btn.load': 'Load',
    'btn.reset': 'Reset',
    'btn.save': 'Save',
    'btn.print': 'Print',
    'btn.download': 'Download',
    'btn.choose': 'Choose',

    // Status bar
    'status.empty': 'No character — load a file or start building',
    'status.abilities': 'abilities',

    // Confirm dialogs
    'confirm.reset.title': 'Confirm Reset',
    'confirm.reset.message': 'All selections and character data will be cleared. Continue?',
    'confirm.reset.yes': 'Confirm',
    'confirm.reset.no': 'Cancel',
    'confirm.leave.title': 'Leave page?',
    'confirm.leave.message': 'You have unsaved selections. If you leave you will lose all changes.',
    'confirm.leave.yes': 'Leave',
    'confirm.leave.no': 'Stay',

    // Card modal
    'modal.prev': 'Previous card',
    'modal.next': 'Next card',
    'modal.level': 'Level',
    'modal.cost': 'Cost',
    'modal.add': '+ Add to deck',
    'modal.added': '✓ Selected',

    // Card thumbnail
    'thumb.level': 'Lvl',
    'thumb.inspect': 'Inspect',

    // Size controls
    'size.bigger': 'Larger cards',
    'size.smaller': 'Smaller cards',
  },
}

// TODO: When English card images are available, update the card image base path
// per locale. Currently all cards use Italian images regardless of language.
// Change in: stores/character.ts (loadCards URL), CardThumbnail.vue (imgSrc),
// CardModal.vue (imgSrc) — e.g. `cards/${locale}/` instead of `cards/`

export function useI18n() {
  function t(key: string, params?: Record<string, string>): string {
    let msg = messages[locale.value]?.[key] ?? messages.it[key] ?? key
    if (params) {
      for (const [k, v] of Object.entries(params)) {
        msg = msg.replace(`{${k}}`, v)
      }
    }
    return msg
  }

  function setLocale(l: Locale) {
    locale.value = l
  }

  return { locale, t, setLocale }
}
