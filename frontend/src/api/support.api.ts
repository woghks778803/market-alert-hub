import { http } from "./http"
import type { Envelope } from "./types"

export type NoticeInfo = {
    id: number
    title: string
    content: string
    category: string

    is_active: boolean
    view_count: number

    updated_at: string
}

export type NoticeSimpleInfo = {
    id: number
    title: string
}

export type NoticeDetailInfo = {
    id: number
    title: string
    summary: string | null
    content: string
    category: string

    is_active: boolean
    view_count: number

    updated_at: string

    prev: NoticeSimpleInfo | null
    next: NoticeSimpleInfo | null
}

export type FAQInfo = {
    id: number
    question: string
    answer: string
    category: string

    sort_order: number
    is_active: boolean

    updated_at: string
}

export type NoticeListRequest = {
    category?: string
    limit?: number
    offset?: number
}

export type FAQListRequest = {
    search?: string
    category?: string
    limit?: number
    offset?: number
}

export const supportApi = {
    // GET /notices/{id}
    async getNotice(id: number) {
        const { data } = await http.get<Envelope<NoticeDetailInfo>>(
            `/supports/notices/${id}`
        );
        return data;
    },

    // GET /notices
    async getNotices(params?: NoticeListRequest) {
        const { data } = await http.get<Envelope<NoticeInfo[]>>(
            '/supports/notices',
            { params }
        );
        return data;
    },

    // GET /faqs
    async getFAQs(params?: FAQListRequest) {
        const { data } = await http.get<Envelope<FAQInfo[]>>(
            '/supports/faqs',
            { params }
        );
        return data;
    },

}