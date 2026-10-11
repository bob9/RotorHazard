<script setup lang="ts">
/**
 * Documentation viewer (the classic /docs page): the timer's Markdown docs, with
 * links between docs kept inside the app and an outline of the open doc.
 */
const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const docName = computed(() => (typeof route.query.d === 'string' && route.query.d) || 'README.md')
const label = (name: string) => (name === 'README.md' ? t('Documentation') : name.replace(/\.md$/i, ''))
useHead({ title: computed(() => label(docName.value)) })

const { data: list } = useFetch<{ docs: string[] }>('/app-docs', { baseURL: '/', server: false })
const docs = computed(() => {
  const all = list.value?.docs || []
  // the index first, then the guides in name order
  return ['README.md', ...all.filter(d => d !== 'README.md')].filter(d => all.includes(d) || d === 'README.md')
})
const docItems = computed(() => docs.value.map(d => ({ label: label(d), value: d })))

const markdown = ref('')
const loading = ref(true)
const failed = ref(false)
async function load(name: string) {
  loading.value = true
  failed.value = false
  try {
    const r = await $fetch<{ markdown: string }>('/app-docs', { baseURL: '/', query: { d: name } })
    markdown.value = r.markdown
  } catch {
    failed.value = true
    markdown.value = ''
  } finally {
    loading.value = false
  }
}
watch(docName, n => load(n), { immediate: true })

