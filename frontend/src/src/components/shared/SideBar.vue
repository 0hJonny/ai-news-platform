<script setup lang="ts">
import { SOCIAL_MEDIA_URLS } from '@/shared/socialLink'
import type { SocialItem } from '@/types/shared/social'
import { ref, computed, watch, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'

interface MenuItem {
  id: string
  label: string
  link?: string
  children?: SubMenuItem[]
}

interface SubMenuItem {
  id: string
  label: string
  link: string
}

const { t } = useI18n()

const isMenuOpen = ref(false)

// Computed only for translations
const menuItems = computed<MenuItem[]>(() => [
  { id: 'home', label: t('sidebar.home'), link: '/' },
  { id: 'security', label: t('sidebar.security'), link: '/security' },
  { id: 'privacy', label: t('sidebar.privacy'), link: '/privacy' },
  { id: 'crypto', label: t('sidebar.crypto'), link: '/crypto' },
  { id: 'technology', label: t('sidebar.technology'), link: '/tech' },
  { id: 'search', label: t('sidebar.search'), link: '/search' },
  { id: 'about', label: t('sidebar.about'), link: '/about' },
])

const SOCIAL_ITEMS: readonly SocialItem[] = Object.freeze([
  {
    id: 'telegram',
    title: 'Telegram',
    link: SOCIAL_MEDIA_URLS.Telegram,
    icon: '#telegram-h',
  },
  {
    id: 'github',
    title: 'Github',
    link: SOCIAL_MEDIA_URLS.Github,
    icon: '#github-h',
  },
])

const getScrollbarWidth = (): number => {
  const outer = document.createElement('div')
  outer.style.visibility = 'hidden'
  outer.style.overflow = 'scroll'
  document.body.appendChild(outer)

  const inner = document.createElement('div')
  outer.appendChild(inner)

  const scrollbarWidth = outer.offsetWidth - inner.offsetWidth
  document.body.removeChild(outer)

  return scrollbarWidth
}

const toggleMenu = (): void => {
  isMenuOpen.value = !isMenuOpen.value
}

const closeMenu = (): void => {
  isMenuOpen.value = false
}

// Lock body scrolling while the menu is open
watch(isMenuOpen, (newValue) => {
  if (newValue) {
    // Check whether scrollbar-gutter is supported
    const supportsScrollbarGutter = CSS.supports('scrollbar-gutter', 'stable')

    if (!supportsScrollbarGutter) {
      // Compute the scrollbar width and compensate for it
      const scrollbarWidth = getScrollbarWidth()
      document.body.style.paddingRight = `${scrollbarWidth}px`
    }

    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
    document.body.style.paddingRight = ''
  }
})

// Cleanup when the component is unmounted
onUnmounted(() => {
  document.body.style.overflow = ''
  document.body.style.paddingRight = ''
})
</script>

<template>
  <div>
    <!-- Menu open/close button -->
    <div>
      <button
        class="header__head-mobile-action"
        @click="toggleMenu"
        :aria-label="t('sidebar.toggleMenu')"
      >
        <!-- X -->
        <div>
          <svg
            stroke="currentColor"
            fill="currentColor"
            viewBox="0 0 50 50"
            width="24px"
            height="24px"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M 0 7.5 L 0 12.5 L 50 12.5 L 50 7.5 Z M 0 22.5 L 0 27.5 L 50 27.5 L 50 22.5 Z M 0 37.5 L 0 42.5 L 50 42.5 L 50 37.5 Z"
            />
          </svg>
        </div>
        <!-- <img class="theme-switcher-icon" style="fill: white" src="/menu.svg" alt="Menu" v-once /> -->
        <div class="menu__blog_text">{{ $t('sidebar.menu') }}</div>
      </button>
    </div>

    <!-- Menu -->
    <nav
      class="menu"
      :class="{ menu_opened: isMenuOpen, menu_closed: !isMenuOpen }"
      @keydown.esc="closeMenu"
      @click="closeMenu"
    >
      <div class="menu__bucket" @click.stop>
        <div class="menu__wrapper">
          <div class="menu__header">
            <button
              @click="closeMenu"
              class="menu__header-button-close"
              :aria-label="t('sidebar.closeMenu')"
              data-js-header-menu-close
              tabindex="0"
            >
              <!-- X -->
              <div class="theme-switcher-icon">
                <svg
                  viewBox="0 0 30 30"
                  width="24px"
                  height="24px"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    fill="var(--icon-color, currentColor)"
                    d="M 7 4 C 6.744125 4 6.4879687 4.0974687 6.2929688 4.2929688 L 4.2929688 6.2929688 C 3.9019687 6.6839688 3.9019687 7.3170313 4.2929688 7.7070312 L 11.585938 15 L 4.2929688 22.292969 C 3.9019687 22.683969 3.9019687 23.317031 4.2929688 23.707031 L 6.2929688 25.707031 C 6.6839688 26.098031 7.3170313 26.098031 7.7070312 25.707031 L 15 18.414062 L 22.292969 25.707031 C 22.682969 26.098031 23.317031 26.098031 23.707031 25.707031 L 25.707031 23.707031 C 26.098031 23.316031 26.098031 22.682969 25.707031 22.292969 L 18.414062 15 L 25.707031 7.7070312 C 26.098031 7.3170312 26.098031 6.6829688 25.707031 6.2929688 L 23.707031 4.2929688 C 23.316031 3.9019687 22.682969 3.9019687 22.292969 4.2929688 L 15 11.585938 L 7.7070312 4.2929688 C 7.5115312 4.0974687 7.255875 4 7 4 z"
                  />
                </svg>
              </div>
              <!-- <img
                class="theme-switcher-icon color-dynamic-bkg"
                src="/menu-close.svg"
                alt="Dark mode"
              /> -->
              <div class="menu__header-text">{{ $t('sidebar.menu') }}</div>
            </button>
          </div>
          <ul>
            <li
              v-for="menuItem in menuItems"
              :key="menuItem.id"
              :class="{
                menu__item: true,
                'menu__item-has-children': menuItem.children,
              }"
            >
              <input
                v-if="menuItem.children"
                :id="`header-nav-${menuItem.id}`"
                type="checkbox"
                class="menu__sub-items-toggle"
                aria-hidden="true"
                :data-js-header-toggle="`header-nav-${menuItem.id}`"
              />
              <label
                class="menu__item-link"
                v-if="menuItem.children"
                :for="`header-nav-${menuItem.id}`"
                tabindex="0"
              >
                <div class="menu__label">{{ menuItem.label }}</div>
                <svg class="svg-icon menu__icon" width="24" height="24" v-once>
                  <use xlink:href="#mdi-chevron-right"></use>
                </svg>
              </label>
              <a v-else class="menu__item-link" :href="menuItem.link" tabindex="0">
                <div class="menu__label">{{ menuItem.label }}</div>
              </a>
              <ul v-if="menuItem.children" class="menu__submenu">
                <li v-for="subItem in menuItem.children" :key="subItem.id">
                  <a class="menu__submenu-link" :href="subItem.link" tabindex="0">{{
                    subItem.label
                  }}</a>
                </li>
              </ul>
            </li>
          </ul>
          <div class="menu__divider"></div>
          <div class="menu__footer">
            <div class="menu__footer-social">
              <a
                v-for="socialItem in SOCIAL_ITEMS"
                :key="socialItem.id"
                class="menu__footer-social__icon-link"
                :href="socialItem.link"
                :title="socialItem.title"
                target="_blank"
                rel="noopener"
              >
                <svg
                  class="svg-icon menu__footer-social__icon lazyloaded"
                  width="24"
                  height="24"
                  v-once
                >
                  <use :xlink:href="socialItem.icon"></use>
                </svg>
              </a>
            </div>
            <p class="menu__footer-notes">
              {{ $t('sidebar.developedBy') }}
              <a :href="SOCIAL_MEDIA_URLS.Github" target="_blank" rel="noopener">0hJonny</a>
              {{ $t('sidebar.onGithub') }}.
            </p>
          </div>
        </div>
        <div data-js-header-overlay class="menu__overlay"></div>
      </div>
    </nav>
  </div>
