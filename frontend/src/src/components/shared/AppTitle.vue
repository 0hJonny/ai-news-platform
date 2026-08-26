<script setup lang="ts">
const props = defineProps<{
  titleHeader: string
}>()
</script>

<template>
  <div class="title-header border-b-2 mb-8">
    <h1 class="w-full text-center text-9xl uppercase font-bold pb-2">
      {{ props.titleHeader }}
    </h1>
  </div>
</template>
