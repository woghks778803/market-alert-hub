import type { RouteRecordRaw } from "vue-router"
import HomeView from "@/views/app/HomeView.vue"
import MarketView from "@/views/app/MarketView.vue"
import AlertsView from "@/views/app/AlertsView.vue"
import SettingView from "@/views/app/SettingView.vue"
import ProfileView from "@/views/app/ProfileView.vue"

export const appRoutes: RouteRecordRaw[] = [
    { path: "", name: "Home", component: HomeView, meta: { requiresAuth: true, requiresVerified: true }, },

    { path: "market", name: "Market", component: MarketView, meta: { requiresAuth: true, requiresVerified: true }, },
    { path: "alerts", name: "Alerts", component: AlertsView, meta: { requiresAuth: true, requiresVerified: true }, },

    { path: "settings", name: "Settings", component: SettingView, meta: { requiresAuth: true, requiresVerified: true }, },
    { path: "settings/profile", name: "Profile", component: ProfileView, meta: { requiresAuth: true, requiresVerified: true } },

]
