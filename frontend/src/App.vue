<script setup lang="ts">
import { onMounted } from 'vue'
import { useCharacterStore } from '@/stores/character'

const store = useCharacterStore()
// Pre-load card index on app start
onMounted(() => store.loadCards())
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <!-- Header -->
    <header class="sticky top-0 z-40 border-b border-stone-800 bg-stone-950/90 backdrop-blur">
      <div class="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
        <router-link to="/" class="flex items-center gap-2 hover:opacity-80 transition-opacity">
          <span class="text-yellow-500 text-xl">⚔️</span>
          <span class="font-bold text-stone-100 tracking-widest uppercase text-sm">
            Daggerheart Builder
          </span>
        </router-link>
        <div class="flex items-center gap-3 text-xs text-stone-500">
          <span v-if="store.className" class="text-yellow-500 font-bold">
            {{ store.className }}
          </span>
          <span v-if="store.selectedDomains.length">
            · {{ store.selectedDomains.join(', ') }}
          </span>
          <span v-if="store.selectedAbilities.size">
            · {{ store.selectedAbilities.size }} abilità scelte
          </span>
        </div>
      </div>
    </header>

    <!-- Loading overlay -->
    <div v-if="store.loading" class="fixed inset-0 bg-stone-950/80 z-50 flex items-center justify-center">
      <div class="text-center space-y-3">
        <div class="text-4xl animate-spin inline-block">⚔️</div>
        <p class="text-stone-400">Caricamento carte…</p>
      </div>
    </div>

    <!-- Error state -->
    <div v-else-if="store.error" class="flex-1 flex items-center justify-center p-8">
      <div class="glass rounded-xl p-6 max-w-md text-center space-y-3">
        <p class="text-red-400 font-bold">Errore nel caricamento</p>
        <p class="text-stone-400 text-sm">{{ store.error }}</p>
        <p class="text-stone-500 text-xs">
          Assicurati di aver eseguito <code class="text-yellow-400">uv run python main.py</code>
          e che la cartella <code class="text-yellow-400">cards/</code> sia accessibile.
        </p>
      </div>
    </div>

    <!-- Main content -->
    <main v-else class="flex-1">
      <router-view />
    </main>

    <!-- Footer -->
    <footer class="border-t border-stone-800 py-3 text-center text-stone-600 text-xs">
      Daggerheart © Darrington Press 2025 · Interfaccia non ufficiale
    </footer>
  </div>
</template>
