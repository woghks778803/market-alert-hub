import type { RouteRecordRaw } from "vue-router"

export const legalRoutes: RouteRecordRaw[] = [
    { path: "", redirect: { name: "NotFound" } },
]