<script setup lang="ts">
/** Spectator view of the current race (classic "Current" page). */
import { currentStatusMessage } from '~/utils/winner'

const rh = useRH()
const { t } = useI18n()
const audio = useAudio()
const route = useRoute()
const router = useRouter()
const { info } = useServerInfo()
const logoUrl = useRuntimeConfig().app.baseURL + 'rh-icon.svg'
rh.load(['race_status', 'current_heat', 'current_laps', 'leaderboard', 'frequency_data', 'pilot_data', 'min_lap', 'format_data', 'seat_data'])

const S = rh.state
const status = computed<number>(() => S.race_status?.race_status ?? 0)
const loaded = computed(() => !!(S.race_status && S.leaderboard && S.current_heat))
const heatNodes = computed(() => S.current_heat?.heatNodes || {})
const seats = computed(() => Object.keys(heatNodes.value).map(Number).filter(i => heatNodes.value[i]?.pilot_id || S.current_heat?.current_heat == null))
const seatColors = computed(() => Object.fromEntries(Object.keys(heatNodes.value).map(i => [Number(i), colorHex(heatNodes.value[i]?.activeColor)])))

// between races the server also sends the previous race ('last_race'); show it until the next one starts
const showLast = computed(() => status.value === RACE_STATUS.READY && !!S.leaderboard?.last_race)
const lb = computed(() => (showLast.value ? S.leaderboard?.last_race : S.leaderboard?.current) || {})
const laps = computed<any[]>(() => ((showLast.value ? S.current_laps?.last_race : S.current_laps?.current) || {}).node_index || [])
const rowsByNode = computed(() => {
  const m: Record<number, any> = {}
  for (const r of lb.value?.leaderboard?.by_race_time || []) m[r.node] = r
  return m
})
// seats shown: the current heat's lineup, or the last race's own pilots between races
// (the current heat has usually advanced to the next heat by then)
const seatColorByIndex = computed<Record<number, string>>(() => Object.fromEntries((S.seat_data?.seats || []).map((s: any) => [s.seat_id, s.color])))
const shownSeats = computed(() => {
  if (!showLast.value) return seats.value.map(i => ({ seat: i, node: heatNodes.value[i] }))
  return laps.value
    .map((l: any, i: number) => ({ l, i }))
    .filter(({ l }) => l?.pilot || l?.laps?.length)
    .map(({ l, i }) => ({ seat: i, node: { callsign: l.pilot?.callsign, pilot_id: l.pilot?.id, activeColor: seatColorByIndex.value[i] } }))
})
const statusMessage = computed(() => currentStatusMessage(lb.value))
const minLapMs = computed(() => (S.min_lap?.min_lap || 0) * 1000)
const nextHeat = computed(() => S.leaderboard?.current?.displayname)
const nextRound = computed(() => S.current_heat?.next_round)
// the card names what it shows: the race being run, a finished one awaiting save, or the heat about to run
const heroLabel = computed(() => showLast.value
  ? t('Last race')
  : status.value === RACE_STATUS.RACING || status.value === RACE_STATUS.STAGING
    ? t('Now racing')
    : status.value === RACE_STATUS.DONE ? t('Finished') : t('Up next'))

// ---- presentation mode (?kiosk=1): no app chrome, type scaled up with the screen ----
const kiosk = useKiosk()
const zoom = ref(1)
const fullscreen = ref(false)
const canFullscreen = ref(false)
// the controls fade out while the pointer rests, and come back when it moves
const idle = ref(false)
let idleTimer: ReturnType<typeof setTimeout> | undefined
function wake() {
  idle.value = false
  clearTimeout(idleTimer)
  idleTimer = setTimeout(() => { idle.value = true }, 3000)
}
const fit = () => { zoom.value = Math.min(2.4, Math.max(1.1, window.innerWidth / 1350)) }
const onFullscreen = () => { fullscreen.value = !!document.fullscreenElement }
function toggleFullscreen() {
  if (document.fullscreenElement) document.exitFullscreen().catch(() => {})
  else document.documentElement.requestFullscreen?.().catch(() => {})
}
function present() {
  // asked for in the click itself: browsers allow full screen only in answer to one
  if (canFullscreen.value && !document.fullscreenElement) document.documentElement.requestFullscreen?.().catch(() => {})
  router.push({ query: { ...route.query, kiosk: '1' } })
}
function exitKiosk() {
  if (document.fullscreenElement) document.exitFullscreen().catch(() => {})
  router.replace({ query: { ...route.query, kiosk: undefined } })
}
function onKioskKey(e: KeyboardEvent) {
  wake()
  if (!kiosk.value || e.target instanceof HTMLInputElement) return
  if (e.key === 'Escape' && !document.fullscreenElement && !document.querySelector('[role="dialog"]')) exitKiosk()
  else if (e.key.toLowerCase() === 'f' && !e.ctrlKey && !e.metaKey && !e.altKey) toggleFullscreen()
}
onMounted(() => {
  canFullscreen.value = !!document.fullscreenEnabled
  onFullscreen()
  fit()
  wake()
  window.addEventListener('resize', fit)
  window.addEventListener('pointermove', wake, { passive: true })
  window.addEventListener('keydown', onKioskKey)
  document.addEventListener('fullscreenchange', onFullscreen)
})
onBeforeUnmount(() => {
  clearTimeout(idleTimer)
  window.removeEventListener('resize', fit)
  window.removeEventListener('pointermove', wake)
  window.removeEventListener('keydown', onKioskKey)
  document.removeEventListener('fullscreenchange', onFullscreen)
})
const kioskZoom = computed(() => (kiosk.value ? { zoom: zoom.value } : undefined))
</script>

