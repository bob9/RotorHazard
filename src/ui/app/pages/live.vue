<script setup lang="ts">
/** Spectator view of the current race (classic "Current" page). */
const rh = useRH()
const { t } = useI18n()
const audio = useAudio()
rh.load(['race_status', 'current_heat', 'current_laps', 'leaderboard', 'frequency_data', 'pilot_data', 'min_lap', 'format_data'])

const S = rh.state
const status = computed<number>(() => S.race_status?.race_status ?? 0)
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
const minLapMs = computed(() => (S.min_lap?.min_lap || 0) * 1000)
const nextHeat = computed(() => S.leaderboard?.current?.displayname)
const nextRound = computed(() => S.current_heat?.next_round)
</script>

<template>
  <UDashboardPanel id="live">
    <template #header>
      <UDashboardNavbar :title="t('Live')">
        <template #right>
          <RhAudioToggle />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div class="mx-auto w-full max-w-6xl space-y-6">
        <section class="flex flex-col items-center gap-2 rounded-3xl bg-default px-6 py-8 text-center ring-1 ring-default sm:py-10">
          <div class="text-sm font-medium text-muted">
            {{ showLast ? t('Last race') : t('Now racing') }}
          </div>
          <h1 class="text-balance font-display text-3xl font-semibold text-highlighted sm:text-4xl">
            {{ lb.displayname || t('Practice') }}
          </h1>
          <div v-if="lb.round" class="text-sm font-medium text-muted">
            {{ t('Round') }} {{ lb.round }}
          </div>
          <RhRaceClock class="mt-4" />
          <div v-if="lb.status_msg" class="mt-3 rounded-full bg-elevated px-4 py-1.5 text-sm font-medium">
            {{ lb.status_msg }}
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
            v-for="i in seats"
            :key="i"
            :seat="i"
            :node="heatNodes[i]"
            :freq="S.frequency_data?.fdata?.[i]"
            :laps="(laps[i]?.laps || []).filter((l: any) => !l.late_lap)"
            :fastest-index="laps[i]?.fastest_lap_index"
            :finished="laps[i]?.finished_flag"
            :row="rowsByNode[i]"
            :rssi="S.heartbeat?.current_rssi?.[i]"
            :crossing="S.heartbeat?.crossing_flag?.[i]"
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
