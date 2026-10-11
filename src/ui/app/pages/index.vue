<script setup lang="ts">
const rh = useRH()
const { t } = useI18n()
const { admin, hasCredentials } = useAuth()
const { info } = useServerInfo()
const audio = useAudio()
const toast = useToast()

rh.load([
  'race_status', 'current_heat', 'current_laps', 'leaderboard', 'frequency_data', 'heat_data', 'class_data',
  'format_data', 'pilot_data', 'node_data', 'enter_and_exit_at_levels', 'min_lap', 'callouts', 'node_tuning'
])

// guests can't run races: send them to the spectator view once sign-in status is known.
// A device with saved credentials that failed the check (wrong password, or the
// timer briefly unreachable) gets the sign-in prompt instead of being sent away.
const guest = computed(() => admin.value === false && !hasCredentials())
watch(guest, (g) => {
  if (g) navigateTo('/live', { replace: true })
}, { immediate: true })

const S = rh.state
const status = computed<number>(() => S.race_status?.race_status ?? 0)
const isReady = computed(() => status.value === RACE_STATUS.READY)
const isLive = computed(() => status.value === RACE_STATUS.RACING || status.value === RACE_STATUS.STAGING)
const isRacing = computed(() => status.value === RACE_STATUS.RACING)
const isDone = computed(() => status.value === RACE_STATUS.DONE)

const numNodes = computed(() => info.value?.num_nodes ?? S.frequency_data?.fdata?.length ?? 0)
const heatNodes = computed(() => S.current_heat?.heatNodes || {})
// like the classic Run page, show only seats with a frequency (or a pilot in this heat)
const seats = computed(() => Array.from({ length: numNodes.value }, (_, i) => i)
  .filter(i => S.frequency_data?.fdata?.[i]?.frequency || heatNodes.value[i]?.pilot_id))
const seatColors = computed(() => Object.fromEntries(seats.value.map(i => [i, colorHex(heatNodes.value[i]?.activeColor)])))
const lapsBySeat = computed<any[]>(() => S.current_laps?.current?.node_index || [])
const board = computed(() => S.leaderboard?.current?.leaderboard)
const teamBoard = computed(() => S.leaderboard?.current?.team_leaderboard)
const rowsByNode = computed(() => {
  const m: Record<number, any> = {}
  for (const r of board.value?.by_race_time || []) m[r.node] = r
  return m
})
const minLapMs = computed(() => (S.min_lap?.min_lap || 0) * 1000)
const anyLaps = computed(() => lapsBySeat.value.some(s => s?.laps?.length))

// heat / format
const heats = computed<any[]>(() => S.heat_data?.heats || [])
const classes = computed<any[]>(() => S.class_data?.classes || [])
const formats = computed<any[]>(() => S.format_data?.formats || [])
const currentHeatId = computed<number | null>(() => S.current_heat?.current_heat ?? null)
const currentHeat = computed(() => heats.value.find(h => h.id === currentHeatId.value))
const currentClass = computed(() => classes.value.find(c => c.id === currentHeat.value?.class_id))
const currentFormat = computed(() => formats.value.find(f => f.id === S.race_status?.race_format_id))
const heatName = computed(() => S.leaderboard?.current?.displayname || currentHeat.value?.displayname || t('Practice'))
const round = computed(() => S.current_heat?.next_round || S.race_status?.next_round)

