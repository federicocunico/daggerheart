import type { CardIndex } from '@/types/card'

export function usePrint() {
  function printCards(
    originCard: CardIndex | null,
    communityCard: CardIndex | null,
    classCards: CardIndex[],
    abilityCards: CardIndex[],
  ) {
    // Print order: origine → comunità → classi → abilità
    const cards: CardIndex[] = [
      ...(originCard   ? [originCard]   : []),
      ...(communityCard ? [communityCard] : []),
      ...classCards,
      ...abilityCards,
    ]

    if (!cards.length) {
      alert('Nessuna carta selezionata da stampare.')
      return
    }

    // Build absolute base URL for cards (works with hash router + GitHub Pages subdirs)
    const cardsBase =
      window.location.origin +
      window.location.pathname +
      (window.location.pathname.endsWith('/') ? '' : '/') +
      'cards/'

    // Split into pages of 9 cards (3×3 grid on A4)
    const PER_PAGE = 9
    const pages: CardIndex[][] = []
    for (let i = 0; i < cards.length; i += PER_PAGE) {
      pages.push(cards.slice(i, i + PER_PAGE))
    }

    const renderPage = (page: CardIndex[]) => {
      const cells = Array.from({ length: PER_PAGE }, (_, i) => {
        const card = page[i]
        if (!card) return `<div class="cell empty"></div>`
        const src = `${cardsBase}${card.img}`
        return `<div class="cell"><img src="${src}" alt="${card.nome.replace(/"/g, '&quot;')}" /></div>`
      })
      return `<div class="page">${cells.join('')}</div>`
    }

    const html = `<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8" />
  <title>Daggerheart – Stampa</title>
  <style>
    @page { size: A4 portrait; margin: 4mm; }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { background: white; }
    .page {
      width: 202mm;
      height: 289mm;
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      grid-template-rows: repeat(3, 1fr);
      gap: 1.5mm;
      page-break-after: always;
    }
    .page:last-child { page-break-after: avoid; }
    .cell {
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .cell img {
      width: 100%;
      height: 100%;
      object-fit: contain;
      display: block;
    }
    .cell.empty {
      border: 0.5mm dashed #ddd;
      border-radius: 2mm;
    }
  </style>
</head>
<body>
  ${pages.map(renderPage).join('\n')}
</body>
</html>`

    const win = window.open('', '_blank')
    if (!win) {
      alert('Abilita i popup del browser per usare la stampa.')
      return
    }
    win.document.write(html)
    win.document.close()
    // Print after images load
    win.addEventListener('load', () => win.print())
  }

  return { printCards }
}
