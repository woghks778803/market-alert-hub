<template>
    <AppLoading :show="postAction.loading.value" overlay />

    <v-container fluid class="app-container">
        <div class="news-post-page">
            <section class="news-post-search">
                <v-text-field
                    :model-value="newsPostListQuery.search"
                    @update:model-value="newsStore.setSearch"
                    placeholder="피드 검색"
                    prepend-inner-icon="mdi-magnify"
                    variant="solo"
                    density="comfortable"
                    rounded="lg"
                    hide-details
                    clearable
                    flat
                />
            </section>
            
            <section class="news-post-header">
                <div class="news-post-title">
                    주요 시장 소식을 빠르게 확인하세요
                </div>

                <div class="news-post-meta">
                    최근 48시간 · {{ POSTS_MAX_LIMIT }}개
                </div>
            </section>
            
                <div v-if="!initialLoaded" class="alert-list-loading">
                    불러오는 중...
                </div>
                
            <v-infinite-scroll
                :key="currentNewsPostListKey"
                class="news-post-list"
                :disabled="!newsHasMore || newsLoadingMore"
                @load="handleLoadMore"
            >
                <PostCard
                    v-for="post in newsPosts"
                    :key="post.newsItemId"
                    :post="post"
                />

                <template #loading>
                    <div class="news-post-list-loading">
                        불러오는 중...
                    </div>
                </template>

                <template #empty>
                    <div class="news-post-list-empty">
                        더 이상 표시할 피드가 없습니다.
                    </div>
                </template>
            </v-infinite-scroll>
        </div>
    </v-container>
</template>

<script setup lang="ts">
import { onMounted, onActivated, ref } from "vue"
import { storeToRefs } from "pinia"

import AppLoading from "@/components/common/AppLoading.vue"
import PostCard from "@/components/news/PostCard.vue"

import { useAsyncAction } from "@/composables/common/useAsyncAction"

import { POSTS_MAX_LIMIT } from "@/services/news.types"
import { useNewsStore } from "@/stores/news.store"

const newsStore = useNewsStore()
const { 
    newsPosts, 
    newsHasMore, 
    newsLoadingMore, 
    newsPostListQuery, 
    currentNewsPostListKey 
} = storeToRefs(newsStore)
const postAction = useAsyncAction()

const initialLoaded = ref(false)

onMounted(async () => {
    newsStore.resetNews()
    
    await postAction.run(async () => {
        await newsStore.fetchNewsPosts()
    })

    initialLoaded.value = true
})

onActivated(async () => {
})

const handleLoadMore = async ({ done }: { done: (status: "ok" | "empty" | "error") => void }) => {
    if (!initialLoaded.value) {
        done("ok")
        return
    }

    if (!newsHasMore.value) {
        done("empty")
        return
    }

    try {
        console.log("handleLoadMore")
        await newsStore.fetchNewsPosts({ append: true })

        done(newsHasMore.value ? "ok" : "empty")
    } catch {
        done("error")
    }
}

</script>