const heatItems = computed(() => {
  const groups: any[] = [[{ label: t('Practice Mode'), value: 0, icon: 'i-lucide-dumbbell', description: t('Races are not saved') }]]
  const active = heats.value.filter(h => h.active !== false)
  const byClass = new Map<number | null, any[]>()
  for (const h of active) {
    const k = h.class_id ?? null
    if (!byClass.has(k)) byClass.set(k, [])
    byClass.get(k)!.push(h)
  }
  const ordered = [...classes.value.map(c => c.id), null]
  for (const cid of ordered) {
    const hs = byClass.get(cid)
    if (!hs?.length) continue
    const cls = classes.value.find(c => c.id === cid)
    groups.push([
      { type: 'label', label: cls ? cls.displayname : t('Unclassified') },
      ...hs.map(h => ({ label: h.displayname, value: h.id, description: [heatStatus(h), heatPilots(h)].filter(Boolean).join(' · ') }))
    ])
  }
  return groups
})
function heatStatus(h: any) {
  // in heat data, next_round holds the highest saved round (rounds raced so far)
  const raced = Math.max(0, Number(h.next_round) || 0)
  return raced ? `${raced} ${raced === 1 ? t('round raced') : t('rounds raced')}` : t('Not raced')
}
function heatPilots(h: any) {
  const pilots = S.pilot_data?.pilots || []
  return (h.slots || []).map((s: any) => pilots.find((p: any) => p.pilot_id === s.pilot_id)?.callsign).filter(Boolean).join(', ')
}
const selectedHeat = computed({
  get: () => currentHeatId.value ?? 0,
  set: (v: number) => rh.emit('set_current_heat', { heat: v || null })
})
// formats grouped by racing mode, like the heat picker groups heats by class
const formatItems = computed<any[]>(() => {
  const modes = [
    { mode: 0, label: t('Individual') },
    { mode: 1, label: t('Team') },
    { mode: 2, label: t('Co-op') }
  ]
  return modes
    .map(m => {
      const fs = formats.value.filter(f => (f.team_racing_mode || 0) === m.mode)
      return fs.length ? [{ type: 'label' as const, label: m.label }, ...fs.map(f => ({ label: t(f.name), value: f.id }))] : []
    })
    .filter(g => g.length)
})
const selectedFormat = computed({
  get: () => S.race_status?.race_format_id ?? undefined,
  set: (v: number) => rh.emit('set_race_format', { race_format: v })
})
const formatLocked = computed(() => !!S.current_heat?.heat_format)

// heat navigation: previous/next heat in the list
const flatHeats = computed(() => heatItems.value.flat().filter((i: any) => i.value !== undefined && i.type !== 'label'))
function stepHeat(dir: number) {
  const idx = flatHeats.value.findIndex((i: any) => i.value === (currentHeatId.value ?? 0))
  const next = flatHeats.value[idx + dir] as any
  if (next) selectedHeat.value = next.value
}

// actions
const discardOpen = ref(false)
// spinner until the race status changes, or 3s if the start was refused (the server
// explains why with a priority message)
const busy = ref(false)
let busyTimer: ReturnType<typeof setTimeout> | undefined
function start() {
  audio.unlock()
  busy.value = true
  clearTimeout(busyTimer)
  busyTimer = setTimeout(() => { busy.value = false }, 3000)
  rh.emit('stage_race')
}
watch(status, () => {
  busy.value = false
  clearTimeout(busyTimer)
})
onBeforeUnmount(() => clearTimeout(busyTimer))
function stop() {
  rh.emit('stop_race')
}
function save() {
  rh.emit('save_laps')
}
// confirm from the server's own notice rather than on click
rh.on('race_saved', (d: any) => {
  const heat = heats.value.find(h => h.id === d?.heat_id)
  toast.add({ title: t('Race saved'), description: heat?.displayname, icon: 'i-lucide-check-circle', color: 'success' })
})
function discard() {
  rh.emit('discard_laps')
  discardOpen.value = false
}
function manualLap(seat: number) {
  audio.manualLapBeep()
  rh.emit('simulate_lap', { node: seat })
}

// heat plan (dynamic heats need confirmation before racing)
const plan = ref<any>(null)
rh.on('heat_plan_result', (d: any) => { plan.value = d })

// tuning while ready/racing; after the race stops the same tap opens lap correction
const tuneSeat = ref<number | null>(null)
const marshal = ref<any>(null)
const marshalSeat = ref<number | null>(null)
rh.on('current_marshal_data', (d: any) => { marshal.value = d })
watch(isDone, (d) => {
  if (d) rh.emit('current_race_marshal')
  else {
    marshal.value = null
    marshalSeat.value = null
  }
}, { immediate: true })
const marshalData = computed(() => marshalSeat.value === null ? null : marshal.value?.seats?.[marshalSeat.value] ?? null)
function openSeat(i: number) {
  if (isDone.value && marshal.value?.seats?.[i]) marshalSeat.value = i
  else tuneSeat.value = i
}
function commitMarshal(c: any) {
  rh.emit('replace_current_laps', { seat: marshalSeat.value, ...c })
  rh.emit('current_race_marshal')
  marshalSeat.value = null
}

