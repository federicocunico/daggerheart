import JSZip from 'jszip'
import type { CardIndex, CharacterSave } from '@/types/card'

export function useDownload(baseUrl: string = '') {
  async function fetchBlob(url: string): Promise<Blob> {
    const res = await fetch(url)
    if (!res.ok) throw new Error(`Failed to fetch ${url}`)
    return res.blob()
  }

  async function downloadSet(
    save: CharacterSave,
    classCards: CardIndex[],
    abilities: CardIndex[],
  ) {
    const zip = new JSZip()

    // Character metadata
    zip.file('personaggio.json', JSON.stringify(save, null, 2))

    // Class cards
    const classFolder = zip.folder('classi')!
    for (const card of classCards) {
      const name = card.img.split('/').pop()!
      const blob = await fetchBlob(`${baseUrl}cards/${card.img}`)
      classFolder.file(name, blob)
    }

    // Selected ability cards, grouped by domain
    for (const card of abilities) {
      const folder = zip.folder(`abilita/${card.dominio ?? 'altro'}`)!
      const name = card.img.split('/').pop()!
      const blob = await fetchBlob(`${baseUrl}cards/${card.img}`)
      folder.file(name, blob)
    }

    const blob = await zip.generateAsync({ type: 'blob' })
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href     = url
    a.download = `daggerheart_${save.className.toLowerCase().replace(/\s+/g, '_')}.zip`
    a.click()
    URL.revokeObjectURL(url)
  }

  function downloadSave(save: CharacterSave) {
    const blob = new Blob([JSON.stringify(save, null, 2)], { type: 'application/json' })
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href     = url
    a.download = `daggerheart_${save.className.toLowerCase().replace(/\s+/g, '_')}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  function loadSave(file: File): Promise<CharacterSave> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = e => {
        try {
          resolve(JSON.parse(e.target!.result as string))
        } catch {
          reject(new Error('File JSON non valido'))
        }
      }
      reader.onerror = () => reject(new Error('Errore lettura file'))
      reader.readAsText(file)
    })
  }

  return { downloadSet, downloadSave, loadSave }
}
