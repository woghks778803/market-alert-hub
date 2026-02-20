import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router"

import PublicLayout from "@/layouts/PublicLayout.vue"
import AppLayout from "@/layouts/AppLayout.vue"

import { authRoutes } from "@/routes/modules/auth.routes"
import { legalRoutes } from "@/routes/modules/legal.routes"
import { infoRoutes } from "@/routes/modules/info.routes"
import { appRoutes } from "@/routes/modules/app.routes"
import { systemRoutes } from "@/routes/modules/system.routes"
import { getAccessToken, clearAccessToken } from "@/api/http";
import { isTokenExpired, isEmailVerifiedFromToken } from "@/utils/jwt"

// NOTE: 여긴 "조립"만 한다.
// - 레이아웃(공개/앱) 트리 만들고
// - children은 modules에서 가져온다.
const routes: RouteRecordRaw[] = [
  {
    path: "/auth",
    component: PublicLayout,
    children: authRoutes,
  },
  {
    path: "/legal",
    component: PublicLayout,
    children: legalRoutes,
  },
  {
    path: "/info",
    component: PublicLayout,
    children: infoRoutes,
  },
  {
    path: "/",
    component: AppLayout,
    meta: { requiresAuth: true }, // AppLayout 아래는 기본적으로 로그인 필요
    children: appRoutes,
  },
  ...systemRoutes,
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})

// --- Global Guard (JWT 기반 최소 가드) ---
router.beforeEach((to, _from, next) => {
  const token = getAccessToken()
  const requiresAuth = Boolean(to.meta.requiresAuth)
  const requiresVerified = Boolean(to.meta.requiresVerified)
  const requiresUnverified = Boolean(to.meta.requiresUnverified)
  const guestOnly = Boolean(to.meta.guestOnly)
  console.log("Global Guard:", { to: to.fullPath, requiresAuth, requiresVerified, requiresUnverified, guestOnly, hasToken: Boolean(token) })

  if (token && isTokenExpired(token)) {
    clearAccessToken()

    if (requiresAuth || requiresVerified) {
      return next({ name: "Login", query: { next: to.fullPath } })
    }

    return next()
  }

  // 로그인 필요 페이지인데 토큰 없으면 로그인으로
  if (requiresAuth) {
    if (!token) {
      return next({ name: "Login", query: { next: to.fullPath } })
    }
  }

  // 이메일 인증 필요(UX) 페이지
  if (requiresVerified) {
    if (!token) {
      return next({ name: "Login", query: { next: to.fullPath } })
    }
    if (!isEmailVerifiedFromToken(token)) {
      return next({ name: "VerifyEmailSent", query: { next: to.fullPath } })
    }
  }

  if (requiresUnverified) {
    if (!token) {
      return next({ name: "Login", query: { next: to.fullPath } })
    }
    if (isEmailVerifiedFromToken(token)) {
      return next({ name: "Home" })
    }
  }

  if (guestOnly && token) {
    if (isEmailVerifiedFromToken(token)) {
      return next({ name: "Home" })
    }
    return next({ name: "VerifyEmailSent" })
  }

  return next()
})
