import { supportApi } from '@/api/support.api'

import {
  toNoticeDto,
  toNoticeDetailDto,
  toFAQDto,
  toNoticeListRequest,
  toFAQListRequest,
} from '@/services/support.mapper'
import type { NoticeListQuery, FAQListQuery, NoticeDto, FAQDto } from '@/services/support.types'

export async function getNotice(id: number) {
  const env = await supportApi.getNotice(id)

  if (!env.success || !env.data) {
    throw env.error ?? new Error('invalid_notice_response')
  }

  return toNoticeDetailDto(env.data)
}
export async function getNotices(payload: NoticeListQuery): Promise<NoticeDto[]> {
  const env = await supportApi.getNotices(toNoticeListRequest(payload))

  if (!env.success || !env.data) {
    throw env.error ?? new Error('invalid_notice_list_response')
  }

  return env.data.map(toNoticeDto)
}

export async function getFAQs(payload: FAQListQuery): Promise<FAQDto[]> {
  const env = await supportApi.getFAQs(toFAQListRequest(payload))

  if (!env.success || !env.data) {
    throw env.error ?? new Error('invalid_FAQ_list_response')
  }

  return env.data.map(toFAQDto)
}
