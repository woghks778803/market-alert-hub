export type ApiError = {
    code: string
    message: string
    target?: string | null
    details?: Record<string, unknown> | null
}

export type ApiMeta = {
    request_id?: string
    timestamp?: string
    pagination?: Pagination | CursorPagination | null
}

export type Pagination = {
    page: number
    page_size: number
    total: number
    has_next: boolean
}

export type CursorPagination = {
    limit: number
    next_cursor: string | null
    has_next: boolean
}

export type Envelope<T> = {
    success: boolean
    data?: T | null
    error?: ApiError | null
    meta: ApiMeta
}

export type SimpleOk = {
    ok: boolean
}

export type CursorListResult<T> = {
    items: T[]
    page: CursorPagination
}

export type ListResult<T> = {
    items: T[]
    page: Pagination
}