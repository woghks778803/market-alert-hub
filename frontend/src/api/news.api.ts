import { http } from "./http"
import type { Envelope, SimpleOk } from "./types"

export type NewsPostInfo = {
    news_item_id: number
    title_original: string
    description_original: string | null
    guid: string | null
    link: string
    published_at: string
    fetched_at: string

    translation_id: number
    translation_local: string
    translation_provider: string | null
    title: string | null
    description: string | null
    translated_at: string

    click_count: number
    share_count: number

    item_language: string
    provider_language: string
    provider_name: string
}

export type NewsPostListRequest = {
    search: string

    cursor_at?: string
    cursor_id?: number
    start?: string
    end?: string

    limit?: number
    sort?: string
}

export const newsApi = {
    // GET /newses/posts
    async getNewsPosts(params?: NewsPostListRequest) {
        const { data } = await http.get<Envelope<NewsPostInfo[]>>(
            '/newses/posts',
            { params }
        );
        return data;
    },
}