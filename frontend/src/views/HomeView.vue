<script setup lang="ts">
import { ref } from 'vue'
const api = ref('pending...')
const admin = ref('pending...')
async function ping() {
  try {
    const r1 = await fetch('/api/healthz')
    api.value = await r1.text()
  } catch (e:any) { api.value = 'error: ' + e?.message }
  try {
    const r2 = await fetch('/admin-api/healthz', { headers: { 'x-admin': 'true' } })
    admin.value = await r2.text()
  } catch (e:any) { admin.value = 'error: ' + e?.message }
}
</script>

<template>
  <section style="padding:24px">
    <h1>Market Alert Hub</h1>
    <button @click="ping">Ping API</button>
    <pre style="margin-top:12px">/api/healthz → {{ api }}</pre>
    <pre>/admin-api/healthz → {{ admin }}</pre>
  </section>
</template>
