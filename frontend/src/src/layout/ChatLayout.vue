<script setup lang="ts">
import Sidebar from '@/components/features/chat/SidebarChat.vue'
</script>

<template>
  <div class="chat-layout">
    <Sidebar />
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.chat-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background-color: var(--color-bkg);
}

.main-content {
  flex: 1;
  position: relative;
  display: flex;
  flex-direction: column;
  transition: margin-left 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
</style>
