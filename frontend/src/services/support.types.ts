
export type NoticeDto = {
    id: number
    title: string
    content: string
    category: NoticeCategory

    isActive: boolean
    viewCount: number

    updatedAt: string
}

export type NoticeSimpleDto = {
    id: number
    title: string
}

export type NoticeDatailDto = {
    id: number
    title: string
    summary: string | null
    content: string
    category: NoticeCategory

    isActive: boolean
    viewCount: number

    updatedAt: string

    prevNotice: NoticeSimpleDto | null
    nextNotice: NoticeSimpleDto | null
}

export type FAQDto = {
    id: number
    question: string
    answer: string
    category: string

    displayOrder: number
    isActive: boolean

    updatedAt: string
}

export type NoticeListQuery = {
    category?: NoticeCategory
    limit?: number
    offset?: number
}

export type FAQListQuery = {
    search: string
    category?: string
    limit?: number
    offset?: number
}

export enum NoticeCategory {
    UPDATE = "update",
    MAINTENANCE = "maintenance",
    NOTICE = "notice",
}

export type NoticeCategoryStyle = {
    title: string
    bg: string
    text: string
}

export const NoticeCategoryLabel: Record<NoticeCategory, NoticeCategoryStyle> = {
    [NoticeCategory.UPDATE]: {
        title: "업데이트",
        bg: "update",
        text: "update",
    },
    [NoticeCategory.MAINTENANCE]: {
        title: "점검",
        bg: "maintenance",
        text: "maintenance",
    },
    [NoticeCategory.NOTICE]: {
        title: "안내",
        bg: "notice",
        text: "notice",
    },
}