// GitHub-style heading ids, so the docs' own "#section" links work
function slug(text: string) {
  return text.trim().toLowerCase().replace(/[^\p{L}\p{N}\s-]/gu, '').replace(/\s/g, '-')
}
const html = computed(() => renderMarkdown(markdown.value))
const el = ref<HTMLElement>()
const outline = ref<{ id: string, text: string, level: number }[]>([])
watch(html, () => nextTick(() => {
  const root = el.value
  if (!root) return
  const seen: Record<string, number> = {}
  const items: typeof outline.value = []
  root.querySelectorAll('h1, h2, h3, h4').forEach((h) => {
    let id = slug(h.textContent || '')
    if (seen[id] !== undefined) id = `${id}-${(seen[id] = seen[id]! + 1)}`
    else seen[id] = 0
    h.id = id
    if (h.tagName === 'H2' || h.tagName === 'H3') items.push({ id, text: h.textContent || '', level: h.tagName === 'H2' ? 2 : 3 })
  })
  // images are served by the timer at /img/ (with translated copies where they exist)
  root.querySelectorAll('img').forEach((img) => {
    const src = img.getAttribute('src') || ''
    if (/^(\.\/)?img\//.test(src)) img.setAttribute('src', '/' + src.replace(/^\.\//, ''))
  })
  root.querySelectorAll('a').forEach(a => resolveLink(a))
  outline.value = items
  trackHeadings()
  if (route.hash) scrollTo(route.hash.slice(1), false)
}), { flush: 'post' })

// Links in the docs are written relative to the repository's doc/ folder. Another doc
// ("Cluster.md", "../doc/Cluster.md#x") opens here; anything else in the repository
// ("../src/node/readme_Arduino.md") opens on GitHub; web links open in a new tab.
const REPO = 'https://github.com/RotorHazard/RotorHazard/blob/main'
function resolveLink(a: HTMLAnchorElement) {
  const href = a.getAttribute('href') || ''
  if (!href || href.startsWith('#')) return
  if (/^[a-z][a-z0-9+.-]*:/i.test(href) || href.startsWith('//')) {
    a.target = '_blank'
    a.rel = 'noopener'
    return
  }
  const url = new URL(href, 'https://repo.invalid/doc/')
  const path = decodeURIComponent(url.pathname)
  const doc = path.match(/^\/doc\/([^/]+\.md)$/i)
  if (doc) {
    a.setAttribute('href', `/app/docs?d=${encodeURIComponent(doc[1]!)}${url.hash}`)
    a.dataset.doc = doc[1]!
    a.dataset.hash = url.hash
  } else {
    a.setAttribute('href', REPO + url.pathname + url.hash)
    a.target = '_blank'
    a.rel = 'noopener'
  }
}

// "On this page" follows the reading position: the last heading above the top third
const active = ref('')
function updateActive() {
  if (!el.value) return
  let current = ''
  for (const h of outline.value) {
    const top = document.getElementById(h.id)?.getBoundingClientRect().top ?? Infinity
    if (top < window.innerHeight / 3) current = h.id
    else break
  }
  active.value = current
}
function trackHeadings() {
  nextTick(updateActive)
}
if (import.meta.client) {
  document.addEventListener('scroll', updateActive, { capture: true, passive: true })
  onBeforeUnmount(() => document.removeEventListener('scroll', updateActive, { capture: true }))
}

// a link to another section of the open doc changes only the hash
watch(() => route.hash, (h, prev) => {
  if (h && h !== prev && !loading.value) scrollTo(h.slice(1))
})

// a section link (in the text or the outline) is a history entry with a shareable #hash
function goSection(id: string) {
  router.push({ query: route.query, hash: '#' + id })
  scrollTo(id)
}
function scrollTo(id: string, smooth = true) {
  document.getElementById(decodeURIComponent(id))?.scrollIntoView({ behavior: smooth ? 'smooth' : 'auto', block: 'start' })
}

// links to other docs ("User%20Guide.md#pages") open here; in-page anchors scroll
function onClick(e: MouseEvent) {
  const a = (e.target as HTMLElement).closest('a')
  if (!a || e.metaKey || e.ctrlKey || e.shiftKey || a.target === '_blank') return
  const href = a.getAttribute('href') || ''
  if (href.startsWith('#')) {
    e.preventDefault()
    // a history entry, so Back returns to where the reader was
    router.push({ query: route.query, hash: href })
    scrollTo(href.slice(1))
    return
  }
  if (a.dataset.doc) {
    e.preventDefault()
    router.push({ path: '/docs', query: { d: a.dataset.doc }, hash: a.dataset.hash || '' })
  }
}

// the User Guide still names the classic pages: say where they are in this interface
const classicNames = computed(() => [
  ['Run', t('Race')], ['Current', t('Live')], ['Format', t('Formats')], ['Event', `${t('Event')}, ${t('Pilots')}, ${t('Heats')}`],
  ['Settings', `${t('Timer')}, ${t('Settings')}`], ['Marshal', t('Marshal')], ['Results', t('Results')]
])
</script>

<template>
  <UDashboardPanel id="docs">
    <template #header>
      <UDashboardNavbar :title="label(docName)">
        <template #right>
          <UButton
            color="neutral"
            variant="ghost"
            icon="i-lucide-external-link"
            :to="`/docs?d=${encodeURIComponent(docName)}`"
            target="_blank"
            external
            :label="t('Open in new tab')"
            :ui="{ label: 'hidden sm:inline' }"
          />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div class="mx-auto grid w-full max-w-7xl grid-cols-1 gap-8 lg:grid-cols-[220px_minmax(0,1fr)] xl:grid-cols-[220px_minmax(0,1fr)_200px]">
        <!-- doc list: a menu on phones, a column on desktop -->
        <nav class="lg:sticky lg:top-0 lg:self-start" :aria-label="t('Documentation')">
          <USelectMenu
            :model-value="docName"
            :items="docItems"
            value-key="value"
            class="w-full lg:hidden"
            :search-input="false"
            @update:model-value="(v: any) => router.push({ path: '/docs', query: { d: v } })"
          />
          <ul class="hidden space-y-0.5 lg:block">
            <li v-for="d in docs" :key="d">
              <NuxtLink
                :to="{ path: '/docs', query: { d } }"
                class="block rounded-md px-2.5 py-1.5 text-sm transition-colors"
                :class="d === docName ? 'bg-elevated font-medium text-highlighted' : 'text-muted hover:bg-elevated/60 hover:text-default'"
              >
                {{ label(d) }}
              </NuxtLink>
            </li>
          </ul>
        </nav>

        <article class="min-w-0">
          <div v-if="loading && !markdown" class="space-y-4" aria-busy="true">
            <USkeleton class="h-9 w-2/3" />
            <USkeleton v-for="i in 6" :key="i" class="h-4 w-full" />
          </div>
          <UEmpty
            v-else-if="failed"
            icon="i-lucide-file-question"
            :title="t('This page cannot be shown')"
            :description="docName"
            :actions="[{ label: t('Documentation'), icon: 'i-lucide-book-open', to: '/docs', color: 'neutral', variant: 'subtle' }]"
            variant="naked"
          />
          <template v-else>
            <UAlert
              v-if="docName === 'User Guide.md'"
              class="mb-8 max-w-[46rem]"
              icon="i-lucide-map"
              color="neutral"
              variant="subtle"
              :title="t('This guide describes the classic interface')"
            >
              <template #description>
                <span>{{ t('In this interface:') }}</span>
                <span v-for="([classic, now], i) in classicNames" :key="classic">{{ i ? ' · ' : ' ' }}{{ classic }} → <b class="font-medium text-highlighted">{{ now }}</b></span>
              </template>
            </UAlert>
            <!-- eslint-disable-next-line vue/no-v-html -->
            <div ref="el" class="rh-doc" @click="onClick" v-html="html" />
          </template>
        </article>

        <aside v-if="outline.length > 2" class="hidden xl:sticky xl:top-0 xl:block xl:self-start">
          <div class="mb-2 text-xs font-semibold uppercase tracking-wider text-dimmed">
            {{ t('On this page') }}
          </div>
          <ul class="max-h-[calc(100vh-10rem)] space-y-1 overflow-y-auto text-sm">
            <li v-for="h in outline" :key="h.id" :class="h.level === 3 ? 'ps-3' : ''">
              <a
                :href="`#${h.id}`"
                class="block truncate border-s-2 ps-2 transition-colors"
                :class="active === h.id ? 'border-primary font-medium text-highlighted' : 'border-transparent text-muted hover:text-highlighted'"
                :aria-current="active === h.id ? 'location' : undefined"
                @click.prevent="goSection(h.id)"
              >{{ h.text }}</a>
            </li>
          </ul>
        </aside>
      </div>
    </template>
  </UDashboardPanel>
</template>
