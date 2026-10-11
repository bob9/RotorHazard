<script setup lang="ts">
/**
 * Marshaling editor for one pilot's race: RSSI history graph with draggable
 * EnterAt / ExitAt, client-side lap recalculation (same algorithm as the
 * classic marshal.js), lap table with delete / restore, manual laps.
 *
 * Used by the Marshal page (saved races → `resave_laps`) and can be used by
 * the Race page for the current race after stop (`current_marshal_data` →
 * `replace_current_laps`). The parent sends the result: `commit` carries
 * `{ laps, enter_at, exit_at }` ready to merge into either payload.
 */
import type { MarshalLap, MarshalHistory, MarshalOptions } from '~/utils/marshal'
import { LAP_SOURCE, LAP_SOURCE_LABELS, MARSHAL_TYPE, isAfterTimeExpired, passPeakHistory, recalcLaps, updateLapTimes } from '~/utils/marshal'

export interface MarshalPilotData {
  history_times?: number[]
  history_values?: number[]
  laps?: MarshalLap[]
  enter_at?: number
  exit_at?: number
  marshal_type?: number
}
export interface MarshalCommit { laps: MarshalLap[], enter_at: number, exit_at: number }

const props = withDefaults(defineProps<{
  /** race_details (saved race) or current_marshal_data.seats[i] (current race) */
  data: MarshalPilotData | null
  /** race start, server monotonic seconds */
  startTime: number
  formatId?: number | null
  /** seat (node index): enables "Load from Node" / "Save to Node" in manual calibration mode */
  seat?: number | null
  color?: string
  canCommit?: boolean
  commitLabel?: string
  discardLabel?: string
  /** the graph height in px */
  graphHeight?: number
}>(), { canCommit: true, color: '#3b82f6', formatId: null, seat: null, commitLabel: undefined, discardLabel: undefined, graphHeight: 280 })

const emit = defineEmits<{
  'commit': [MarshalCommit]
  'discard': []
  'update:dirty': [boolean]
}>()

const rh = useRH()
const { t } = useI18n()
const toast = useToast()
rh.load(['min_lap', 'format_data', { type: 'config', value: { TIMING: ['calibrationMode'] } }])

const S = rh.state
const calibrationMode = ref<number | null>(null)
rh.on('config_update', (d: any) => {
  const v = d?.config?.TIMING?.calibrationMode
  if (v !== undefined) calibrationMode.value = Number(v)
})

const raceFormat = computed(() => {
  if (!props.formatId || props.formatId <= 0) return null
  return (S.format_data?.formats || []).find((f: any) => f.id === props.formatId) || null
})
const timed = computed(() => !!raceFormat.value && !raceFormat.value.unlimited_time)
const minLapMs = computed(() => (Number(S.min_lap?.min_lap) || 0) * 1000)
const minFirstMs = computed(() => (Number(S.min_lap?.min_first_crossing) || 0) * 1000)

// ---- editing state ----
const laps = ref<MarshalLap[]>([])
const enterAt = ref(0)
const exitAt = ref(0)
const marshalType = ref(MARSHAL_TYPE.RSSI as number)
const history = shallowRef<MarshalHistory>({ times: [], values: [] })
const selected = ref<number | null>(null)
const manualTime = ref<number | string | undefined>()
// the manual lap time in seconds, when one is entered
const manualSec = computed(() => {
  const v = manualTime.value
  if (v === undefined || v === '') return null
  const n = Number(v)
  return Number.isFinite(n) && n >= 0 ? n : null
})
const baseline = ref('')

const isPassPeak = computed(() => marshalType.value === MARSHAL_TYPE.PASS_PEAK_ONLY)
const hasHistory = computed(() => history.value.times.length > 0)
const canRecalc = computed(() => hasHistory.value)

function signature() {
  return JSON.stringify([enterAt.value, exitAt.value, laps.value.map(l => [Math.round(l.lap_time_stamp), l.source, !!l.deleted])])
}
const dirty = computed(() => !!props.data && signature() !== baseline.value)
watch(dirty, v => emit('update:dirty', v), { immediate: true })

