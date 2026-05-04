import { computed, ref } from 'vue'

export function useAsyncAction() {
  const loading = ref(false)

  const isReady = computed(() => !loading.value)

  async function run<T>(fn: () => T | Promise<T>) {
    if (loading.value) return null
    loading.value = true
    try {
      await fn()
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    isReady,
    run,
  }
}
