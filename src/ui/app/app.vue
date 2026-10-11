<script setup lang="ts">
const { refresh } = useAuth()
onMounted(refresh)
</script>

<template>
  <UApp :toaster="{ position: 'top-right', duration: 4000 }" :tooltip="{ delayDuration: 300 }">
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
  </UApp>
</template>
