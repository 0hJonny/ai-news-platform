<script setup lang="ts">
import ThemeSwitcher from './ThemeSwitcher.vue'
import SideBar from './SideBar.vue'
import LanguageSwitcher from './LanguageSwitcher.vue'
</script>

<template>
  <header>
    <div class="header-container border-b-2">
      <nav class="header-container-nav header-text">
        <div class="header-left-side">
          <SideBar />
        </div>

        <div class="header-right-side flex gap-4 items-center">
          <LanguageSwitcher />
          <ThemeSwitcher />
        </div>
      </nav>
    </div>
  </header>
</template>

<style scoped>
.header-left-side {
  display: flex;
  align-items: center;
}

.header-right-side {
  display: flex;
  align-items: center;
}
</style>
