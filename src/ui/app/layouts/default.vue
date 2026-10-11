<script setup lang="ts">
import type { NavigationMenuItem } from '@nuxt/ui'

const rh = useRH()
const { t } = useI18n()
const { admin, loginOpen, logout } = useAuth()
const { info } = useServerInfo()
const { unread, restartRequired, restarting } = useMessages()
const colorMode = useColorMode()
const route = useRoute()

rh.load(['all_languages', 'language', 'race_status', 'current_heat'])

const sidebarOpen = ref(false)
const searchOpen = ref(false)
const messagesOpen = ref(false)
const aboutOpen = ref(false)

const raceLive = computed(() => [1, 3].includes(rh.state.race_status?.race_status))

// admin-only pages: guests who open one by address go to Live, with an offer to sign in
const ADMIN_PAGES = ['/marshal', '/pilots', '/heats', '/formats', '/timer', '/plugins', '/settings/general', '/settings/actions',
  '/settings/leds', '/settings/vrx', '/settings/plugins', '/settings/data', '/settings/cluster', '/settings/system']
const toast = useToast()
watch([admin, () => route.path], ([isAdmin, path]) => {
  if (isAdmin !== false || !ADMIN_PAGES.includes(path)) return
  navigateTo('/live', { replace: true })
  toast.add({
    title: t('Sign in to open that page'),
    icon: 'i-lucide-lock-keyhole',
    color: 'neutral',
    actions: [{ label: t('Sign in'), color: 'neutral', variant: 'outline', onClick: () => { loginOpen.value = true } }]
  })
}, { immediate: true })

const raceItems = computed<NavigationMenuItem[]>(() => [
  ...(admin.value
    ? [{ label: t('Race'), icon: 'i-lucide-flag', to: '/', badge: raceLive.value ? { label: t('Live'), color: 'error' as const, variant: 'solid' as const, size: 'sm' as const } : undefined },
        { label: t('Marshal'), icon: 'i-lucide-pencil-ruler', to: '/marshal' }]
    : [{ label: t('Live'), icon: 'i-lucide-radio', to: '/live' }]),
  { label: t('Results'), icon: 'i-lucide-trophy', to: '/results' },
  ...(admin.value ? [] : [{ label: t('Event'), icon: 'i-lucide-calendar-days', to: '/event' }])
])

const eventItems = computed<NavigationMenuItem[]>(() => admin.value
  ? [
      { label: t('Event'), icon: 'i-lucide-calendar-days', to: '/event' },
      { label: t('Pilots'), icon: 'i-lucide-users', to: '/pilots' },
      { label: t('Heats'), icon: 'i-lucide-layers', to: '/heats' },
      { label: t('Formats'), icon: 'i-lucide-timer', to: '/formats' }
    ]
  : [])

const systemItems = computed<NavigationMenuItem[]>(() => admin.value
  ? [
      { label: t('Timer'), icon: 'i-lucide-radio-tower', to: '/timer' },
      { label: t('Settings'), icon: 'i-lucide-settings', to: '/settings', badge: restartRequired.value ? { label: t('Restart'), color: 'warning' as const, variant: 'subtle' as const, size: 'sm' as const } : undefined },
      { label: t('Plugins'), icon: 'i-lucide-puzzle', to: '/plugins' }
    ]
  : [])

const pluginItems = computed<NavigationMenuItem[]>(() => (info.value?.plugin_pages || []).map(p => ({
  label: p.label ? t(p.label) : prettyPath(p.url),
  icon: 'i-lucide-app-window',
  to: `/page?url=${encodeURIComponent(p.url)}`,
  active: route.path === '/page' && route.query.url === p.url
})))

