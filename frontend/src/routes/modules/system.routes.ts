import type { RouteRecordRaw } from "vue-router"
import NotFoundView from "@/views/system/NotFoundView.vue"

export const systemRoutes: RouteRecordRaw[] = [

    // 404
    {
        path: "/:pathMatch(.*)*",
        name: "NotFound",
        component: NotFoundView,
        meta: { allows: [], guestOnly: false },
    },
]
