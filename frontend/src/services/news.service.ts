import type { CursorListResult, CursorPagination } from "@/api/types"
import {
    newsApi,
} from "@/api/news.api"

import { toNewsPostDto, toNewsPostListRequest } from "@/services/news.mapper"
import type { NewsPostListQuery, NewsPostDto } from "@/services/news.types"

export async function getNewsPosts(payload: NewsPostListQuery): Promise<CursorListResult<NewsPostDto>> {
    const env = await newsApi.getNewsPosts(toNewsPostListRequest(payload))

    if (!env.success || !env.data) {
        throw env.error ?? new Error("invalid_news_post_list_response")
    }

    return {
        items: env.data.map(toNewsPostDto),
        page: env.meta.pagination as CursorPagination
    }
}