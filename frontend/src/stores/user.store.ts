import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { getMe, type MeDto } from "@/services/user.service";

export const useUserStore = defineStore("user", () => {
    const me = ref<MeDto | null>(null);

    const email = computed(() => me.value?.email ?? null);

    async function fetchMeAction() {
        me.value = await getMe();
    }

    function clearMe() {
        me.value = null;
    }

    return { me, email, fetchMeAction, clearMe };
});