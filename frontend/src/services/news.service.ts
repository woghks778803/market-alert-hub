import {
    newsApi,
} from "@/api/news.api"

import { toNewsPostDto, toNewsPostListRequest } from "@/services/news.mapper"
import type { NewsPostListQuery } from "@/services/news.types"

export async function getNewsPosts(payload: NewsPostListQuery) {
    const env = await newsApi.getNewsPosts(toNewsPostListRequest(payload))

    if (!env.success || !env.data) {
        throw env.error ?? new Error("invalid_news_post_list_response")
    }

    return env.data.map(toNewsPostDto)
}