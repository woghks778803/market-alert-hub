import { computed, onUnmounted, ref } from "vue";

export function useCooldown() {
    const cooldownSec = ref(0);
    let timer: number | null = null;

    const isCooldown = computed(() => cooldownSec.value > 0);

    function stop() {
        if (timer !== null) {
            window.clearInterval(timer);
            timer = null;
        }
        cooldownSec.value = 0;
    }

    function start(sec: number) {
        const s = Number.isFinite(sec) ? Math.max(0, Math.floor(sec)) : 0;
        cooldownSec.value = s;

        if (timer !== null) {
            window.clearInterval(timer);
            timer = null;
        }

        if (cooldownSec.value <= 0) return;

        timer = window.setInterval(() => {
            if (cooldownSec.value <= 1) {
                cooldownSec.value = 0;
                if (timer !== null) {
                    window.clearInterval(timer);
                    timer = null;
                }
                return;
            }
            cooldownSec.value -= 1;
        }, 1000);
    }

    onUnmounted(() => {
        if (timer !== null) {
            window.clearInterval(timer);
            timer = null;
        }
    });

    return {
        cooldownSec,
        isCooldown,
        startCooldown: start,
        stopCooldown: stop,
    };
}