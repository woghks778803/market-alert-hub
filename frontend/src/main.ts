import { createApp } from "vue"
import App from "./App.vue"
import { router } from "./routes"
import { vuetify } from "./plugins/vuetify"
import { createPinia } from "pinia"
import './styles/main.css'

const pinia = createPinia()

createApp(App)
    .use(router)
    .use(vuetify)
    .use(pinia)
    .mount("#app")
