<script setup lang="ts">
import { ref, onMounted } from 'vue'

const isDark = ref(false)

const switchTheme = () => {
  isDark.value = !isDark.value

  if (isDark.value) {
    document.documentElement.classList.add('dark')
    localStorage.setItem('theme', 'dark')
  } else {
    document.documentElement.classList.remove('dark')
    localStorage.setItem('theme', 'light')
  }
}

onMounted(() => {
  const theme = localStorage.getItem('theme')
  isDark.value = theme === 'dark'

  if (isDark.value) {
    document.documentElement.classList.add('dark')
  }
})
</script>

<template>
  <div class="dark-switcher">
    <button
      @click="switchTheme"
      class="theme-switcher group"
      :class="{ 'dark-mode': isDark }"
      aria-label="Toggle theme"
    >
      <div class="switch-thumb" />
      <img class="icon" src="/moon.svg" alt="Dark mode" />
      <img class="icon" src="/sun.svg" alt="Light mode" />
    </button>
  </div>
</template>

<style scoped>
.theme-switcher {
  --switch-width: 3.5em;
  --switch-height: 1.8em;
  --thumb-size: 1.4em;

  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;

  width: var(--switch-width);
  height: var(--switch-height);

  padding: 0 0.3em;
  border-radius: 999px;

  cursor: pointer;
  background-color: var(--color-bkg-alt);
  transition: var(--transition);
}

.icon {
  width: 1em;
  height: 1em;
  z-index: 1;
}

.switch-thumb {
  position: absolute;
  top: 50%;
  left: 0.2em;

  width: var(--thumb-size);
  height: var(--thumb-size);

  background: var(--color-bkg);
  border-radius: 50%;

  transform: translate(0, -50%);
  transition:
    transform 0.3s ease,
    background 0.3s ease;
  z-index: 2;
}

.theme-switcher.dark-mode .switch-thumb {
  transform: translate(calc(var(--switch-width) - var(--thumb-size) - 0.4em), -50%);
  background: black;
}
</style>
