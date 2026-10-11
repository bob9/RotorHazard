<script setup lang="ts">
/** VRx diagnostics (the classic /vrxstatus page): controllers and devices as the timer sees them. */
const { t } = useI18n()
const rh = useRH()
useHead({ title: computed(() => t('VRx Status')) })
rh.load(['vrx_list'])

const list = computed(() => rh.state.vrx_list || null)
const controllers = computed(() => Object.entries<any>(list.value?.controllers || {}))
const devices = computed(() => Object.entries<any>(list.value?.devices || {}))
const show = (v: any) => (v !== null && typeof v === 'object' ? JSON.stringify(v, null, 2) : String(v ?? '—'))
</script>

<template>
  <UDashboardPanel id="vrx-status">
    <template #header>
      <UDashboardNavbar :title="t('VRx Status')">
        <template #leading>
          <UButton icon="i-lucide-chevron-left" color="neutral" variant="ghost" to="/settings/system" :aria-label="t('System')" />
        </template>
        <template #right>
          <UButton color="neutral" variant="ghost" icon="i-lucide-refresh-cw" :aria-label="t('Refresh')" @click="rh.refresh(['vrx_list'])" />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div class="mx-auto w-full max-w-5xl space-y-8">
        <p class="text-sm text-muted">
          {{ t('Diagnostic view of VRx controllers and the video receivers they report.') }}
        </p>
        <div v-if="!list" class="grid gap-4 sm:grid-cols-2">
          <USkeleton v-for="i in 2" :key="i" class="h-40 rounded-2xl" />
        </div>
        <UEmpty v-else-if="!controllers.length && !devices.length" icon="i-lucide-tv" :title="t('No VRx controllers')" :description="t('Enable a VRx controller plugin to see its receivers here.')" variant="naked" />
        <template v-else>
          <section v-if="controllers.length" class="space-y-3">
            <h2 class="px-1 font-display text-xl font-semibold text-highlighted">
              {{ t('Controllers') }}
            </h2>
            <div class="grid gap-4 sm:grid-cols-2">
              <UCard v-for="[id, c] in controllers" :key="id">
                <div class="mb-3 flex items-center justify-between gap-2">
                  <span class="font-medium text-highlighted">{{ id }}</span>
                  <UBadge :color="c.ready ? 'success' : 'neutral'" variant="subtle" :label="c.ready ? t('Ready') : t('Not ready')" />
                </div>
                <dl class="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5 text-sm">
                  <template v-for="(v, k) in c.mapping || {}" :key="k">
                    <dt class="text-muted">{{ k }}</dt>
                    <dd class="tabular min-w-0 truncate">{{ show(v) }}</dd>
                  </template>
                </dl>
              </UCard>
            </div>
          </section>
          <section v-if="devices.length" class="space-y-3">
            <h2 class="px-1 font-display text-xl font-semibold text-highlighted">
              {{ t('Devices') }}
            </h2>
            <div class="grid gap-4 sm:grid-cols-2">
              <UCard v-for="[id, d] in devices" :key="id">
                <div class="mb-3 font-medium text-highlighted">{{ id }}</div>
                <dl class="grid grid-cols-[auto_minmax(0,1fr)] gap-x-4 gap-y-1.5 text-sm">
                  <template v-for="(v, k) in d" :key="k">
                    <dt class="text-muted">{{ k }}</dt>
                    <dd v-if="v !== null && typeof v === 'object'"><pre class="overflow-x-auto whitespace-pre-wrap font-mono text-xs">{{ show(v) }}</pre></dd>
                    <dd v-else class="tabular min-w-0 break-words">{{ show(v) }}</dd>
                  </template>
                </dl>
              </UCard>
            </div>
          </section>
        </template>
      </div>
    </template>
  </UDashboardPanel>
</template>