// hotkeys (classic: z start, x stop, c save, v discard, space = primary action, alt+n manual lap)
function onKey(e: KeyboardEvent) {
  const el = e.target as HTMLElement
  if (!admin.value || el?.closest('input, textarea, [contenteditable], [role="dialog"], [role="listbox"]')) return
  const k = e.key.toLowerCase()
  if (e.altKey && !e.ctrlKey && /^[1-8]$/.test(e.key)) {
    if (isRacing.value) manualLap(Number(e.key) - 1)
    e.preventDefault()
    return
  }
  if (e.ctrlKey || e.metaKey || e.altKey) return
  if (k === ' ') {
    e.preventDefault()
    if (isReady.value) start()
    else if (isLive.value) stop()
    else if (isDone.value) save()
  } else if (k === 'z' && isReady.value) start()
  else if (k === 'x' && isLive.value) stop()
  else if (k === 'c' && (isDone.value || isRacing.value)) save()
  else if (k === 'v' && isDone.value) discardOpen.value = true
}
onMounted(() => window.addEventListener('keydown', onKey))
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))
</script>

<template>
  <UDashboardPanel id="race" :ui="{ body: 'p-0 sm:p-0' }">
    <template #header>
      <UDashboardNavbar :title="t('Race')">
        <template #right>
          <RhAudioToggle />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <!-- guests are redirected to /live (see the guest watcher) -->
      <div v-if="guest" />
      <div v-else-if="admin === false" class="p-6">
        <UEmpty icon="i-lucide-lock-keyhole" :title="t('Sign in to run races')" :description="t('Race control is available to the event admin.')" :actions="[{ label: t('Watch live'), to: '/live' }]" />
      </div>
      <div v-else class="mx-auto w-full max-w-[1600px] space-y-6 p-4 sm:p-6">
        <!-- Race control -->
        <section class="relative overflow-hidden rounded-3xl bg-default ring-1 ring-default shadow-sm">
          <RhArt name="race-hero" class="pointer-events-none absolute inset-0 hidden size-full object-cover dark:block dark:opacity-40" />
          <div class="pointer-events-none absolute inset-0 bg-gradient-to-br from-primary/[0.06] via-transparent to-transparent" />
          <div class="relative grid grid-cols-1 items-center gap-6 p-5 sm:p-8 lg:grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)]">
            <!-- heat -->
            <div class="min-w-0 space-y-3">
              <div class="flex items-center gap-1">
                <UButton icon="i-lucide-chevron-left" color="neutral" variant="ghost" size="sm" :disabled="!isReady" :aria-label="t('Previous heat')" @click="stepHeat(-1)" />
                <USelectMenu
                  v-model="selectedHeat"
                  :items="heatItems"
                  value-key="value"
                  :disabled="!isReady"
                  :search-input="{ placeholder: t('Find a heat…') }"
                  variant="none"
                  class="min-w-0"
                  :ui="{ base: 'px-1 py-0', content: 'min-w-80' }"
                >
                  <template #default>
                    <div class="min-w-0 text-left">
                      <div class="truncate font-display text-2xl font-semibold text-highlighted sm:text-3xl">
                        {{ heatName }}
                      </div>
                    </div>
                  </template>
                </USelectMenu>
                <UButton icon="i-lucide-chevron-right" color="neutral" variant="ghost" size="sm" :disabled="!isReady" :aria-label="t('Next heat')" @click="stepHeat(1)" />
              </div>
              <div class="flex flex-wrap items-center gap-2 pl-2">
                <UBadge v-if="currentClass" :label="currentClass.displayname" color="neutral" variant="subtle" />
                <UBadge v-if="currentHeatId && round" :label="`${t('Round')} ${round}`" color="neutral" variant="subtle" />
                <UBadge v-if="!currentHeatId" :label="t('Practice: races are not saved')" color="warning" variant="subtle" icon="i-lucide-info" />
                <USelectMenu
                  v-model="selectedFormat"
                  :items="formatItems"
                  value-key="value"
                  :disabled="!isReady || formatLocked"
                  size="sm"
                  variant="soft"
                  icon="i-lucide-timer"
                  :search-input="{ placeholder: t('Find a format…') }"
                  :placeholder="t('External format')"
                  :ui="{ content: 'min-w-72' }"
                />
              </div>
            </div>

            <!-- clock -->
            <RhRaceClock />

            <!-- actions (below lg they live in the sticky bar at the bottom) -->
            <div class="hidden flex-col items-stretch gap-2 lg:flex lg:items-end">
              <Transition name="rh" mode="out-in">
                <UButton
                  v-if="isReady"
                  key="start"
                  size="xl"
                  icon="i-lucide-play"
                  :label="t('Start Race')"
                  :loading="busy"
                  class="justify-center rounded-full px-8 lg:min-w-52"
                  @click="start"
                />
                <UButton
                  v-else-if="isLive"
                  key="stop"
                  size="xl"
                  color="error"
                  icon="i-lucide-square"
                  :label="t('Stop Race')"
                  class="justify-center rounded-full px-8 lg:min-w-52"
                  @click="stop"
                />
                <UButton
                  v-else
                  key="save"
                  size="xl"
                  color="success"
                  icon="i-lucide-check"
                  :label="currentHeatId ? t('Save Results') : t('Clear Laps')"
                  class="justify-center rounded-full px-8 lg:min-w-52"
                  @click="save"
                />
              </Transition>
              <div class="flex justify-center gap-1 lg:justify-end">
                <UButton
                  v-if="isDone"
                  color="neutral"
                  variant="ghost"
                  size="sm"
                  icon="i-lucide-trash-2"
                  :label="t('Discard')"
                  @click="discardOpen = true"
                />
                <UButton
                  v-if="isDone && !anyLaps"
                  color="neutral"
                  variant="ghost"
                  size="sm"
                  icon="i-lucide-rotate-ccw"
                  :label="t('Restart')"
                  @click="start"
                />
                <UButton
                  v-if="isRacing"
                  color="neutral"
                  variant="ghost"
                  size="sm"
                  icon="i-lucide-save"
                  :label="t('Stop and Save')"
                  @click="save"
                />
              </div>
              <div class="hidden text-center text-xs text-dimmed lg:block lg:text-right">
                <UKbd value="space" size="sm" /> {{ isReady ? t('to start') : isLive ? t('to stop') : t('to save') }}
              </div>
            </div>
          </div>
          <div v-if="S.leaderboard?.current?.status_msg" class="relative border-t border-default bg-elevated/50 px-6 py-2.5 text-center text-sm font-medium text-highlighted">
            {{ S.leaderboard.current.status_msg }}
          </div>
        </section>

        <!-- seats + leaderboard -->
        <div class="grid grid-cols-1 gap-6 2xl:grid-cols-[minmax(0,1fr)_440px]">
          <div class="grid min-w-0 grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <RhSeatCard
              v-for="i in seats"
              :key="i"
              :seat="i"
              :node="heatNodes[i]"
              :freq="S.frequency_data?.fdata?.[i]"
              :laps="lapsBySeat[i]?.laps"
              :fastest-index="lapsBySeat[i]?.fastest_lap_index"
              :finished="lapsBySeat[i]?.finished_flag"
              :row="rowsByNode[i]"
              :rssi="S.heartbeat?.current_rssi?.[i]"
              :crossing="S.heartbeat?.crossing_flag?.[i]"
              :enter-at="S.enter_and_exit_at_levels?.enter_at_levels?.[i]"
              :exit-at="S.enter_and_exit_at_levels?.exit_at_levels?.[i]"
              :racing="isRacing"
              :stopped="isDone && !!currentHeatId"
              :admin="!!admin"
              :min-lap-ms="minLapMs"
              @manual-lap="manualLap(i)"
              @delete-lap="(idx: number) => rh.emit('delete_lap', { node: i, lap_index: idx })"
              @restore-lap="(idx: number) => rh.emit('restore_deleted_lap', { node: i, lap_index: idx })"
              @tune="openSeat(i)"
            />
          </div>

          <div class="min-w-0 space-y-4">
            <!-- id="leaderboard": classic-page plugins dock their panels before it -->
            <UCard id="leaderboard" :ui="{ body: 'p-0 sm:p-0' }">
              <template #header>
                <div class="flex items-center justify-between">
                  <h2 class="font-semibold text-highlighted">
                    {{ t('Leaderboard') }}
                  </h2>
                  <span class="text-xs text-muted">{{ currentFormat?.name }}</span>
                </div>
              </template>
              <RhLeaderboard :board="board" kind="current" :seat-colors="seatColors" :min-lap-ms="minLapMs" dense />
            </UCard>
            <UCard v-if="teamBoard" :ui="{ body: 'p-0 sm:p-0' }">
              <template #header>
                <h2 class="font-semibold text-highlighted">
                  {{ t('Teams') }}
                </h2>
              </template>
              <RhTeamLeaderboard :board="teamBoard" />
            </UCard>
          </div>
        </div>

        <!-- classic-page plugins (Gate Walkthrough Calibration, Auto Marshalling...) append their panels here -->
        <div id="rh-plugin-dock" class="flex flex-wrap gap-3 empty:hidden" />

        <RhRaceTools />
      </div>

      <!-- phone / tablet: race clock and primary action stay within reach -->
      <div
        v-if="admin !== false"
        class="sticky bottom-0 z-20 mt-auto border-t border-default bg-default/85 px-4 pt-3 backdrop-blur-xl lg:hidden"
        style="padding-bottom: max(0.75rem, env(safe-area-inset-bottom))"
      >
        <div class="mx-auto flex max-w-3xl items-center gap-3">
          <RhRaceClock size="sm" class="me-auto" />
          <UButton
            v-if="isDone"
            color="neutral"
            variant="ghost"
            icon="i-lucide-trash-2"
            :aria-label="t('Discard')"
            :label="t('Discard')"
            :ui="{ label: 'max-[420px]:sr-only' }"
            @click="discardOpen = true"
          />
          <UButton
            v-if="isRacing"
            color="neutral"
            variant="ghost"
            icon="i-lucide-save"
            :aria-label="t('Stop and Save')"
            :ui="{ label: 'max-[420px]:sr-only' }"
            :label="t('Stop and Save')"
            @click="save"
          />
          <UButton
            v-if="isReady"
            size="lg"
            icon="i-lucide-play"
            :label="t('Start Race')"
            :loading="busy"
            class="rounded-full px-5"
            @click="start"
          />
          <UButton
            v-else-if="isLive"
            size="lg"
            color="error"
            icon="i-lucide-square"
            :label="t('Stop Race')"
            class="rounded-full px-5"
            @click="stop"
          />
          <template v-else>
            <UButton
              v-if="!anyLaps"
              color="neutral"
              variant="ghost"
              icon="i-lucide-rotate-ccw"
              :aria-label="t('Restart')"
              @click="start"
            />
            <UButton
              size="lg"
              color="success"
              icon="i-lucide-check"
              :label="currentHeatId ? t('Save Results') : t('Clear Laps')"
              class="rounded-full px-5"
              @click="save"
            />
          </template>
        </div>
      </div>

      <UModal v-model:open="discardOpen" :title="t('Discard this race?')" :description="t('The laps from this race will be deleted and the timer reset.')">
        <template #footer="{ close }">
          <div class="flex w-full justify-end gap-2">
            <UButton color="neutral" variant="ghost" :label="t('Cancel')" @click="close" />
            <UButton color="error" :label="t('Discard Laps')" @click="discard" />
          </div>
        </template>
      </UModal>

      <RhHeatPlan v-model:plan="plan" source="run" />

      <USlideover
        :open="marshalSeat !== null"
        :title="marshalSeat !== null ? `${t('Marshal')} · ${heatNodes[marshalSeat]?.callsign || `${t('Seat')} ${marshalSeat + 1}`}` : ''"
        :description="t('Correct laps for the race that just finished, then commit before saving.')"
        :ui="{ content: 'max-w-3xl' }"
        @update:open="(o: boolean) => { if (!o) marshalSeat = null }"
      >
        <template #body>
          <RhMarshalEditor
            v-if="marshalData && marshalSeat !== null"
            :data="marshalData"
            :start-time="marshal.race.start_time"
            :format-id="marshal.race.format_id"
            :seat="marshalSeat"
            :color="seatColors[marshalSeat]"
            :can-commit="!!heatNodes[marshalSeat]?.pilot_id"
            :graph-height="240"
            @commit="commitMarshal"
            @discard="marshalSeat = null"
          />
        </template>
      </USlideover>

      <USlideover
        :open="tuneSeat !== null"
        :title="tuneSeat !== null ? `${t('Tuning')} · ${t('Seat')} ${tuneSeat + 1}` : ''"
        :description="tuneSeat !== null ? (heatNodes[tuneSeat]?.callsign || '') : ''"
        :ui="{ content: 'max-w-xl' }"
        @update:open="(o: boolean) => { if (!o) tuneSeat = null }"
      >
        <template #body>
          <RhNodeTuning v-if="tuneSeat !== null" :node="tuneSeat" />
        </template>
      </USlideover>
    </template>
  </UDashboardPanel>
</template>
