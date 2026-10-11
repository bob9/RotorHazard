<script setup lang="ts">
const { refresh } = useAuth()
const route = useRoute()
onMounted(refresh)

// Toasts never cover the navigation or the race controls: bottom right on wider screens
// (above the notification bell); bottom centre on phones, above the Race page's sticky bar.
const wide = ref(true)
let mq: MediaQueryList | undefined
const onMq = () => { wide.value = !!mq?.matches }
onMounted(() => {
  mq = window.matchMedia('(min-width: 1024px)')
  onMq()
  mq.addEventListener('change', onMq)
})
onBeforeUnmount(() => mq?.removeEventListener('change', onMq))
const toaster = computed(() => wide.value
  ? { position: 'bottom-right' as const, duration: 4000, ui: { viewport: 'bottom-20' } }
  : { position: 'bottom-center' as const, duration: 4000, ui: { viewport: route.path === '/' ? 'bottom-20' : '' } })
</script>

<template>
  <UApp :toaster="toaster" :tooltip="{ delayDuration: 300 }">
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
  </UApp>
</template>
