import { createApp } from "vue"
import { createPinia } from "pinia"
import 'vue3-toastify/dist/index.css'

import '@/styles/main.css'
import App from "./App.vue"
import { router } from "@/routes"
import { vuetify } from "@/plugins/vuetify"
import { wsClient } from "@/services/ws/ws.client"
import { marketWs } from "@/services/ws/market.ws"
import { useAppSettings } from "@/composables/common/useAppSettings"

const settings = useAppSettings()
const pinia = createPinia()

settings.initAppSettings()
marketWs.init()
wsClient.connect()

createApp(App)
    .use(router)
    .use(vuetify)
    .use(pinia)
    .mount("#app")
