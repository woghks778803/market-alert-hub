import { computed, ref, watch } from "vue"

// const g = globalThis as any;
// g.__termsConsentLoadCount = (g.__termsConsentLoadCount ?? 0) + 1;
// export const __termsConsentInstanceId =
//     g.__termsConsentInstanceId ?? (g.__termsConsentInstanceId = Math.random().toString(16).slice(2));

// console.log("[useTermsConsent] loadCount=", g.__termsConsentLoadCount, "id=", __termsConsentInstanceId);

const STORAGE_KEY = "signup_terms_consent";
// individual
const agreeService = ref(false); // (필수)
const agreePrivacy = ref(false); // (필수)
const agreeMarketing = ref(false); // (선택)
const allChecked = ref(false);
let isRestoring = true;

const canProceed = computed(() => agreeService.value && agreePrivacy.value)
const consentPayload = computed(() => ({
    agreeService: agreeService.value,
    agreePrivacy: agreePrivacy.value,
    agreeMarketing: agreeMarketing.value,
}));

console.log("useTermsConsent initialized", {
    agreeService: agreeService.value,
    agreePrivacy: agreePrivacy.value,
    agreeMarketing: agreeMarketing.value,
    allChecked: allChecked.value,
});

/**
 * 🔹 최초 로드 시 sessionStorage에서 복구
 */
(function restore() {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) {
        isRestoring = false;
        return;
    }

    try {
        const parsed = JSON.parse(raw);
        agreeService.value = !!parsed.agree_service;
        agreePrivacy.value = !!parsed.agree_privacy;
        agreeMarketing.value = !!parsed.agree_marketing;

        allChecked.value =
            agreeService.value &&
            agreePrivacy.value &&
            agreeMarketing.value;



        console.log("useTermsConsent restored from sessionStorage", {
            agreeService: agreeService.value,
            agreePrivacy: agreePrivacy.value,
            agreeMarketing: agreeMarketing.value,
            allChecked: allChecked.value,
        });

    } catch {
        sessionStorage.removeItem(STORAGE_KEY);
    } finally {
        isRestoring = false;
    }
})();

/**
 * 🔹 값 변경 시 자동 저장
 */
function persistNow() {
    sessionStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
            agree_service: agreeService.value,
            agree_privacy: agreePrivacy.value,
            agree_marketing: agreeMarketing.value,
        })
    );
}

watch(
    [agreeService, agreePrivacy, agreeMarketing],
    () => {
        if (isRestoring) return;
        if (!canProceed.value) {
            sessionStorage.removeItem(STORAGE_KEY);
            return;
        }
        persistNow();
    },
    { deep: false }
);


function toggleAll(v: boolean | null) {
    allChecked.value = v === true
    agreeService.value = allChecked.value
    agreePrivacy.value = allChecked.value
    agreeMarketing.value = allChecked.value
};

function resetTermsConsent() {
    agreeService.value = false;
    agreePrivacy.value = false;
    agreeMarketing.value = false;
    allChecked.value = false;

    // queueMicrotask(() => {
    //     canPersist = true;
    // });
};

function syncAllChecked() {
    allChecked.value = agreeService.value && agreePrivacy.value && agreeMarketing.value
};

export function useTermsConsent() {
    return {
        agreeService,
        agreePrivacy,
        agreeMarketing,
        allChecked,

        canProceed,
        consentPayload,

        toggleAll,
        syncAllChecked,
        resetTermsConsent
    }
};
