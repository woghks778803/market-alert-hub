import { ref } from "vue";
import { defineStore } from "pinia";
import type { UserDto, ChangeUserSettingQuery } from "@/services/user.types"
import * as userSevice from "@/services/user.service";

export const useUserStore = defineStore("user", () => {
    const me = ref<UserDto | null>(null);

    async function fetchMe(): Promise<void> {
        me.value = await userSevice.getMe();
    }

    async function changeMeSetting(payload: ChangeUserSettingQuery): Promise<void> {
        await userSevice.changeMeSetting(payload);
    }

    function setMarketing(value: boolean | null) {
        if (value == null || me.value == null) return

        const prev = me.value?.isMarketing
        me.value.isMarketing = value

        changeMeSetting({ isMarketing: value }).catch(() => {
            me.value!.isMarketing = prev
        })
    }

    function setQuietHours(value: boolean | null) {
        if (value == null || me.value == null) return

        const prev = me.value.isQuietHours
        me.value.isQuietHours = value

        changeMeSetting({ isQuietHours: value }).catch(() => {
            me.value!.isQuietHours = prev
        })
    }

    function clearMe() {
        me.value = null;
    }

    return {
        me,
        fetchMe,
        clearMe,
        changeMeSetting,

        setMarketing,
        setQuietHours

    };
});