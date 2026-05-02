<template>
  <v-btn
    v-show="showScrollTop"
    class="scroll-top-button"
    :style="{ bottom: `${bottomOffset}px` }"
    icon
    size="large"
    color="deep-purple"
    @click="scrollToTop"
  >
    <v-icon>mdi-chevron-up</v-icon>
  </v-btn>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'

const props = withDefaults(
  defineProps<{
    bottomOffset?: number
    showAfter?: number
  }>(),
  {
    bottomOffset: 96,
    showAfter: 300,
  }
)

const showScrollTop = ref(false)

function onWindowScroll() {
  showScrollTop.value = window.scrollY > props.showAfter
}

function scrollToTop() {
  window.scrollTo({
    top: 0,
    behavior: 'smooth',
  })
}

onMounted(() => {
  window.addEventListener('scroll', onWindowScroll)
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', onWindowScroll)
})
</script>
