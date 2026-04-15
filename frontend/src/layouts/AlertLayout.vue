<template>
<div class="app-container alert-layout">
    <v-tabs
    class="alert-tabs"
        grow>
    
      <v-tab :to="{ name: 'Rules' }">
        규칙
      </v-tab>

      <v-tab :to="{ name: 'Archives' }">
        보관
      </v-tab>
    
      <v-tab :to="{ name: 'Logs' }">
        기록
      </v-tab>
    
    </v-tabs>
</div>

<router-view />

</template>