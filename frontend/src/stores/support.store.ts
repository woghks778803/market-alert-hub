import { defineStore } from "pinia"
import { ref } from "vue"

import * as supportService from "@/services/support.service"
import type { NoticeDto, NoticeDatailDto, NoticeListQuery, FAQDto, FAQListQuery } from "@/services/support.types"
import { NoticeCategory } from "@/services/support.types"

export const useSupportStore = defineStore("notice", () => {
    let searchTimer: any
    const faqs = ref<FAQDto[]>([])
    const notices = ref<NoticeDto[]>([])
    const notice = ref<NoticeDatailDto | null>(null)
    const activeTab = ref<NoticeCategory>(NoticeCategory.UPDATE)

    const noticeListQuery = ref<NoticeListQuery>({
        category: NoticeCategory.UPDATE,
        limit: 20,
        offset: 0,
    })

    const FAQListQuery = ref<FAQListQuery>({
        search: "",
        category: undefined,
        limit: 20,
        offset: 0,
    })

    async function fetchNotices() {
        notices.value = await supportService.getNotices(noticeListQuery.value)
    }

    async function fetchNotice(id: number) {
        notice.value = await supportService.getNotice(id)
    }

    async function fetchFAQs() {
        faqs.value = await supportService.getFAQs(FAQListQuery.value)
    }

    function setSearch(value: string) {
        clearTimeout(searchTimer)

        searchTimer = setTimeout(() => {
            FAQListQuery.value.search = value
            fetchFAQs()
        }, 500)
    }

    function setNoticeCategory(category: NoticeCategory) {
        noticeListQuery.value.category = category
        noticeListQuery.value.offset = 0

        fetchNotices()
    }

    function resetSupport() {
        notice.value = null
        notices.value = []
        faqs.value = []
        activeTab.value = NoticeCategory.UPDATE
    }

    return {
        activeTab,

        noticeListQuery,
        FAQListQuery,

        notices,
        notice,
        faqs,

        fetchNotices,
        fetchNotice,
        fetchFAQs,

        resetSupport,

        setSearch,
        setNoticeCategory,
    }
})