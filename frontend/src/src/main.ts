import './assets/main.css'
import './index.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import i18n from './plugins/i18n'
import { setupLocaleSync } from '@/plugins/locale-sync'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(i18n)

setupLocaleSync()

app.mount('#app')
