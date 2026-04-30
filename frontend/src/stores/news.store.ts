import { defineStore } from "pinia"
import { ref, computed } from "vue"
import * as newsService from "@/services/news.service"
import type { NewsPostDto, NewsPostListQuery } from "@/services/news.types"
import { NewsPostSort, POSTS_MAX_LIMIT, POSTS_LIMIT } from "@/services/news.types"
import { } from "@/services/news.types"

export const useNewsStore = defineStore("news", () => {
    let searchTimer: any
    const newsPosts = ref<NewsPostDto[]>([])

    const newsHasMore = ref(true)
    const newsLoadingMore = ref(false)

    const newsPostListQuery = ref<NewsPostListQuery>({
        search: "",
        sort: NewsPostSort.RECENT_UPDATED,
        cursorAt: undefined,
        cursorId: undefined
    })

    const currentNewsPostListKey = ref<number>(0)

    async function fetchNewsPosts(options?: { append?: boolean }) {
        const append = options?.append ?? false

        if (newsLoadingMore.value) return
        if (append && !newsHasMore.value) return
        if (newsPosts.value.length >= POSTS_MAX_LIMIT) {
            newsHasMore.value = false
            return
        }

        newsLoadingMore.value = true

        try {
            newsPostListQuery.value.limit = POSTS_LIMIT

            if (!append) {
                currentNewsPostListKey.value += 1
                newsPosts.value = []
                newsHasMore.value = true
                newsPostListQuery.value.cursorAt = undefined
                newsPostListQuery.value.cursorId = undefined
            }

            const data = await newsService.getNewsPosts(newsPostListQuery.value)

            if (data.length === 0) {
                newsHasMore.value = false
                return
            }

            if (append) {
                newsPosts.value.push(...data)
            } else {
                newsPosts.value = data
            }

            if (data.length < POSTS_LIMIT || newsPosts.value.length >= POSTS_MAX_LIMIT) {
                newsHasMore.value = false
            }

            const last = newsPosts.value[newsPosts.value.length - 1]

            if (last) {
                newsPostListQuery.value.cursorAt = last.publishedAt
                newsPostListQuery.value.cursorId = last.newsItemId
            }

        } finally {
            newsLoadingMore.value = false
        }
    }

    function setSearch(value: string) {
        clearTimeout(searchTimer)

        searchTimer = setTimeout(() => {
            newsPostListQuery.value.search = value
            fetchNewsPosts()
        }, 500)
    }

    function resetNews() {
        newsPosts.value = []

        currentNewsPostListKey.value = 0
        newsHasMore.value = true
        newsLoadingMore.value = false
    }

    return {
        newsPosts,

        currentNewsPostListKey,
        newsHasMore,
        newsLoadingMore,

        newsPostListQuery,

        fetchNewsPosts,

        resetNews,
        setSearch,
    }
})