import type { RouteRecordRaw } from "vue-router"

import LoginView from "@/views/public/auth/LoginView.vue"
import ForgotPasswordView from "@/views/public/auth/ForgotPasswordView.vue"
import ResetPasswordView from "@/views/public/auth/ResetPasswordView.vue"
import RegisterSelectView from "@/views/public/auth/RegisterSelectView.vue"
import TermsConsentView from "@/views/public/auth/TermsConsentView.vue"
import RegisterEmailView from "@/views/public/auth/RegisterEmailView.vue"
import VerifyEmailSentView from "@/views/public/auth/VerifyEmailSentView.vue"
import EmailVerifyCallbackView from "@/views/public/auth/EmailVerifyCallbackView.vue"

export const authRoutes: RouteRecordRaw[] = [
    // --- Auth: Login ---
    {
        path: "",
        redirect: { name: "Login" },
    },
    {
        path: "login",
        name: "Login",
        component: LoginView,
        meta: { requiresAuth: false, guestOnly: true },
    },
    {
        path: "forgot-password",
        name: "ForgotPassword",
        component: ForgotPasswordView,
        meta: { requiresAuth: false, guestOnly: true },
    },
    {
        path: "reset-password",
        name: "ResetPassword",
        component: ResetPasswordView,
        meta: { requiresAuth: false, guestOnly: true },
    },

    // --- Auth: Sign up flow ---
    {
        path: "signup",
        name: "Signup",
        component: RegisterSelectView,
        meta: { requiresAuth: false, guestOnly: true },
    },
    {
        path: "signup/terms",
        name: "SignupTerms",
        component: TermsConsentView,
        meta: { requiresAuth: false, guestOnly: true },
    },
    {
        path: "signup/email",
        name: "SignupEmail",
        component: RegisterEmailView,
        meta: { requiresAuth: false, guestOnly: true },
    },
    {
        path: "signup/verify-sent",
        name: "VerifyEmailSent",
        component: VerifyEmailSentView,
        meta: { requiresAuth: false, guestOnly: true },
    },

    // --- Email verify callback (from email link) ---
    // 예: /verify-email?token=...
    {
        path: "verify-email",
        name: "VerifyEmailCallback",
        component: EmailVerifyCallbackView,
        meta: { requiresAuth: false, guestOnly: true },
    },
]
