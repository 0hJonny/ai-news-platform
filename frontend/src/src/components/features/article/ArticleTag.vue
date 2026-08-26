<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  tag: string
}

const props = defineProps<Props>()

const tagStyles = [
  'tag-card-violet',
  'tag-card-gray',
  'tag-card-orange',
  'tag-card-green',
  'tag-card-red',
  'tag-card-yellow',
  'tag-card-blue',
  'tag-card-cyan',
  'tag-card-pink',
  'tag-card-teal',
] as const

const getStyleForTag = (tag: string): string => {
  let hash = 0
  for (let i = 0; i < tag.length; i++) {
    hash = tag.charCodeAt(i) + ((hash << 5) - hash)
  }
  const index = Math.abs(hash) % tagStyles.length
  const style = tagStyles[index]
  return style ?? 'tag-card-gray'
}

const tagStyle = computed(() => getStyleForTag(props.tag))

const formattedTag = computed(() => {
  return props.tag.charAt(0).toUpperCase() + props.tag.slice(1)
})
</script>

<template>
  <div
    class="cursor-pointer motion-reduce:transition-none motion-reduce:hover:transform-none duration-100 hover:scale-110"
  >
    <div :class="tagStyle">
      {{ formattedTag }}
    </div>
  </div>
</template>

<style lang="css" scoped></style>
