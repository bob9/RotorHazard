<script setup lang="ts">
// Plugin page viewer: shows a page added with rhapi.ui.blueprint_add() inside the app.
const { t } = useI18n()
const { info } = useServerInfo()
// the classic stylesheet follows prefers-color-scheme, which inside a frame comes from the
// frame element's color-scheme: pass the app's appearance through
const colorMode = useColorMode()
const route = useRoute()

// only same-origin paths ("/x", not "//host" or "/\host") may be framed
const url = computed(() => {
  const u = typeof route.query.url === 'string' ? route.query.url.trim() : ''
  return /^\/(?![/\\])/.test(u) ? u : null
})

// app routes open in the app itself (framing the app inside itself is never wanted)
const base = useRuntimeConfig().app.baseURL
watch(url, (u) => {
  if (u && (u + '/').startsWith(base)) navigateTo(u.slice(base.length - 1) || '/', { replace: true })
}, { immediate: true })

const entry = computed(() => info.value?.plugin_pages?.find(p => p.url === url.value))
const title = computed(() => {
  if (entry.value?.label) return t(entry.value.label)
  if (!url.value) return t('Plugin Page')
  const last = url.value.split(/[?#]/)[0]!.replace(/\/+$/, '').split('/').pop() || ''
  return last ? last.replace(/[-_]/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) : t('Plugin Page')
})
useHead({ title })

const frame = ref<HTMLIFrameElement | null>(null)
const loading = ref(true)
const nonce = ref(0)
watch(url, () => { loading.value = true })

function reload() {
  loading.value = true
  try {
    frame.value?.contentWindow?.location.reload()
  } catch {
    nonce.value++
  }
}
</script>

<template>
  <UDashboardPanel id="plugin-page" :ui="{ body: 'p-0 sm:p-0 gap-0 overflow-hidden' }">
    <template #header>
      <UDashboardNavbar :title="title">
        <template #right>
          <template v-if="url">
            <UButton
              color="neutral"
              variant="ghost"
              icon="i-lucide-rotate-cw"
              :loading="loading"
              :aria-label="t('Reload')"
              @click="reload"
            />
            <UButton
              color="neutral"
              variant="ghost"
              icon="i-lucide-external-link"
              :to="url"
              target="_blank"
              external
              :label="t('Open in new tab')"
              :ui="{ label: 'hidden sm:inline' }"
            />
          </template>
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <!-- plugin pages carry their own (usually light) styling: show them as an inset sheet -->
      <div v-if="url" class="relative min-h-0 flex-1 bg-elevated/40">
        <div v-if="loading" class="absolute inset-x-0 top-0 z-10">
          <UProgress size="2xs" animation="carousel" />
        </div>
        <iframe
          :key="`${url}#${nonce}`"
          ref="frame"
          :src="url"
          :title="title"
          class="absolute inset-2 h-[calc(100%-1rem)] w-[calc(100%-1rem)] rounded-xl border-0 bg-white shadow-sm ring-1 ring-default sm:inset-4 sm:h-[calc(100%-2rem)] sm:w-[calc(100%-2rem)] dark:ring-white/10"
          :style="{ colorScheme: colorMode.value === 'dark' ? 'dark' : 'light' }"
          @load="loading = false"
        />
      </div>
      <div v-else class="flex flex-1 items-center justify-center p-6">
        <UEmpty
          icon="i-lucide-shield-alert"
          :title="t('This page cannot be shown')"
          :description="t('Only pages served by this timer can be opened here.')"
          :actions="[{ label: t('Plugins'), icon: 'i-lucide-puzzle', to: '/plugins', color: 'neutral', variant: 'subtle' }]"
          variant="naked"
        />
      </div>
    </template>
  </UDashboardPanel>
</template>