function prettyPath(url: string) {
  const last = url.replace(/\/+$/, '').split('/').pop() || url
  return last.replace(/[-_]/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

// Search covers pages, settings (with everyday synonyms), and event data
const searchData = ref(false)
watch(searchOpen, (o) => {
  if (o && !searchData.value) {
    searchData.value = true
    rh.load(['pilot_data', 'heat_data', 'class_data', 'format_data'])
  }
})
const settingsIndex = computed(() => admin.value
  ? [
      { label: t('Frequencies'), description: t('Timer'), icon: 'i-lucide-radio', to: '/timer', keywords: 'frequency frequencies channel channels band raceband vtx video node nodes imd preset' },
      { label: t('Sensor Tuning'), description: t('Timer'), icon: 'i-lucide-activity', to: '/timer', keywords: 'tuning enterat exitat rssi calibration signal gate threshold' },
      { label: t('Race duration and scoring'), description: t('Formats'), icon: 'i-lucide-timer', to: '/formats', keywords: 'duration length time clock minutes staging tones win condition laps scoring holeshot' },
      { label: t('Minimum Lap Time'), description: t('Race'), icon: 'i-lucide-gauge', to: '/', keywords: 'min lap minimum short laps ignore crossings' },
      { label: t('Audio'), description: t('Settings'), icon: 'i-lucide-volume-2', to: '/settings/audio', keywords: 'voice callouts sound speech tones beep volume announce' },
      { label: t('Event Actions'), description: t('Settings'), icon: 'i-lucide-zap', to: '/settings/actions', keywords: 'automation actions effects trigger' },
      { label: t('Data & Backups'), description: t('Settings'), icon: 'i-lucide-hard-drive', to: '/settings/data', keywords: 'backup restore export import csv json database new event archive reset' },
      { label: t('Admin Login'), description: t('Settings'), icon: 'i-lucide-key-round', to: '/settings/general', keywords: 'password username login admin security' },
      { label: t('Language'), description: t('Settings'), icon: 'i-lucide-languages', to: '/settings/general', keywords: 'language translation timer name logo appearance dark light theme interface classic' },
      { label: t('Secondary Timers'), description: t('Settings'), icon: 'i-lucide-network', to: '/settings/cluster', keywords: 'cluster split mirror secondary sensors' },
      { label: t('System'), description: t('Settings'), icon: 'i-lucide-cpu', to: '/settings/system', keywords: 'restart reboot shutdown logs version firmware advanced port' },
      { label: t('Plugins & Streams'), description: t('Settings'), icon: 'i-lucide-cast', to: '/settings/plugins', keywords: 'plugin settings stream overlay obs video' }
    ]
  : [])
const dataIndex = computed(() => {
  if (!searchData.value) return []
  const items: any[] = []
  for (const p of rh.state.pilot_data?.pilots || []) items.push({ label: p.callsign, description: [t('Pilot'), p.name].filter(Boolean).join(' · '), icon: 'i-lucide-user', to: '/pilots', keywords: `${p.name || ''} ${p.team || ''}` })
  const classes = rh.state.class_data?.classes || []
  for (const c of classes) items.push({ label: c.displayname, description: t('Class'), icon: 'i-lucide-trophy', to: `/heats?class=${c.id}` })
  for (const h of rh.state.heat_data?.heats || []) {
    items.push({ label: h.displayname, description: [t('Heat'), classes.find((c: any) => c.id === h.class_id)?.displayname].filter(Boolean).join(' · '), icon: 'i-lucide-layers', to: h.class_id ? `/heats?class=${h.class_id}` : '/heats' })
  }
  for (const f of rh.state.format_data?.formats || []) items.push({ label: t(f.name), description: t('Format'), icon: 'i-lucide-timer', to: '/formats' })
  return items
})
const searchGroups = computed(() => [
  {
    id: 'pages',
    label: t('Go to'),
    items: [...raceItems.value, ...eventItems.value, ...systemItems.value, ...pluginItems.value]
      .map(i => ({ label: i.label, icon: i.icon, to: i.to as string }))
  },
  ...(settingsIndex.value.length ? [{ id: 'settings', label: t('Settings'), items: settingsIndex.value }] : []),
  ...(dataIndex.value.length ? [{ id: 'event', label: t('Event'), items: dataIndex.value, ignoreFilter: false }] : []),
  {
    id: 'actions',
    label: t('Actions'),
    items: [
      { label: colorMode.value === 'dark' ? t('Light appearance') : t('Dark appearance'), icon: colorMode.value === 'dark' ? 'i-lucide-sun' : 'i-lucide-moon', onSelect: () => { colorMode.preference = colorMode.value === 'dark' ? 'light' : 'dark' } },
      { label: t('Classic interface'), icon: 'i-lucide-history', to: '/interface/classic', external: true, target: '_self' },
      { label: t('Documentation'), icon: 'i-lucide-book-open', to: '/docs?d=README.md', external: true, target: '_blank' },
      ...(admin.value ? [{ label: t('Restart server'), icon: 'i-lucide-rotate-cw', onSelect: () => { restartOpen.value = true } }] : [])
    ]
  }
])
const searchFuse = { fuseOptions: { keys: ['label', 'description', 'keywords'], threshold: 0.35, ignoreLocation: true }, resultLimit: 40 }

const restartOpen = ref(false)
// 'Later' hides the restart banner for this visit; the Settings item keeps a badge
const restartSnoozed = ref(false)
const { restartServer } = useMessages()

defineShortcuts({
  meta_k: () => { searchOpen.value = !searchOpen.value }
})

const logoUrl = useRuntimeConfig().app.baseURL + 'rh-icon.svg'
const version = computed(() => info.value?.server?.release_version)
</script>

<template>
  <UDashboardGroup unit="rem" storage="local" storage-key="rh-dashboard">
    <UDashboardSidebar
      id="rh"
      v-model:open="sidebarOpen"
      collapsible
      resizable
      :default-size="15"
      :min-size="13"
      :max-size="20"
      class="bg-elevated/40"
      :ui="{ footer: 'lg:border-t lg:border-default' }"
    >
      <template #header="{ collapsed }">
        <NuxtLink to="/" class="flex items-center gap-2.5 min-w-0">
          <img :src="logoUrl" alt="" class="size-7 shrink-0">
          <span v-if="!collapsed" class="truncate font-display text-[17px] font-semibold text-highlighted">RotorHazard</span>
        </NuxtLink>
      </template>

      <template #default="{ collapsed }">
        <UDashboardSearchButton :collapsed="collapsed" class="bg-transparent ring-default" :label="t('Search')" />

        <UNavigationMenu :collapsed="collapsed" :items="raceItems" orientation="vertical" tooltip popover />

        <template v-if="eventItems.length">
          <div v-if="!collapsed" class="mt-3 px-2.5 text-[11px] font-semibold uppercase tracking-wider text-dimmed">
            {{ t('Event') }}
          </div>
          <UNavigationMenu :collapsed="collapsed" :items="eventItems" orientation="vertical" tooltip popover />
        </template>

        <template v-if="systemItems.length">
          <div v-if="!collapsed" class="mt-3 px-2.5 text-[11px] font-semibold uppercase tracking-wider text-dimmed">
            {{ t('System') }}
          </div>
          <UNavigationMenu :collapsed="collapsed" :items="systemItems" orientation="vertical" tooltip popover />
        </template>

        <template v-if="pluginItems.length">
          <div v-if="!collapsed" class="mt-3 px-2.5 text-[11px] font-semibold uppercase tracking-wider text-dimmed">
            {{ t('Plugin Pages') }}
          </div>
          <UNavigationMenu :collapsed="collapsed" :items="pluginItems" orientation="vertical" tooltip popover />
        </template>
      </template>

      <template #footer="{ collapsed }">
        <div class="flex w-full flex-col gap-1">
          <RhConnection :collapsed="collapsed" />
          <UButton
            v-if="!admin"
            :label="collapsed ? undefined : t('Sign in as admin')"
            icon="i-lucide-lock-keyhole"
            color="neutral"
            variant="ghost"
            block
            :square="collapsed"
            class="justify-start"
            @click="loginOpen = true"
          />
          <UButton
            v-if="!admin"
            :label="collapsed ? undefined : t('Classic interface')"
            icon="i-lucide-history"
            color="neutral"
            variant="ghost"
            block
            :square="collapsed"
            class="justify-start"
            to="/interface/classic"
            external
            target="_self"
          />
          <UDropdownMenu
            v-else
            :items="[
              [{ label: t('About RotorHazard'), icon: 'i-lucide-info', onSelect: () => { aboutOpen = true } },
               { label: t('Classic interface'), icon: 'i-lucide-history', to: '/interface/classic', external: true, target: '_self' },
               { label: t('Documentation'), icon: 'i-lucide-book-open', to: '/docs?d=README.md', external: true, target: '_blank' }],
              [{ label: colorMode.value === 'dark' ? t('Light appearance') : t('Dark appearance'), icon: colorMode.value === 'dark' ? 'i-lucide-sun' : 'i-lucide-moon', onSelect: () => { colorMode.preference = colorMode.value === 'dark' ? 'light' : 'dark' } }],
              ...(info?.auth_required ? [[{ label: t('Sign out'), icon: 'i-lucide-log-out', onSelect: logout }]] : [])
            ]"
            :content="{ align: 'start', side: 'top' }"
          >
            <UButton
              color="neutral"
              variant="ghost"
              block
              :square="collapsed"
              class="justify-start"
              icon="i-lucide-shield-check"
              :label="collapsed ? undefined : t('Admin')"
              :trailing-icon="collapsed ? undefined : 'i-lucide-chevrons-up-down'"
              :ui="{ trailingIcon: 'ms-auto text-dimmed' }"
            />
          </UDropdownMenu>
        </div>
      </template>
    </UDashboardSidebar>

    <UDashboardSearch v-model:open="searchOpen" :groups="searchGroups" :fuse="searchFuse" :color-mode="false" :placeholder="t('Search pages, settings, pilots and heats…')" />

    <div class="flex min-w-0 flex-1 flex-col">
      <div
        v-if="restartRequired && admin && !restartSnoozed"
        class="flex shrink-0 items-center gap-3 border-b border-amber-300/60 bg-amber-100 px-4 py-2 text-sm text-amber-950 dark:border-amber-400/20 dark:bg-amber-400/15 dark:text-amber-100"
        role="status"
      >
        <UIcon :name="restarting ? 'i-lucide-loader-circle' : 'i-lucide-rotate-cw'" class="size-4 shrink-0" :class="restarting ? 'animate-spin' : ''" />
        <span class="min-w-0 flex-1 truncate">{{ restarting ? t('Restarting server…') : t('Restart the server to apply changed settings or plugins.') }}</span>
        <template v-if="!restarting">
          <UButton size="xs" color="neutral" variant="ghost" class="text-current" :label="t('Later')" @click="restartSnoozed = true" />
          <UButton size="xs" color="neutral" variant="solid" :label="t('Restart now')" @click="restartOpen = true" />
        </template>
      </div>
      <UBanner
        v-if="rh.status.everConnected && !rh.status.connected"
        icon="i-lucide-wifi-off"
        color="error"
        :title="restarting ? t('Server is restarting…') : t('Connection to the timer lost. Reconnecting…')"
      />
      <!-- bars that classic-page plugins add to <body> (classic-bridge.client.ts) -->
      <div id="rh-plugin-top" class="empty:hidden shrink-0 max-w-full overflow-x-auto" />
      <slot />
    </div>

    <RhLogin />
    <RhMessages v-model:open="messagesOpen" />
    <RhAlerts />

    <UModal v-model:open="aboutOpen" :title="t('About RotorHazard')">
      <template #body>
        <div class="space-y-4">
          <div class="flex items-center gap-4">
            <img :src="logoUrl" alt="" class="size-14">
            <div>
              <div class="font-display text-xl font-semibold">RotorHazard</div>
              <div class="text-sm text-muted">{{ version }}</div>
            </div>
          </div>
          <!-- eslint-disable-next-line vue/no-v-html -->
          <div class="rh-prose text-sm" v-html="info?.server?.about_html" />
          <div class="text-sm text-muted">
            {{ t('Clock sync') }}: ±{{ Math.ceil(rh.status.latencyMs / 2) }} ms
          </div>
        </div>
      </template>
    </UModal>

    <UModal v-model:open="restartOpen" :title="t('Restart server?')" :description="t('Races in progress will be stopped. The timer will be back in a few seconds.')">
      <template #footer="{ close }">
        <div class="flex w-full justify-end gap-2">
          <UButton color="neutral" variant="ghost" :label="t('Cancel')" @click="close" />
          <UButton color="warning" :label="t('Restart')" @click="() => { restartServer(); close() }" />
        </div>
      </template>
    </UModal>

    <ClientOnly>
      <Teleport to="body">
        <UButton
          v-if="unread || messagesOpen"
          class="fixed right-4 z-40 rounded-full shadow-lg"
          :class="route.path === '/' && admin ? 'bottom-24 lg:bottom-4' : 'bottom-4'"
          color="neutral"
          variant="solid"
          icon="i-lucide-bell"
          :label="String(unread)"
          @click="messagesOpen = true"
        />
      </Teleport>
    </ClientOnly>
  </UDashboardGroup>
</template>
