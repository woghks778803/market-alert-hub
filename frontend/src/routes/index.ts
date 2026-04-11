import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router"

import PublicLayout from "@/layouts/PublicLayout.vue"
import AppLayout from "@/layouts/AppLayout.vue"

import { authRoutes } from "@/routes/modules/auth.routes"
import { legalRoutes } from "@/routes/modules/legal.routes"
import { supportRoutes } from "@/routes/modules/support.routes"
import { appRoutes } from "@/routes/modules/app.routes"
import { systemRoutes } from "@/routes/modules/system.routes"
import type { StatusDto } from "@/services/auth.types"
import { useAuthStore } from "@/stores/auth.store"

// NOTE: 여긴 "조립"만 한다.
// - 레이아웃(공개/앱) 트리 만들고
// - children은 modules에서 가져온다.
const routes: RouteRecordRaw[] = [
  {
    path: "/auth",
    component: PublicLayout,
    children: authRoutes,
    meta: { hideHeader: true },
  },
  {
    path: "/legal",
    component: PublicLayout,
    children: legalRoutes,
    meta: { showBack: true },
  },
  {
    path: "/support",
    component: PublicLayout,
    children: supportRoutes,
    meta: { showBack: true },
  },
  {
    path: "/",
    component: AppLayout,
    children: appRoutes,
  },
  ...systemRoutes,
]

export const router = createRouter({
  history: createWebHistory(),
  routes,

  scrollBehavior(to, from, savedPosition) {
    // 뒤로가기/앞으로가기를 눌렀을 때는 원래 위치를 기억
    if (savedPosition) {
      return savedPosition
    } else {
      // 그 외에 새로운 페이지로 이동할 때는 맨 위
      return { top: 0 }
    }
  },
})

function getAuthState(status: StatusDto | null) {
  if (!status) return "guest"

  if (!status.emaileEnrolled) {
    return "unenrolled"
  }

  if (!status.emailVerified) {
    return "unverified"
  }

  return "verified"
}

let authBootstrapped = false
// --- Global Guard (JWT 기반 최소 가드) ---
router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()
  const allows = Array.isArray(to.meta.allows) ? to.meta.allows : []

  let status = authStore.getStatus()
  let authState = getAuthState(status)

  if (!authBootstrapped) {
    authBootstrapped = true
    try {
      status = await authStore.reissue()
      authState = getAuthState(status)
    } catch {
      authStore.clearStatus()
    }
  }

  console.log("Global Guard:", { to: to.fullPath, authState, allows, hasStatus: status })

  // if (token && isTokenExpired(token)) {
  // authStore.clearStatus()
  // }

  if (!allows || allows.length === 0) {
    return next()
  }

  if (!allows.includes(authState)) {
    if (authState == "guest")
      return next({ name: "Login", query: { next: to.fullPath } })
    else if (authState == "unenrolled")
      return next({ name: "VerifyEmail", query: { next: to.fullPath } })
    else if (authState == "unverified")
      return next({ name: "VerifyEmailSent", query: { next: to.fullPath } })
    else if (authState == "verified")
      return next({ name: "Home", query: { next: to.fullPath } })
  }

  return next()

})
