import { ref } from "vue"

export type EmailVerifyMode = "processing" | "success" | "fail"

export function useEmailVerifyCallback() {
    const mode = ref<EmailVerifyMode>("processing")
    const running = ref(false)

    function setMode(next: EmailVerifyMode) {
        mode.value = next
    }

    async function runVerify(run?: () => Promise<EmailVerifyMode | void> | EmailVerifyMode | void) {
        if (running.value) return
        running.value = true
        mode.value = "processing"
        try {
            const result = await run?.()
            if (result === "success" || result === "fail" || result === "processing") {
                mode.value = result
            }
        } catch {
            mode.value = "fail"
        } finally {
            running.value = false
        }
    }

    return {
        mode,
        running,
        setMode,
        runVerify,
    }
}
