import type { RouteRecordRaw, RouteLocationNormalizedLoaded } from "vue-router"
import AlertLayout from "@/layouts/AlertLayout.vue"

import HomeView from "@/views/app/home/HomeView.vue"

import MarketView from "@/views/app/market/IndexView.vue"
import SymbolDetailView from "@/views/app/market/SymbolDetailView.vue"

import RulesView from "@/views/app/alert/RulesView.vue"
// import ChannelsView from "@/views/app/alert/ChannelsView.vue"
import LogsView from "@/views/app/alert/LogsView.vue"

import MoreView from "@/views/app/more/MoreView.vue"
import AppSettingView from "@/views/app/more/AppSettingView.vue"
import ProfileView from "@/views/app/user/ProfileView.vue"


export const appRoutes: RouteRecordRaw[] = [
    {
        path: "", name: "Home", component: HomeView, meta: { title: "홈", allows: ["verified"], showBack: false, tab: "home" },
    },

    {
        path: "market", name: "Markets", component: MarketView, meta: { title: "마켓", allows: ["verified"], showBack: false, tab: "market" },
    },
    {
        path: "market/:exchange/:symbol", name: "SymbolDetail", component: SymbolDetailView,
        meta: {
            title: (route: RouteLocationNormalizedLoaded) => `${route.params.symbol}/${route.params.exchange}`,
            allows: ["verified"],
            showBack: true,
            tab: "market",
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
            // {
            //     path: "channels",
            //     name: "Channels",
            //     component: ChannelsView,
            //     meta: { title: "알림 채널", allows: ["verified"], showBack: false, tab: "alert" },
            // },
            {
                path: "logs",
                name: "Logs",
                component: LogsView,
                meta: { title: "알림 로그", allows: ["verified"], showBack: false, tab: "alert" },
            }
        ]
    },

    { path: "more", name: "More", component: MoreView, meta: { title: "더보기", allows: ["verified"], showBack: false, tab: "more" }, },
    { path: "more/setting/app", name: "AppSetting", component: AppSettingView, meta: { title: "앱 설정", allows: ["verified"], showBack: true, tab: "more" }, },
    { path: "user", name: "Profile", component: ProfileView, meta: { title: "내정보", allows: ["verified"], showBack: true, tab: "more" } },
]
