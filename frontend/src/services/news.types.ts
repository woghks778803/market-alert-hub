export type NewsPostDto = {
    newsItemId: number
    titleOriginal: string
    descriptionOriginal: string | null
    guid: string | null
    link: string
    publishedAt: string
    fetchedAt: string

    translationId: number
    translationLocal: LanguageCode
    translationProvider: TranslationCode | null
    title: string | null
    description: string | null
    translatedAt: string

    clickCount: number
    shareCount: number

    itemLanguage: LanguageCode
    providerLanguage: LanguageCode
    providerName: string
}

export type NewsPostListQuery = {
    search: string

    cursor?: string
    limit?: number
    sort?: NewsPostSort
}

export enum NewsPostSort {
    RECENT_UPDATED = "recent_updated",
}

export enum TranslationCode {
    GOOGLE = "GOOGLE"
}

export enum LanguageCode {
    KO = "ko",
    EN = "en",
    JA = "ja",
    ZH = "zh",
    UNKNOWN = "unknown",
}

export const MAX_POSTS_LIMIT: number = 300