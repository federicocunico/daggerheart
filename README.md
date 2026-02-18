# Daggerheart Card Builder

Estrae le 270 carte dal PDF stampabile italiano di Daggerheart e le serve
tramite una SPA Vue 3 per costruire il mazzo del proprio personaggio.

---

## Prerequisiti

| Tool | Versione minima |
|------|----------------|
| [uv](https://docs.astral.sh/uv/getting-started/installation/) | qualsiasi recente |
| Node.js | 20 o 22 |

---

## Avvio locale (sviluppo)

### 1 — Estrai le carte dal PDF

```bash
# Nella root del progetto:
uv run python parse_pdf.py
# → genera cards/ con 270 PNG + JSON + cards/index.json
```

### 2 — Avvia il server di sviluppo

```bash
cd frontend
npm install        # solo la prima volta
npm run dev
```

Apri **http://localhost:5173** nel browser.

> Il dev server serve automaticamente la cartella `../cards/` all'URL `/cards/`
> tramite il plugin Vite personalizzato — non è necessario copiare nulla.

### 3 — Anteprima della build di produzione (opzionale)

```bash
cd frontend
npm run build      # compila + copia cards/ → dist/cards/
npm run preview    # serve dist/ su http://localhost:4173
```

---

## Deploy su GitHub Pages

### Prima configurazione (una sola volta)

1. Vai su **Settings → Pages** del tuo repository
2. In **Source** seleziona **GitHub Actions**
3. Salva

Da questo momento ogni push su `main` / `master` esegue automaticamente
il workflow `.github/workflows/deploy.yml` che:

1. Estrae le carte con `uv run python main.py`
2. Compila il frontend con `npm run build`
3. Pubblica `frontend/dist/` su GitHub Pages

L'URL del sito sarà `https://<user>.github.io/<repo>/`.

> **Nota:** il PDF `sources/carte_stampabili.pdf` deve essere committato
> nel repository per poter essere usato dalla CI.

---

## Struttura del progetto

```
daggerheart/
├── sources/
│   └── carte_stampabili.pdf   ← PDF sorgente (non incluso nel repo)
├── cards/                     ← generato da main.py
│   ├── origine/               18 carte razza
│   ├── comunità/               9 carte comunità
│   ├── domini/
│   │   ├── arcano/
│   │   │   ├── classi/        6 carte classe (base, spec, maestria × 2 classi)
│   │   │   └── abilita/      21 carte abilità/incantesimo
│   │   ├── lama/ osso/ codice/ grazia/ mezzanotte/ saggio/ splendore/ valore/
│   │   └── …
│   └── index.json             manifesto completo per il frontend
├── frontend/                  ← Vue 3 + TypeScript + Tailwind
│   ├── src/
│   ├── dist/                  ← output build (gitignored)
│   └── package.json
├── main.py                    ← script di estrazione carte
└── pyproject.toml
```

---

## Uso dell'app

1. **Scegli la classe** dalla griglia nella home (filtrabile per dominio)
2. Nella tab **Classe** seleziona i tuoi **2 domini** di riferimento
3. Nella tab **Abilità** sfoglia e seleziona le carte — filtra per livello e tipo
4. Usa la barra in basso per:
   - **Salva JSON** — salva lo stato del personaggio (ricaricabile)
   - **Scarica mazzo ZIP** — scarica tutte le carte selezionate come PNG organizzati per dominio
   - **Carica** — riprendi un personaggio salvato precedentemente
