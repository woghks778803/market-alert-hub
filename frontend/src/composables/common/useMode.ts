import { ref } from "vue"

export type RenderMode = "default" | "success" | "fail"

export function useMode() {
    const mode = ref<RenderMode>("default")

    function setMode(next: RenderMode) {
        mode.value = next
    }

    return {
        mode,
        setMode,
    }
}
