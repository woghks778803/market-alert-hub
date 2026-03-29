import { createApp } from "vue"
import App from "./App.vue"
import { router } from "./routes"
import { vuetify } from "./plugins/vuetify"
import { createPinia } from "pinia"
import './styles/main.css'
import { wsClient } from "@/services/ws/ws.client"
import { marketWs } from "@/services/ws/market.ws"

marketWs.init()
wsClient.connect()

const pinia = createPinia()

createApp(App)
    .use(router)
    .use(vuetify)
    .use(pinia)
    .mount("#app")