</template>

<style scoped>
.menu {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: 100%;
  z-index: 10000;
  transition:
    transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1),
    background-color 0s ease,
    backdrop-filter 0s ease;
  background-color: rgba(var(--color-cover-bkg-rgb), 0);
  backdrop-filter: blur(0);
  cursor: pointer;
}

.menu.menu_opened {
  display: block;
  transform: translateX(0);
  background-color: rgba(var(--color-cover-bkg-rgb), 0.7);
  backdrop-filter: blur(5px);
  transition:
    transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1),
    background-color 0.3s ease,
    backdrop-filter 0.3s ease;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

.menu.menu_closed {
  visibility: hidden;
  cursor: default;
  transition:
    visibility 0.3s ease,
    transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.menu_overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0);
  backdrop-filter: blur(0);
  z-index: 9999;
  opacity: 0;
  transition: opacity 0.3s ease-in-out;
}

.menu.menu_opened + .menu_overlay {
  opacity: 1;
  transition: opacity 0.3s ease-in-out;
}

.menu__wrapper {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  margin: auto;
  max-width: min(30%, 100vw);
  background-color: var(--color-black); /* White menu background */
  /* padding: var(--space-m); */
  color: var(--color-white); /* White text */
  z-index: 10001; /* Place the menu above the translucent overlay */
  transform: translateX(-100%);
  transition: transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  overflow-y: scroll;
  -webkit-overflow-scrolling: touch;
  will-change: transform;
  cursor: default;
  scroll-behavior: smooth;
  scrollbar-width: none;
  padding-right: var(--space-m);
  padding-left: 112px;
}

