<template>
  <v-container class="support-page">
    <div class="mb-6">
      <h1 class="text-h6 font-weight-bold mb-1">
        무엇을 도와드릴까요?
      </h1>

      <p class="text-body-2 text-medium-emphasis mb-0">
        자주 묻는 질문과 공지사항을 확인하거나 문의를 남겨주세요.
      </p>
    </div>

    <v-card
      variant="outlined"
      rounded="lg"
      class="support-link-card mb-3"
    >
      <v-list-item
        :to="{ name: 'Notice' }"
        min-height="78"
        append-icon="mdi-chevron-right"
      >
        <template #prepend>
          <v-avatar
            color="surface-variant"
            rounded="lg"
            size="44"
            class="mr-4"
          >
            <v-icon>
              mdi-bullhorn-outline
            </v-icon>
          </v-avatar>
        </template>

        <v-list-item-title class="font-weight-bold mb-1">
          공지사항
        </v-list-item-title>

        <v-list-item-subtitle>
          서비스 업데이트와 주요 안내를 확인할 수 있습니다.
        </v-list-item-subtitle>
      </v-list-item>
    </v-card>

    <v-card
      variant="outlined"
      rounded="lg"
      class="support-link-card"
    >
      <v-list-item
        :to="{ name: 'FAQ' }"
        min-height="78"
        append-icon="mdi-chevron-right"
      >
        <template #prepend>
          <v-avatar
            color="surface-variant"
            rounded="lg"
            size="44"
            class="mr-4"
          >
            <v-icon>
              mdi-help-circle-outline
            </v-icon>
          </v-avatar>
        </template>

        <v-list-item-title class="font-weight-bold mb-1">
          자주 묻는 질문
        </v-list-item-title>

        <v-list-item-subtitle>
          서비스 이용 중 자주 발생하는 궁금증을 확인해 보세요.
        </v-list-item-subtitle>
      </v-list-item>
    </v-card>

    <div class="text-subtitle-2 font-weight-bold mt-7 mb-3">
      문의하기
    </div>

    <v-card
      variant="outlined"
      rounded="lg"
      class="mb-3"
    >
      <v-card-item>
        <template #prepend>
          <v-avatar
            rounded="lg"
            size="44"
            class="mr-4"
            color="kakao"
          >
            <v-icon>
              mdi-chat-processing-outline
            </v-icon>
          </v-avatar>
        </template>

        <v-card-title class="text-subtitle-1 font-weight-bold">
          카카오톡 1:1 문의
        </v-card-title>

        <v-card-subtitle>
          이용 방법, 오류 신고 및 일반 문의
        </v-card-subtitle>

        <template #append>
          <v-chip
            size="x-small"
            color="warning"
            variant="tonal"
            class="font-weight-bold"
          >
            권장
          </v-chip>
        </template>
      </v-card-item>

      <v-card-text class="pt-1 text-body-2 text-medium-emphasis">
        빠른 확인이 필요한 문의는 카카오톡 채널을 이용해 주세요.
      </v-card-text>

      <v-card-actions class="px-4 pb-4 pt-0">
        <v-btn
          block
          variant="flat"
          class="support-kakao-button"
          color="kakao"
          href="https://pf.kakao.com/_nxmqPX"
        >
          카카오톡으로 문의하기
        </v-btn>
      </v-card-actions>
    </v-card>

    <v-card
      variant="outlined"
      rounded="lg"
    >
      <v-card-item>
        <template #prepend>
          <v-avatar
            color="surface-variant"
            rounded="lg"
            size="44"
            class="mr-4"
          >
            <v-icon>
              mdi-email-outline
            </v-icon>
          </v-avatar>
        </template>

        <v-card-title class="text-subtitle-1 font-weight-bold">
          이메일 문의
        </v-card-title>

        <v-card-subtitle>
          개인정보, 약관 및 서비스 운영 관련 문의
        </v-card-subtitle>
      </v-card-item>

      <v-card-text class="pt-1">
        <a
          class="support-email"
          href="mailto:support@alertping.site"
        >
          support@alertping.site
        </a>

        <p class="text-caption text-medium-emphasis mt-3 mb-0">
          이메일은 접수 및 확인 용도로 운영됩니다. 일반 문의는 카카오톡
          채널을 이용해 주세요.
        </p>
      </v-card-text>
    </v-card>

    <v-alert
      type="info"
      variant="tonal"
      density="compact"
      rounded="lg"
      class="mt-5"
      color="primary"
    >
      오류 문의 시 문제가 발생한 화면, 시간, 상황과 함께 화면 캡처를
      보내주시면 확인에 도움이 됩니다.
    </v-alert>
  </v-container>
</template>
