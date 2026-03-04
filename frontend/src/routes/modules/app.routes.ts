import type { RouteRecordRaw } from "vue-router"
import HomeView from "@/views/app/HomeView.vue"
import MarketView from "@/views/app/MarketView.vue"
import AlertsView from "@/views/app/AlertsView.vue"
import SettingView from "@/views/app/SettingView.vue"
import ProfileView from "@/views/app/ProfileView.vue"

export const appRoutes: RouteRecordRaw[] = [
    { path: "", name: "Home", component: HomeView, meta: { allows: ["verified"] }, },

    { path: "market", name: "Market", component: MarketView, meta: { allows: ["verified"] }, },
    { path: "alerts", name: "Alerts", component: AlertsView, meta: { allows: ["verified"] }, },

    { path: "settings", name: "Settings", component: SettingView, meta: { allows: ["verified"] }, },
    { path: "settings/profile", name: "Profile", component: ProfileView, meta: { allows: ["verified"] } },

]