function load() {
  const d = props.data
  selected.value = null
  manualTime.value = undefined
  if (!d) {
    laps.value = []
    history.value = { times: [], values: [] }
    baseline.value = signature()
    return
  }
  marshalType.value = d.marshal_type ?? MARSHAL_TYPE.RSSI
  enterAt.value = Number(d.enter_at ?? 0)
  exitAt.value = Number(d.exit_at ?? 0)
  const src = (d.laps || []).map(l => ({ ...l, deleted: !!l.deleted }))
  history.value = marshalType.value === MARSHAL_TYPE.PASS_PEAK_ONLY
    ? passPeakHistory(src, props.startTime)
    : { times: d.history_times || [], values: d.history_values || [] }
  laps.value = updateLapTimes(src)
  baseline.value = signature()
}
watch(() => [props.data, props.startTime], load, { immediate: true })

function options(): MarshalOptions {
  return {
    startTime: props.startTime,
    enterAt: enterAt.value,
    exitAt: exitAt.value,
    marshalType: marshalType.value,
    minLapMs: minLapMs.value,
    minLapBehavior: Number(S.min_lap?.min_lap_behavior) || 0,
    minFirstCrossingMs: minFirstMs.value,
    raceFormat: raceFormat.value
  }
}

function recalc() {
  if (!canRecalc.value) return
  laps.value = recalcLaps(history.value, laps.value, options())
  selected.value = null
}

// EnterAt / ExitAt (keep Exit ≤ Enter, as the classic setEnter / setExit do)
function setEnter(v: number | null | undefined) {
  if (v === null || v === undefined || Number.isNaN(Number(v))) return
  const n = Math.max(0, Math.min(255, Math.round(Number(v))))
  enterAt.value = n
  if (n < exitAt.value) exitAt.value = n
  recalc()
}
function setExit(v: number | null | undefined) {
  if (v === null || v === undefined || Number.isNaN(Number(v))) return
  const n = Math.max(0, Math.min(255, Math.round(Number(v))))
  exitAt.value = n
  if (n > enterAt.value) enterAt.value = n
  recalc()
}

// ---- laps ----
const rows = computed(() => {
  let n = 0
  return laps.value.map((lap, i) => {
    const num = lap.deleted ? null : n++
    return {
      lap,
      i,
      num,
      short: !lap.deleted && !!num && (lap.lap_time ?? 0) < minLapMs.value,
      late: isAfterTimeExpired(lap, raceFormat.value)
    }
  })
})
const deletedCount = computed(() => laps.value.filter(l => l.deleted).length)
const lapCount = computed(() => Math.max(0, laps.value.length - deletedCount.value - 1))

function toggleDeleted(i: number) {
  const lap = laps.value[i]
  if (!lap) return
  lap.deleted = !lap.deleted
  updateLapTimes(laps.value)
}
function select(i: number | null) {
  selected.value = selected.value === i ? null : i
  if (selected.value !== null) manualTime.value = undefined
}
function addLap() {
  const s = manualSec.value
  if (s === null) {
    toast.add({ title: t('To add a lap manually, first specify lap time'), icon: 'i-lucide-info', color: 'warning' })
    return
  }
  const lap: MarshalLap = { crossingStart: 0, crossingEnd: 0, lap_time_stamp: Math.trunc(s * 1000), source: LAP_SOURCE.MANUAL, deleted: false }
  laps.value.push(lap)
  updateLapTimes(laps.value)
  selected.value = laps.value.findIndex(l => l.lap_time_stamp === lap.lap_time_stamp && l.source === LAP_SOURCE.MANUAL)
  manualTime.value = undefined
}
function cleanDeleted() {
  laps.value = laps.value.filter(l => !l.deleted)
  selected.value = null
}