.menu__wrapper::-webkit-scrollbar {
  display: none;
}

@media (max-width: 1079px) {
  .menu__wrapper {
    width: 100vw;
    max-width: 100vw;
    left: 0;
    transform: translateX(-100%);
  }
}

.menu.menu_opened .menu__wrapper {
  transform: translateX(0);
  transition: transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.menu__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-m); /* Bottom spacing */
}

.menu_opened .menu__header-button-close {
  display: flex;
}

.menu__header-button-close {
  margin-top: 30px;
  display: flex;
  width: fit-content;
  cursor: pointer;
  align-items: center;
  padding: var(--space-s) var(--space-m) var(--space-s) var(--space-s);
  border-radius: 25px; /* rounded corners */
}

@media (max-width: 1079px) {
  .menu__header-button-close {
    padding: var(--space-s);
  }
}

.menu__header-button-close:hover {
  background-color: var(--color-palette-dark);
}

.menu__header-text {
  font-size: var(--text-size-small); /* Heading text size */
  color: var(--color-white);
  margin-left: var(--space-xs);
  line-height: 160%;
}

@media (max-width: 1079px) {
  .menu__header-text {
    display: none;
  }
}

.menu__blog_text {
  font-size: var(--text-size-small); /* Heading text size */
  color: var(--color-text-primary);
  margin-left: var(--space-xs);
  line-height: 160%;
}

@media (max-width: 1079px) {
  .menu__blog_text {
    display: none;
  }
}

.menu__header-search {
  display: none;
}

@media (max-width: 1079px) {
  .menu__header-search {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    height: 120px;
    padding-bottom: 10px;
  }
}

.menu__item-link {
  position: relative;
  display: flex;
  height: 48px;
  padding: 0 var(--space-m) 0 var(--space-n);
  align-items: center;
  gap: var(--space-s);
  align-self: stretch;
  font-size: var(--text-size-regular);
  font-weight: 400;
  line-height: 24px;
  color: inherit; /* Use the text color from the parent element */
  text-decoration: none; /* Remove the underline from links */
}

.menu__item-link:hover {
  background-color: var(--color-palette-dark);
}

.menu__item-has-children .menu__item-link {
  justify-content: space-between;
  cursor: pointer;
}

.menu__submenu {
  display: none;
  padding-left: var(--space-m);
}

.menu__item-has-children input[type='checkbox']:checked ~ .menu__submenu {
  display: block; /* Show the nested submenu when the parent item is selected */
}

.menu__item-has-children input[type='checkbox'] {
  position: absolute;
  visibility: hidden; /* or opacity: 0; */
}

.menu__footer {
  display: flex;
  flex-direction: column;
  gap: var(--space-m);
  padding: var(--space-m) var(--space-n);
}

.menu__footer-social {
  display: flex;
  gap: var(--space-m);
}

.menu__footer-notes {
  color: var(--color-palette-silver);
  font-size: var(--text-size-tiny);
  font-weight: 400;
  line-height: 160%;
  padding: var(--header-padding);
}

.menu__footer-notes > .link-ref {
  color: var(--color-palette-silver);
  background-color: unset;
}

.header__burger {
  display: flex;
  cursor: pointer;
}

.header__head-mobile-action {
  display: inline-flex;
  width: fit-content;
  cursor: pointer;
  align-items: center;
  padding: var(--space-s) var(--space-m) var(--space-s) var(--space-s);
  padding-right: 16px;
  border-radius: 25px;
}

@media (max-width: 1079px) {
  .header__head-mobile-action {
    padding: var(--space-s);
  }
}

.header__head-mobile-action:hover {
  background-color: var(--color-palette-dark-dynamic);
}

.svg-icon-black {
  fill: var(--color-black);
}

.svg-icon-white {
  fill: var(--color-white);
}

.color-dynamic-bkg {
  fill: var(--color-text-primary);
}
</style>
