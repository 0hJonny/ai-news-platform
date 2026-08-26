<script setup lang="ts">
import { SOCIAL_MEDIA_URLS } from '@/shared/socialLink'

const currentYear = new Date().getFullYear()

const socialLinks = [
  { name: 'Github', url: SOCIAL_MEDIA_URLS.Github, icon: 'Github' },
  { name: 'Telegram', url: SOCIAL_MEDIA_URLS.Telegram, icon: 'Telegram' },
]
</script>

<template>
  <footer class="footer">
    <div class="footer__container">
      <div class="footer__section">
        <h3 class="footer__title">{{ $t('footer.about') }}</h3>
        <p class="footer__text">{{ $t('footer.description') }}</p>
      </div>

      <div class="footer__section">
        <h3 class="footer__title">{{ $t('footer.links') }}</h3>
        <ul class="footer__links">
          <li>
            <router-link to="/about">{{ $t('footer.aboutUs') }}</router-link>
          </li>
          <li>
            <router-link to="/contact">{{ $t('footer.contact') }}</router-link>
          </li>
          <li>
            <router-link to="/privacy">{{ $t('footer.privacy') }}</router-link>
          </li>
        </ul>
      </div>

      <div class="footer__section">
        <h3 class="footer__title">{{ $t('footer.social') }}</h3>
        <div class="footer__social">
          <a
            v-for="link in socialLinks"
            :key="link.name"
            :href="link.url"
            :aria-label="link.name"
            class="footer__social-link"
          >
            {{ link.name }}
          </a>
        </div>
      </div>
    </div>

    <div class="footer__bottom">
      <p>&copy; {{ currentYear }} {{ $t('footer.copyright') }}</p>
    </div>
  </footer>
</template>

<style scoped>
.footer {
  background: var(--color-bkg);
  color: var(--color-text-primary);
  margin-top: auto;
  border-top: 1px solid var(--color-divider-light);
  transition: var(--transition);
}

.footer__container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 3rem 1.5rem;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
}

.footer__title {
  margin-bottom: 1rem;
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--color-text-primary);
}

.footer__text {
  color: var(--color-text-sub);
  line-height: 1.6;
}

.footer__links {
  list-style: none;
  padding: 0;
}

.footer__links li {
  margin-bottom: 0.5rem;
}

.footer__links a {
  color: var(--color-text-sub);
  text-decoration: none;
  transition: color 0.2s ease;
}

.footer__links a:hover {
  color: var(--color-text-title);
  text-decoration: underline;
}

.footer__social {
  display: flex;
  gap: 1rem;
}

.footer__social-link {
  color: var(--color-text-sub);
  text-decoration: none;
  transition: color 0.2s ease;
}

.footer__social-link:hover {
  color: var(--color-text-title);
  text-decoration: underline;
}

.footer__bottom {
  border-top: 1px solid var(--color-divider-light);
  padding: 1.5rem;
  text-align: center;
  color: var(--color-text-sub);
}
</style>
