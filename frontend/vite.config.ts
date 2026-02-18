import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import { resolve, join } from 'node:path'
import { existsSync, statSync, createReadStream, promises as fsp } from 'node:fs'

// Plugin: serve ../cards/ at /cards/ in dev; copy to dist/cards/ at build time
function cardsPlugin() {
  const cardsRoot = resolve(fileURLToPath(import.meta.url), '../../cards')

  function getContentType(filePath: string): string {
    const ext = filePath.split('.').pop()?.toLowerCase()
    return { png: 'image/png', json: 'application/json' }[ext ?? ''] ?? 'application/octet-stream'
  }

  return {
    name: 'daggerheart-cards',
    configureServer(server: any) {
      server.middlewares.use('/cards', (req: any, res: any, next: any) => {
        const url: string = req.url ?? '/'
        const filePath = join(cardsRoot, decodeURIComponent(url))
        try {
          if (!existsSync(filePath) || !statSync(filePath).isFile()) { next(); return }
        } catch { next(); return }

        res.setHeader('Content-Type', getContentType(filePath))
        res.setHeader('Cache-Control', 'public, max-age=3600')
        createReadStream(filePath).pipe(res)
      })
    },
    async closeBundle() {
      if (!existsSync(cardsRoot)) return
      const dest = resolve(fileURLToPath(import.meta.url), '../dist/cards')
      console.log('\nCopying cards/ → dist/cards/ …')
      await fsp.cp(cardsRoot, dest, { recursive: true })
      console.log('Cards copied.')
    },
  }
}

export default defineConfig({
  plugins: [
    vue(),
    tailwindcss(),
    cardsPlugin(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  // './' = relative paths, works for local preview.
  // GitHub Actions overrides this via --base flag with the correct Pages path.
  base: process.env.VITE_BASE_URL ?? './',
  server: {
    host: '127.0.0.1',   // explicit IPv4 — fixes "unable to connect" on Windows
    port: 5173,
    fs: { allow: ['..'] },
  },
})
