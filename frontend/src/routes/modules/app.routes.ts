import type { RouteRecordRaw, RouteLocationNormalizedLoaded } from "vue-router"
import AlertLayout from "@/layouts/AlertLayout.vue"

import HomeView from "@/views/app/HomeView.vue"

import MarketView from "@/views/app/market/index.vue"
import SymbolDetailView from "@/views/app/market/SymbolDetailView.vue"

import RulesView from "@/views/app/alert/RulesView.vue"
import ChannelsView from "@/views/app/alert/ChannelsView.vue"
import LogsView from "@/views/app/alert/LogsView.vue"

import SettingView from "@/views/app/SettingView.vue"
import ProfileView from "@/views/app/ProfileView.vue"

export const appRoutes: RouteRecordRaw[] = [
    {
        path: "", name: "Home", component: HomeView, meta: { allows: ["verified"], showBack: false, tab: "home" },
    },

    {
        path: "market", name: "Markets", component: MarketView, meta: { title: "마켓", allows: ["verified"], tab: "market", showBack: false },
    },
    {
        path: "market/:exchange/:symbol", name: "SymbolDetail", component: SymbolDetailView,
        meta: {
            title: (route: RouteLocationNormalizedLoaded) => `${route.params.symbol}/${route.params.exchange}`,
            allows: ["verified"],
            tab: "market",
            showBack: true,
            fallback: { name: 'Markets' }
        },
    },

    {
        path: "alert", name: "Alerts", component: AlertLayout, redirect: { name: "Rules" }, meta: { allows: ["verified"], tab: "alert" },
        children: [
            {
                path: "rules",
                name: "Rules",
                component: RulesView,
                meta: { title: "알림 규칙", allows: ["verified"], showBack: false, tab: "alert" },
            },
            {
                path: "channels",
                name: "Channels",
                component: ChannelsView,
                meta: { title: "알림 채널", allows: ["verified"], showBack: false, tab: "alert" },
            },
            {
                path: "logs",
                name: "Logs",
                component: LogsView,
                meta: { title: "알림 로그", allows: ["verified"], showBack: false, tab: "alert" },
            }
        ]
    },

    { path: "setting", name: "Settings", component: SettingView, meta: { title: "설정", allows: ["verified"], showBack: false, tab: "setting" }, },
    { path: "settings/profile", name: "Profile", component: ProfileView, meta: { allows: ["verified"], tab: "setting" } },

]
