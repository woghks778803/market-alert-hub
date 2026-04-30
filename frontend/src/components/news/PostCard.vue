<template>
    <v-card class="news-post-card">
        <div class="news-post-card__top">
            <div class="news-post-source">
                <span class="news-post-source__dot"></span>
                {{ post.providerName }}
            </div>
    
            <div class="news-post-time">
                {{ formatDateTime(post.publishedAt) }}
            </div>
        </div>
    
        <div class="news-post-card__title">
            {{ post.title }}
        </div>
    
        <div class="news-post-card__original">
            {{ post.titleOriginal }}
        </div>
    
        <div class="news-post-card__bottom">
            <div class="news-post-tag">
                번역됨 · 원문 보기
            </div>

            <v-icon size="16" class="news-post-open-icon">
                mdi-open-in-new
            </v-icon>
        </div>
    </v-card>
</template>

<script setup lang="ts">
import type { NewsPostDto } from "@/services/news.types"
import { formatDateTime } from "@/utils/format"
const props = defineProps<{
  post: NewsPostDto
}>()

function openPost(item: any) {
    // TODO: 상세 또는 원문 링크 이동
}
</script>