// ---- graph ----
const lastStamp = computed(() => laps.value.reduce((m, l) => Math.max(m, l.lap_time_stamp), 0))
const domain = computed<[number, number]>(() => {
  const s = props.startTime
  const ts = history.value.times
  let end = ts.length && !isPassPeak.value ? ts[ts.length - 1]! : s
  end = Math.max(end, s + lastStamp.value / 1000 + (ts.length ? 0 : 2))
  if (end <= s) end = s + (timed.value ? Number(raceFormat.value.race_time_sec) || 10 : 10)
  return [s, end]
})
const regions = computed(() => {
  const r: { from: number, to: number }[] = []
  const s = props.startTime
  if (minFirstMs.value) r.push({ from: s, to: s + minFirstMs.value / 1000 })
  if (timed.value) r.push({ from: s + (Number(raceFormat.value.race_time_sec) || 0), to: domain.value[1] + 1 })
  return r
})
const markers = computed(() => rows.value.map(r => ({
  time: props.startTime + r.lap.lap_time_stamp / 1000,
  deleted: r.lap.deleted,
  label: r.num === null ? undefined : String(r.num),
  active: r.i === selected.value,
  ...(!isPassPeak.value && r.lap.crossingStart && r.lap.crossingEnd ? { start: r.lap.crossingStart, end: r.lap.crossingEnd } : {})
})))
const cursor = computed(() => {
  if (selected.value !== null && laps.value[selected.value]) return props.startTime + laps.value[selected.value]!.lap_time_stamp / 1000
  if (manualSec.value !== null) return props.startTime + manualSec.value
  return null
})

const graphBox = ref<HTMLElement>()
function onSeek(time: number) {
  // tap near a lap selects it; elsewhere it picks the time for a manual lap
  const width = graphBox.value?.clientWidth || 600
  const tol = ((domain.value[1] - domain.value[0]) * 10) / width
  let best: number | null = null
  let bestD = Infinity
  laps.value.forEach((l, i) => {
    const d = Math.abs(props.startTime + l.lap_time_stamp / 1000 - time)
    if (d < bestD) {
      bestD = d
      best = i
    }
  })
  if (best !== null && bestD <= tol) {
    selected.value = best
    manualTime.value = undefined
    scrollToRow(best)
  } else {
    selected.value = null
    manualTime.value = Math.max(0, Math.round((time - props.startTime) * 1000) / 1000)
  }
}

// ---- node levels (manual calibration mode only, as in the classic page) ----
const showNodeTools = computed(() => props.seat !== null && props.seat !== undefined && calibrationMode.value === 0)
let loadPending = false
rh.on('enter_and_exit_at_levels', (d: any) => {
  if (!loadPending || props.seat === null || props.seat === undefined) return
  loadPending = false
  const en = d?.enter_at_levels?.[props.seat]
  const ex = d?.exit_at_levels?.[props.seat]
  if (en === undefined || ex === undefined) return
  if (en === enterAt.value && ex === exitAt.value) return
  enterAt.value = en
  exitAt.value = Math.min(ex, en)
  recalc()
})
function loadFromNode() {
  loadPending = true
  rh.refresh(['enter_and_exit_at_levels'])
}
function saveToNode() {
  if (props.seat === null || props.seat === undefined) return
  rh.emit('set_enter_at_level', { node: props.seat, enter_at_level: enterAt.value })
  rh.emit('set_exit_at_level', { node: props.seat, exit_at_level: exitAt.value })
  toast.add({ title: t('Enter/Exit points saved to active node'), icon: 'i-lucide-check-circle', color: 'success' })
}

// ---- confirm ----
function commit() {
  if (!props.data) return
  updateLapTimes(laps.value)
  emit('commit', {
    laps: JSON.parse(JSON.stringify(laps.value)),
    enter_at: enterAt.value,
    exit_at: exitAt.value
  })
  baseline.value = signature()
}
function discard() {
  load()
  emit('discard')
}

