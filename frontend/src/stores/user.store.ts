import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { getMe, type MeDto } from "@/services/user.service";

export const useUserStore = defineStore("user", () => {
    const me = ref<MeDto | null>(null);

    const loading = ref({
        fetchMe: false,
    });

    const email = computed(() => me.value?.email ?? null);

    async function fetchMe() {
        loading.value.fetchMe = true;
        try {
            me.value = await getMe();
        } finally {
            loading.value.fetchMe = false;
        }
    }

    function clearMe() {
        me.value = null;
    }

    return { me, email, loading, fetchMe, clearMe };
});