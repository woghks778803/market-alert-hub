import type { RouteRecordRaw } from "vue-router"

import LoginView from "@/views/public/auth/LoginView.vue"
import ForgotPasswordView from "@/views/public/auth/ForgotPasswordView.vue"
import ResetPasswordView from "@/views/public/auth/ResetPasswordView.vue"

import RegisterSelectView from "@/views/public/auth/RegisterSelectView.vue"
import TermsConsentView from "@/views/public/auth/TermsConsentView.vue"
import RegisterEmailView from "@/views/public/auth/RegisterEmailView.vue"
import OauthFailView from "@/views/public/auth/OauthFailView.vue"
import VerifyEmailSentView from "@/views/public/auth/VerifyEmailSentView.vue"
import EmailVerifyView from "@/views/public/auth/EmailVerifyView.vue"
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
        meta: { allows: ["guest"] },
    },
    {
        path: "forgot-password",
        name: "ForgotPassword",
        component: ForgotPasswordView,
        meta: { allows: ["guest"] },
    },
    {
        path: "reset-password",
        name: "ResetPassword",
        component: ResetPasswordView,
        meta: { allows: ["guest"] },
    },

    // --- Auth: Sign up flow ---
    {
        path: "signup",
        name: "Signup",
        component: RegisterSelectView,
        meta: { allows: ["guest"] },
    },
    {
        path: "signup/terms",
        name: "SignupTerms",
        component: TermsConsentView,
        meta: { allows: ["guest"] },
    },
    {
        path: "signup/email",
        name: "SignupEmail",
        component: RegisterEmailView,
        meta: { allows: ["guest"] },
    },
    {
        path: "oauth/fail",
        name: "OauthFail",
        component: OauthFailView,
        meta: { allows: ["guest"] },
    },

    // --- Email verify callback (from email link) ---
    // 예: /verify-email?token=...
    {
        path: "verify-email",
        name: "VerifyEmail",
        component: EmailVerifyView,
        meta: { allows: ["unenrolled"] },
    },
    {
        path: "verify-email-callback",
        name: "VerifyEmailCallback",
        component: EmailVerifyCallbackView,
        meta: {},
    },
    {
        path: "verify-sent",
        name: "VerifyEmailSent",
        component: VerifyEmailSentView,
        meta: { allows: ["unverified"] },
    },
]
