import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';

export function usePageMeta() {
    const route = useRoute();
    const router = useRouter();

    const title = computed(() => {
        const t = route.meta.title;
        return typeof t === "function" ? t(route) : t ?? "";
    });

    const hideHeader = computed(() => route.meta.hideHeader === true);
    const showBack = computed(() => route.meta.showBack === true);

    const goBack = () => {
        if (window.history.state?.back) {
            router.back();
        } else {
            const fallback = route.meta.fallback as string || '/';
            router.push(fallback);
        }
    };

    return { title, showBack, hideHeader, goBack };
}