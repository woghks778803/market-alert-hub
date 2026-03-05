<template>
  <v-card rounded="lg" variant="flat">
    <v-card-title>내정보</v-card-title>
    <v-card-text>
      <v-list lines="two">
        <v-list-item title="닉네임" subtitle="-" />
        <v-list-item title="이메일" subtitle="-" />
        <v-list-item title="가입 방식" subtitle="Email / Kakao" />
      </v-list>

      <v-btn class="mt-3" block variant="tonal" :to="{ name: 'Settings' }">
        설정으로 돌아가기
      </v-btn>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts"></script>
