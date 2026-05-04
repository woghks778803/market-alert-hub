import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import { router } from '@/routes'
import { vuetify } from '@/plugins/vuetify'
import { createToastPlugin } from '@/plugins/toast.plugin'
import { createAuthPlugin } from '@/plugins/auth.plugin'
import { wsClient } from '@/services/ws/ws.client'
import { marketWs } from '@/services/ws/market.ws'
import { useAppSettings } from '@/composables/common/useAppSettings'
import '@/styles/main.css'

const settings = useAppSettings()
const pinia = createPinia()

settings.initAppSettings()
marketWs.init()
wsClient.connect()

createApp(App)
  .use(router)
  .use(vuetify)
  .use(pinia)
  .use(createToastPlugin())
  .use(createAuthPlugin(pinia))
  .mount('#app')
