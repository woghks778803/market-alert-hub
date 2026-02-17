import type { RouteRecordRaw } from "vue-router"
import NotFoundView from "@/views/system/NotFoundView.vue"

export const systemRoutes: RouteRecordRaw[] = [
    // 번외: oauth callback, email verify landing 등이 필요하면 여기에
    // {
    //   path: "/oauth/callback/kakao",
    //   name: "oauth.kakao.callback",
    //   component: () => import("@/views/system/KakaoCallbackView.vue"),
    // },

    // 404
    {
        path: "/:pathMatch(.*)*",
        name: "NotFound",
        component: NotFoundView,
        meta: { requiresAuth: false, guestOnly: false },
    },
]
