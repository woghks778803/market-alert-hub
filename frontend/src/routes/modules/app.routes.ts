import type { RouteRecordRaw } from "vue-router"
import HomeView from "@/views/app/HomeView.vue"
import MarketView from "@/views/app/MarketView.vue"
import AlertsView from "@/views/app/AlertsView.vue"
import SettingView from "@/views/app/SettingView.vue"
import ProfileView from "@/views/app/ProfileView.vue"

export const appRoutes: RouteRecordRaw[] = [
    { path: "", name: "Home", component: HomeView },

    { path: "market", name: "Market", component: MarketView },
    { path: "alerts", name: "Alerts", component: AlertsView },

    { path: "settings", name: "Settings", component: SettingView },
    { path: "settings/profile", name: "Profile", component: ProfileView },

]