// ---- keyboard: arrows move the highlight, Delete or x toggles delete ----
const table = ref<HTMLElement>()
function scrollToRow(i: number) {
  nextTick(() => table.value?.querySelector(`[data-lap="${i}"]`)?.scrollIntoView({ block: 'nearest' }))
}
function onKey(e: KeyboardEvent) {
  if (!props.data || e.ctrlKey || e.metaKey || e.altKey || e.defaultPrevented) return
  const el = e.target as HTMLElement
  if (el?.closest('input, textarea, select, [contenteditable], [role="listbox"], [role="menu"], [role="combobox"]')) return
  const n = laps.value.length
  if (!n) return
  if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
    const dir = e.key === 'ArrowDown' ? 1 : -1
    const cur = selected.value
    selected.value = cur === null ? (dir > 0 ? 0 : n - 1) : Math.min(n - 1, Math.max(0, cur + dir))
    manualTime.value = undefined
    scrollToRow(selected.value)
    e.preventDefault()
  } else if ((e.key === 'Delete' || e.key === 'x' || e.key === 'X') && selected.value !== null) {
    toggleDeleted(selected.value)
    e.preventDefault()
  } else if (e.key === 'Escape' && selected.value !== null) {
    selected.value = null
  }
}
onMounted(() => window.addEventListener('keydown', onKey))
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))

const sourceColor = (s: number) => (({ 0: 'neutral', 1: 'info', 2: 'primary', 3: 'neutral', 4: 'secondary' } as const)[s as 0] || 'neutral')
const fmtStamp = (ms: number) => (ms / 1000).toFixed(3)

defineExpose({ dirty, recalc, reset: load, setEnter, setExit })
</script>

