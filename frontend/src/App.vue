<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCharacterStore } from '@/stores/character'
import { DOMAIN_META } from '@/types/card'

const route  = useRoute()
const router = useRouter()
const store  = useCharacterStore()

onMounted(() => store.loadCards())
</script>

<template>
  <div class="min-h-screen flex flex-col">

    <!-- ── Header ─────────────────────────────────────────────────────────── -->
    <header class="sticky top-0 z-40 border-b border-[var(--border)] bg-[var(--bg-panel)]/95 backdrop-blur-sm">
      <div class="max-w-5xl mx-auto px-4 sm:px-6 h-14 flex items-center gap-3">

        <!-- Logo / builder link -->
        <router-link
          to="/"
          class="flex items-center gap-2 flex-shrink-0 hover:opacity-80 transition-opacity"
        >
          <span class="text-[var(--gold)]" style="font-size:1.1rem">✦</span>
          <span
            class="font-bold text-[var(--gold)] uppercase tracking-[0.18em] text-sm"
            style="font-family: 'Cinzel', serif"
          >
            Daggerheart
          </span>
        </router-link>

        <!-- Nav: Schema button -->
        <router-link
          to="/schema"
          class="ml-1 flex-shrink-0"
          title="Visualizzazione a grafico"
        >
          <span
            :class="[
              'text-xs uppercase tracking-[0.12em] px-2.5 py-1 rounded border transition-all',
              route.name === 'schema'
                ? 'border-[var(--gold)] text-[var(--gold)] bg-[var(--gold-glow)]'
                : 'border-[var(--border)] text-[var(--text-dim)] hover:border-[var(--gold-dim)] hover:text-[var(--text)]',
            ]"
            style="font-family:'Cinzel',serif"
          >
            Schema
          </span>
        </router-link>

        <!-- Spacer -->
        <div class="flex-1" />

        <!-- Character status (compact) -->
        <div
          v-if="store.className"
          class="flex items-center gap-2 text-xs text-[var(--text-dim)] overflow-hidden"
        >
          <span
            class="text-[var(--gold)] font-semibold truncate hidden sm:inline"
            style="font-family: 'Cinzel', serif"
          >{{ store.className }}</span>
          <template v-for="d in store.selectedDomains" :key="d">
            <span class="text-[var(--text-dim)] hidden sm:inline">·</span>
            <span
              class="hidden sm:inline"
              :style="`color: ${DOMAIN_META[d].hex}`"
            >{{ DOMAIN_META[d].icon }}</span>
          </template>
          <template v-if="store.selectedAbilities.size">
            <span class="text-[var(--text-dim)]">·</span>
            <span class="text-[var(--gold)]">{{ store.selectedAbilities.size }}</span>
            <span class="hidden sm:inline">abilità</span>
          </template>
        </div>
      </div>
    </header>

    <!-- ── Loading overlay ────────────────────────────────────────────────── -->
    <div
      v-if="store.loading"
      class="fixed inset-0 bg-[var(--bg)]/85 z-50 flex items-center justify-center"
    >
      <div class="text-center space-y-4">
        <div
          class="text-[var(--gold)] text-4xl animate-spin inline-block"
          style="animation-timing-function: linear"
        >✦</div>
        <p
          class="text-[var(--gold)] uppercase tracking-[0.25em] text-xs"
          style="font-family: 'Cinzel', serif"
        >Caricamento carte…</p>
      </div>
    </div>

    <!-- ── Error state ────────────────────────────────────────────────────── -->
    <div
      v-else-if="store.error"
      class="flex-1 flex items-center justify-center p-8"
    >
      <div class="panel-gold p-8 max-w-md text-center space-y-4">
        <p
          class="text-red-400 uppercase tracking-widest text-sm"
          style="font-family: 'Cinzel', serif"
        >Errore nel caricamento</p>
        <p class="text-[var(--text-dim)] text-sm">{{ store.error }}</p>
        <p class="text-[var(--text-dim)] text-xs">
          Esegui <code class="text-[var(--gold)]">uv run python main.py</code>
          e verifica che la cartella <code class="text-[var(--gold)]">cards/</code> sia accessibile.
        </p>
      </div>
    </div>

    <!-- ── Main content ───────────────────────────────────────────────────── -->
    <main v-else class="flex-1">
      <router-view />
    </main>

    <!-- ── Footer ─────────────────────────────────────────────────────────── -->
    <footer
      class="border-t border-[var(--border)] py-3 text-center text-[var(--text-dim)] text-xs"
      style="font-family: 'Cinzel', serif; letter-spacing: 0.12em"
    >
      Daggerheart © Darrington Press · Interfaccia non ufficiale
    </footer>
  </div>
</template>