<template>
  <UDashboardPanel id="live" :class="kiosk && idle ? 'cursor-none' : ''">
    <template #header>
      <!-- presentation mode: the event's name, and controls that fade out while the pointer rests -->
      <div v-if="kiosk" class="flex shrink-0 items-center gap-3 px-4 py-3 sm:px-6" :style="kioskZoom">
        <img :src="logoUrl" alt="" class="size-7 shrink-0">
        <span class="min-w-0 truncate font-display text-lg font-semibold text-highlighted">{{ info?.event?.name || 'RotorHazard' }}</span>
        <div class="ms-auto flex items-center gap-1 transition-opacity duration-500 focus-within:opacity-100" :class="idle ? 'opacity-0' : 'opacity-100'">
          <RhAudioToggle />
          <UTooltip v-if="canFullscreen" :text="fullscreen ? t('Exit full screen') : t('Full screen')" :kbds="['F']">
            <UButton
              color="neutral"
              variant="ghost"
              :icon="fullscreen ? 'i-lucide-minimize' : 'i-lucide-maximize'"
              :aria-label="fullscreen ? t('Exit full screen') : t('Full screen')"
              @click="toggleFullscreen"
            />
          </UTooltip>
          <UTooltip :text="t('Exit presentation mode')" :kbds="['Esc']">
            <UButton color="neutral" variant="ghost" icon="i-lucide-x" :aria-label="t('Exit presentation mode')" @click="exitKiosk" />
          </UTooltip>
        </div>
      </div>
      <UDashboardNavbar v-else :title="t('Live')">
        <template #right>
          <RhBell />
          <RhAudioToggle />
          <UTooltip :text="t('Presentation mode: full screen, for a projector or TV')">
            <UButton
              color="neutral"
              variant="ghost"
              icon="i-lucide-presentation"
              :aria-label="t('Presentation mode')"
              :label="t('Present')"
              :ui="{ label: 'hidden sm:inline' }"
              @click="present"
            />
          </UTooltip>
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div v-if="!loaded" class="mx-auto w-full max-w-6xl space-y-6" aria-busy="true" :style="kioskZoom">
        <USkeleton class="h-48 w-full rounded-3xl" />
        <USkeleton class="h-64 w-full rounded-2xl" />
      </div>
      <div v-else class="mx-auto w-full max-w-6xl space-y-6" :style="kioskZoom">
        <!-- between races: a compact header for the last race; during one: the big clock -->
        <section
          class="flex flex-col items-center gap-2 rounded-3xl bg-default px-6 text-center ring-1 ring-default"
          :class="showLast ? 'py-5' : 'py-8 sm:py-10'"
        >
          <div class="text-sm font-medium text-muted">
            {{ heroLabel }}<template v-if="showLast && lb.round"> · {{ t('Round') }} {{ lb.round }}</template>
          </div>
          <h1 class="text-balance font-display font-semibold text-highlighted" :class="showLast ? 'text-2xl' : 'text-3xl sm:text-4xl'">
            {{ lb.displayname || t('Practice') }}
          </h1>
          <div v-if="lb.round && !showLast" class="text-sm font-medium text-muted">
            {{ t('Round') }} {{ lb.round }}
          </div>
          <!-- between races this card shows the last race's result, not the next race's clock -->
          <RhRaceClock v-if="!showLast" class="mt-4" />
          <div v-if="statusMessage" class="mt-3 rounded-full bg-elevated px-4 py-1.5 text-sm font-medium">
            {{ statusMessage }}
          </div>
        </section>

        <UAlert
          v-if="showLast && nextHeat"
          icon="i-lucide-arrow-right-circle"
          color="neutral"
          variant="subtle"
          :title="`${t('Up next')}: ${nextHeat}${nextRound ? ` · ${t('Round')} ${nextRound}` : ''}`"
          :description="Object.values(heatNodes).map((n: any) => n.callsign).filter(Boolean).join(' · ')"
        />

        <UCard :ui="{ body: 'p-0 sm:p-0' }">
          <RhLeaderboard :board="lb.leaderboard" kind="current" :seat-colors="seatColors" :min-lap-ms="minLapMs" top-speed />
        </UCard>
        <UCard v-if="lb.team_leaderboard" :ui="{ body: 'p-0 sm:p-0' }">
          <RhTeamLeaderboard :board="lb.team_leaderboard" />
        </UCard>

        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <RhSeatCard
            v-for="s in shownSeats"
            :key="s.seat"
            :seat="s.seat"
            :node="s.node"
            :freq="S.frequency_data?.fdata?.[s.seat]"
            :laps="(laps[s.seat]?.laps || []).filter((l: any) => !l.late_lap)"
            :fastest-index="laps[s.seat]?.fastest_lap_index"
            :finished="laps[s.seat]?.finished_flag"
            :row="rowsByNode[s.seat]"
            :rssi="S.heartbeat?.current_rssi?.[s.seat]"
            :crossing="S.heartbeat?.crossing_flag?.[s.seat]"
            :min-lap-ms="minLapMs"
            :show-signal="false"
          />
        </div>

        <p v-if="!audio.unlocked.value && audio.settings.enabled" class="text-center text-sm text-muted">
          {{ t('Tap anywhere to hear race callouts on this device.') }}
        </p>
      </div>
    </template>
  </UDashboardPanel>
</template>
