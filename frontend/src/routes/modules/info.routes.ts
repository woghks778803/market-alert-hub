import type { RouteRecordRaw } from "vue-router"

export const infoRoutes: RouteRecordRaw[] = [
    { path: "", redirect: { name: "NotFound" } },
]