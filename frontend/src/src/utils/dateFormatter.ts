import type { Composer } from 'vue-i18n'

/**
 * Formats a date into a readable format
 */
export function formatDate(dateString: string, locale: string = 'en-US'): string {
  const date = new Date(dateString)

  return new Intl.DateTimeFormat(locale, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(date)
}

/**
 * Formats a date with time
 */
export function formatDateTime(dateString: string, locale: string = 'en-US'): string {
  const date = new Date(dateString)

  return new Intl.DateTimeFormat(locale, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

/**
 * Formats a date into a short format
 */
export function formatShortDate(dateString: string, locale: string = 'en-US'): string {
  const date = new Date(dateString)

  return new Intl.DateTimeFormat(locale, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(date)
}

/**
 * Formats a date relative to the current time
 */
export function formatRelativeTime(dateString: string, locale: string = 'en-US'): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)

  const rtf = new Intl.RelativeTimeFormat(locale, { numeric: 'auto' })

  if (Math.abs(diffInSeconds) < 60) {
    return rtf.format(-diffInSeconds, 'second')
  }

  const diffInMinutes = Math.floor(diffInSeconds / 60)
  if (Math.abs(diffInMinutes) < 60) {
    return rtf.format(-diffInMinutes, 'minute')
  }

  const diffInHours = Math.floor(diffInMinutes / 60)
  if (Math.abs(diffInHours) < 24) {
    return rtf.format(-diffInHours, 'hour')
  }

  const diffInDays = Math.floor(diffInHours / 24)
  if (Math.abs(diffInDays) < 30) {
    return rtf.format(-diffInDays, 'day')
  }

  const diffInMonths = Math.floor(diffInDays / 30)
  if (Math.abs(diffInMonths) < 12) {
    return rtf.format(-diffInMonths, 'month')
  }

  const diffInYears = Math.floor(diffInMonths / 12)
  return rtf.format(-diffInYears, 'year')
}

/**
 * Checks whether the date is today
 */
export function isToday(dateString: string): boolean {
  const date = new Date(dateString)
  const today = new Date()

  return (
    date.getDate() === today.getDate() &&
    date.getMonth() === today.getMonth() &&
    date.getFullYear() === today.getFullYear()
  )
}

/**
 * Checks whether the date is yesterday
 */
export function isYesterday(dateString: string): boolean {
  const date = new Date(dateString)
  const yesterday = new Date()
  yesterday.setDate(yesterday.getDate() - 1)

  return (
    date.getDate() === yesterday.getDate() &&
    date.getMonth() === yesterday.getMonth() &&
    date.getFullYear() === yesterday.getFullYear()
  )
}

/**
 * Formats a date accounting for "today" and "yesterday" using i18n
 */
export function formatSmartDate(dateString: string, t: Composer['t']): string {
  if (isToday(dateString)) {
    return t('date.today')
  }

  if (isYesterday(dateString)) {
    return t('date.yesterday')
  }

  return formatDate(dateString, t('$locale') as string)
}

/**
 * Gets the difference between two dates in days
 */
export function getDaysDifference(dateString1: string, dateString2?: string): number {
  const date1 = new Date(dateString1)
  const date2 = dateString2 ? new Date(dateString2) : new Date()

  const diffInTime = date2.getTime() - date1.getTime()
  return Math.floor(diffInTime / (1000 * 60 * 60 * 24))
}

/**
 * Sorts an array of articles by date
 */
export function sortArticlesByDate<T extends { publishedDate: string }>(
  articles: T[],
  ascending: boolean = false,
): T[] {
  return [...articles].sort((a, b) => {
    const dateA = new Date(a.publishedDate).getTime()
    const dateB = new Date(b.publishedDate).getTime()
    return ascending ? dateA - dateB : dateB - dateA
  })
}

type PeriodKey = 'today' | 'yesterday' | 'thisWeek' | 'thisMonth' | 'older'

interface GroupedArticles<T> {
  label: string
  articles: T[]
}

/**
 * Groups articles by period using i18n
 */
export function groupArticlesByPeriod<T extends { publishedDate: string }>(
  articles: T[],
  t: Composer['t'],
): GroupedArticles<T>[] {
  const labels: Record<PeriodKey, string> = {
    today: t('date.today'),
    yesterday: t('date.yesterday'),
    thisWeek: t('date.thisWeek'),
    thisMonth: t('date.thisMonth'),
    older: t('date.older'),
  }

  const groups: Record<PeriodKey, T[]> = {
    today: [],
    yesterday: [],
    thisWeek: [],
    thisMonth: [],
    older: [],
  }

  const now = new Date()
  const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
  const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)

  articles.forEach((article) => {
    const articleDate = new Date(article.publishedDate)
    let periodKey: PeriodKey

    if (isToday(article.publishedDate)) {
      periodKey = 'today'
    } else if (isYesterday(article.publishedDate)) {
      periodKey = 'yesterday'
    } else if (articleDate > weekAgo) {
      periodKey = 'thisWeek'
    } else if (articleDate > monthAgo) {
      periodKey = 'thisMonth'
    } else {
      periodKey = 'older'
    }

    groups[periodKey].push(article)
  })

  return (Object.keys(groups) as PeriodKey[])
    .filter((key) => groups[key].length > 0)
    .map((key) => ({
      label: labels[key],
      articles: groups[key],
    }))
}
