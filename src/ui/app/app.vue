<script setup lang="ts">
const { refresh } = useAuth()
onMounted(refresh)

// Toasts never cover the race controls: bottom right on wider screens (above the
// notification bell), top centre on phones (clear of the sticky race bar at the bottom).
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
  : { position: 'top-center' as const, duration: 4000 })
</script>

<template>
  <UApp :toaster="toaster" :tooltip="{ delayDuration: 300 }">
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
  </UApp>
</template>
