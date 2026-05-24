import type {
  NoticeInfo,
  NoticeDetailInfo,
  FAQInfo,
  NoticeListRequest,
  FAQListRequest,
} from '@/api/support.api'
import type {
  NoticeDto,
  NoticeDatailDto,
  FAQDto,
  NoticeListQuery,
  FAQListQuery,
} from '@/services/support.types'
import { NoticeCategory } from '@/services/support.types'

export function toNoticeDto(data: NoticeInfo): NoticeDto {
  return {
    id: data.id,
    title: data.title,
    content: data.content,
    category: data.category as NoticeCategory,

    isActive: data.is_active,
    viewCount: data.view_count,

    createdAt: data.created_at,
    updatedAt: data.updated_at,
  }
}

export function toNoticeDetailDto(data: NoticeDetailInfo): NoticeDatailDto {
  return {
    id: data.id,
    title: data.title,
    summary: data.summary,
    content: data.content,
    category: data.category as NoticeCategory,

    isActive: data.is_active,
    viewCount: data.view_count,

    createdAt: data.created_at,
    updatedAt: data.updated_at,

    prevNotice: data.prev,
    nextNotice: data.next,
  }
}

export function toFAQDto(data: FAQInfo): FAQDto {
  return {
    id: data.id,
    question: data.question,
    answer: data.answer,
    category: data.category,

    sortOrder: data.sort_order,
    isActive: data.is_active,

    updatedAt: data.updated_at,
  }
}

export function toNoticeDtoList(list: NoticeInfo[]): NoticeDto[] {
  return list.map(toNoticeDto)
}

export function toFAQDtoList(list: FAQInfo[]): FAQDto[] {
  return list.map(toFAQDto)
}

export function toNoticeListRequest(q: NoticeListQuery): NoticeListRequest {
  return {
    category: q.category,
    limit: q.limit,
    offset: q.offset,
  }
}

export function toFAQListRequest(q: FAQListQuery): FAQListRequest {
  return {
    search: q.search,
    category: q.category,
    limit: q.limit,
    offset: q.offset,
  }
}
