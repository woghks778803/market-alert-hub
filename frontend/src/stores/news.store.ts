import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { NewsPostDto, NewsPostListQuery } from '@/services/news.types'
import { NewsPostSort, MAX_POSTS_LIMIT } from '@/services/news.types'
import * as newsService from '@/services/news.service'

export const useNewsStore = defineStore('news', () => {
  let searchTimer: ReturnType<typeof setTimeout> | null = null
  const newsPosts = ref<NewsPostDto[]>([])

  const currentNewsPostListKey = ref<number>(0)

  const newsNextCursor = ref<string | null>(null)
  const newsHasMore = ref(true)
  const newsLoadingMore = ref(false)

  const newsPostListQuery = ref<NewsPostListQuery>({
    search: '',
    sort: NewsPostSort.RECENT_UPDATED,
    limit: 20,
    cursor: undefined,
  })

  async function fetchNewsPosts(options?: { append?: boolean }) {
    const append = options?.append ?? false

    if (newsLoadingMore.value) return
    if (append && !newsHasMore.value) return
    if (newsPosts.value.length >= MAX_POSTS_LIMIT) {
      newsHasMore.value = false
      return
    }

    newsLoadingMore.value = true

    const prevCursor = newsPostListQuery.value.cursor ?? undefined

    try {
      if (!append) {
        currentNewsPostListKey.value += 1
        newsPosts.value = []
        newsHasMore.value = true
        newsPostListQuery.value.cursor = undefined
      } else {
        newsPostListQuery.value.cursor = newsNextCursor.value ?? undefined
      }

      const result = await newsService.getNewsPosts(newsPostListQuery.value)

      const rows = result.items

      newsPosts.value = append ? [...newsPosts.value, ...rows] : rows

      newsNextCursor.value = result.page?.next_cursor ?? null
      newsHasMore.value = result.page?.has_next ?? false
    } catch (err) {
      newsPostListQuery.value.cursor = prevCursor
      throw err
    } finally {
      newsLoadingMore.value = false
    }
  }

  function setSearch(value: string) {
    if (searchTimer) {
      clearTimeout(searchTimer)
    }

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
