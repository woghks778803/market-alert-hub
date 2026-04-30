import type { NewsPostInfo, NewsPostListRequest } from "@/api/news.api"
import type { NewsPostDto, NewsPostListQuery } from "@/services/news.types"
import { NewsPostSort, LanguageCode, TranslationCode } from "@/services/news.types"

export function toNewsPostDto(data: NewsPostInfo): NewsPostDto {
    return {
        newsItemId: data.news_item_id,
        titleOriginal: data.title_original,
        descriptionOriginal: data.description_original,
        guid: data.guid,
        link: data.link,
        publishedAt: data.published_at,
        fetchedAt: data.fetched_at,

        translationId: data.translation_id,
        translationLocal: data.translation_local as LanguageCode,
        translationProvider: data.translation_provider as TranslationCode,
        title: data.title,
        description: data.description,
        translatedAt: data.translated_at,

        clickCount: data.click_count,
        shareCount: data.share_count,

        itemLanguage: data.item_language as LanguageCode,
        providerLanguage: data.provider_language as LanguageCode,
        providerName: data.provider_name
    }
}

export function toNewsPostListRequest(q: NewsPostListQuery): NewsPostListRequest {
    return {
        search: q.search,

        cursor_at: q.cursorAt,
        cursor_id: q.cursorId,
        end: q.end,
        start: q.start,

        limit: q.limit,
        sort: q.sort as NewsPostSort,
    }
}