<template>
  <div class="space-y-6">
    <!-- graph -->
    <section class="overflow-hidden rounded-3xl bg-default ring-1 ring-default shadow-sm">
      <div class="flex flex-wrap items-center gap-x-4 gap-y-3 border-b border-default px-4 py-3 sm:px-5">
        <div class="min-w-0 flex-1">
          <slot name="title" />
        </div>
        <div class="flex w-full items-center gap-2 sm:w-auto">
          <Transition name="rh">
            <UBadge
              v-if="dirty"
              color="warning"
              variant="subtle"
              icon="i-lucide-circle-dot"
              :label="t('Unsaved changes')"
              class="hidden sm:inline-flex"
            />
          </Transition>
          <UButton
            color="neutral"
            variant="ghost"
            icon="i-lucide-undo-2"
            :label="discardLabel || t('Discard Changes')"
            :aria-label="discardLabel || t('Discard Changes')"
            :ui="{ label: 'hidden sm:inline' }"
            class="ml-auto sm:ml-0"
            :disabled="!data"
            @click="discard"
          />
          <UButton
            icon="i-lucide-check"
            :label="commitLabel || t('Commit Changes')"
            :title="dirty ? t('Unsaved changes') : undefined"
            :disabled="!data || !canCommit"
            :variant="dirty ? 'solid' : 'soft'"
            @click="commit"
          />
        </div>
      </div>

      <div class="space-y-3 p-4 sm:p-5">
        <div class="flex flex-wrap items-end justify-between gap-3">
          <div class="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted">
            <span class="inline-flex items-center gap-1.5"><span class="h-0.5 w-4 rounded bg-[#ef4444]" />{{ t('EnterAt') }}</span>
            <span class="inline-flex items-center gap-1.5"><span class="h-0.5 w-4 rounded bg-[#f59e0b]" />{{ t('ExitAt') }}</span>
            <span class="inline-flex items-center gap-1.5"><span class="h-3 w-0.5 rounded bg-success" />{{ t('Lap') }}</span>
            <span class="inline-flex items-center gap-1.5"><span class="h-3 w-0 border-l border-dashed border-(--ui-text-dimmed)" />{{ t('Deleted') }}</span>
          </div>
          <div class="grid w-full grid-cols-[1fr_1fr_auto] items-end gap-2 sm:flex sm:w-auto">
            <UFormField :label="t('EnterAt')" size="sm" class="sm:w-28">
              <UInputNumber :model-value="enterAt" :min="0" :max="255" size="sm" :disabled="!data" @update:model-value="setEnter" />
            </UFormField>
            <UFormField :label="t('ExitAt')" size="sm" class="sm:w-28">
              <UInputNumber :model-value="exitAt" :min="0" :max="255" size="sm" :disabled="!data" @update:model-value="setExit" />
            </UFormField>
            <UTooltip :text="canRecalc ? t('Recalculate laps from the RSSI history') : t('No RSSI history was recorded for this race')">
              <UButton
                color="neutral"
                variant="outline"
                size="sm"
                icon="i-lucide-refresh-cw"
                :label="t('Recalculate')"
                :aria-label="t('Recalculate')"
                :ui="{ label: 'hidden sm:inline' }"
                :disabled="!data || !canRecalc"
                @click="recalc"
              />
            </UTooltip>
          </div>
        </div>

        <div ref="graphBox">
          <RhRssiGraph
            :history="history"
            :enter-at="enterAt"
            :exit-at="exitAt"
            :editable="!!data && canRecalc"
            :color="color"
            :height="graphHeight"
            :markers="markers"
            :cursor="cursor"
            :domain="domain"
            :origin="startTime"
            :regions="regions"
            @update:enter-at="setEnter"
            @update:exit-at="setExit"
            @seek="onSeek"
          >
            <div v-if="data && !hasHistory" class="pointer-events-none absolute inset-x-0 top-1/2 flex -translate-y-1/2 justify-center px-4">
              <div class="flex items-center gap-2 rounded-full bg-default/90 px-3 py-1.5 text-xs text-muted shadow-xs ring-1 ring-default backdrop-blur">
                <UIcon name="i-lucide-activity" class="size-4" />
                {{ t('No RSSI history was recorded for this race') }}
              </div>
            </div>
          </RhRssiGraph>
        </div>
        <p class="text-xs text-muted">
          <template v-if="canRecalc">
            {{ t('Drag the lines to change EnterAt and ExitAt; laps are recalculated from the recorded signal. Click a lap to highlight it, or click anywhere else to pick a time for a manual lap.') }}
          </template>
          <template v-else>
            {{ t('Click a lap to highlight it, or click anywhere else to pick a time for a manual lap.') }}
          </template>
        </p>
      </div>
    </section>

    <div class="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
      <!-- laps -->
      <UCard :ui="{ body: 'p-0 sm:p-0', header: 'px-4 sm:px-5' }">
        <template #header>
          <div class="flex items-center justify-between gap-3">
            <h3 class="font-semibold text-highlighted">
              {{ t('Laps') }}
              <span class="ml-1 font-normal tabular text-muted">{{ lapCount }}</span>
            </h3>
            <div class="hidden items-center gap-1.5 text-xs text-dimmed sm:flex">
              <UKbd value="↑" size="sm" /><UKbd value="↓" size="sm" /> {{ t('select') }}
              <UKbd value="x" size="sm" class="ml-2" /> {{ t('delete / restore') }}
            </div>
          </div>
        </template>
        <div ref="table" class="max-h-[560px] overflow-auto">
          <table class="w-full text-sm">
            <thead class="sticky top-0 z-[1] bg-default/95 backdrop-blur">
              <tr class="text-left text-[11px] font-semibold uppercase tracking-wider text-dimmed">
                <th class="w-12 px-3 py-2 sm:pl-5">
                  {{ t('Lap') }}
                </th>
                <th class="px-3 py-2 text-right">
                  {{ t('Timestamp') }}
                </th>
                <th class="px-3 py-2 text-right">
                  {{ t('Lap Time') }}
                </th>
                <th class="hidden px-3 py-2 sm:table-cell">
                  {{ t('Source') }}
                </th>
                <th class="px-3 py-2 text-right">
                  {{ t('Peak') }}
                </th>
                <th class="w-12 px-3 py-2 sm:pr-5">
                  <span class="sr-only">{{ t('Deleted') }}</span>
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-default">
              <tr
                v-for="r in rows"
                :key="`${r.i}-${r.lap.lap_time_stamp}`"
                :data-lap="r.i"
                class="tabular cursor-pointer transition-colors"
                :class="[
                  r.i === selected ? 'bg-primary/10 shadow-[inset_3px_0_0_var(--ui-primary)]' : r.late ? 'bg-elevated/50 hover:bg-elevated' : 'hover:bg-elevated/60',
                  r.lap.deleted ? 'text-dimmed' : ''
                ]"
                @click="select(r.i)"
              >
                <td class="px-3 py-2 font-semibold sm:pl-5" :class="r.lap.deleted ? '' : 'text-highlighted'">
                  {{ r.num ?? '–' }}
                </td>
                <td class="px-3 py-2 text-right" :class="r.lap.deleted ? 'line-through' : ''">
                  {{ fmtStamp(r.lap.lap_time_stamp) }}
                </td>
                <td class="px-3 py-2 text-right">
                  <span v-if="r.lap.deleted" class="text-xs font-medium uppercase tracking-wide">{{ t('Deleted') }}</span>
                  <span v-else class="inline-flex items-center gap-1" :class="r.short ? 'font-medium text-amber-700 dark:text-amber-400' : 'text-highlighted'">
                    <UTooltip v-if="r.short" :text="t('Shorter than the minimum lap time')">
                      <UIcon name="i-lucide-triangle-alert" class="size-3.5" />
                    </UTooltip>
                    {{ formatLapMs(r.lap.lap_time) }}
                  </span>
                  <UTooltip v-if="r.late" :text="t('After the race time expired')">
                    <UIcon name="i-lucide-flag" class="ml-1 size-3.5 align-[-2px] text-dimmed" />
                  </UTooltip>
                </td>
                <td class="hidden px-3 py-2 sm:table-cell">
                  <UBadge :label="t(LAP_SOURCE_LABELS[r.lap.source] || String(r.lap.source))" :color="sourceColor(r.lap.source)" variant="subtle" size="sm" />
                </td>
                <td class="px-3 py-2 text-right text-muted">
                  {{ r.lap.peak_rssi ?? '—' }}
                </td>
                <td class="px-3 py-1.5 text-right sm:pr-5">
                  <UTooltip :text="r.lap.deleted ? t('Restore') : t('Delete')">
                    <UButton
                      :icon="r.lap.deleted ? 'i-lucide-rotate-ccw' : 'i-lucide-x'"
                      :color="r.lap.deleted ? 'neutral' : 'error'"
                      variant="ghost"
                      size="xs"
                      :aria-label="r.lap.deleted ? t('Restore') : t('Delete')"
                      @click.stop="toggleDeleted(r.i)"
                    />
                  </UTooltip>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-if="data && !rows.length" class="py-10 text-center text-sm text-dimmed">
            {{ t('No laps recorded') }}
          </div>
        </div>
      </UCard>

      <!-- tools -->
      <div class="space-y-6">
        <RhGroup :title="t('Modify')">
          <div class="space-y-3 px-4 py-3">
            <UFormField :label="t('Manual Lap Time')" :hint="t('seconds')">
              <UFieldGroup class="w-full">
                <UInput
                  v-model.number="manualTime"
                  type="number"
                  step="0.001"
                  min="0"
                  :placeholder="'0.000'"
                  :disabled="!data"
                  class="flex-1"
                  @focus="selected = null"
                  @keydown.enter="addLap"
                />
                <UButton icon="i-lucide-plus" :label="t('Add Lap')" :disabled="!data" @click="addLap" />
              </UFieldGroup>
            </UFormField>
          </div>
          <div class="flex items-center justify-between gap-3 px-4 py-3">
            <div class="min-w-0 text-[13px] text-muted">
              {{ deletedCount ? `${deletedCount} ${t('Deleted')}` : t('No deleted laps') }}
            </div>
            <UButton
              color="neutral"
              variant="soft"
              size="sm"
              icon="i-lucide-eraser"
              :label="t('Clean Deleted Laps')"
              :disabled="!data || !deletedCount"
              @click="cleanDeleted"
            />
          </div>
        </RhGroup>

        <RhGroup v-if="showNodeTools" :title="t('Node')" :footer="t('Use the race\'s EnterAt and ExitAt on the timer, or start from the timer\'s current values.')">
          <div class="flex flex-wrap gap-2 px-4 py-3">
            <UButton color="neutral" variant="soft" size="sm" icon="i-lucide-download" :label="t('Load from Node')" :disabled="!data" @click="loadFromNode" />
            <UButton color="neutral" variant="soft" size="sm" icon="i-lucide-upload" :label="t('Save to Node')" :disabled="!data" @click="saveToNode" />
          </div>
        </RhGroup>

        <slot name="aside" />
      </div>
    </div>
  </div>
</template>
