import { marked } from 'marked'
import DOMPurify from 'dompurify'

marked.setOptions({
  gfm: true,
  breaks: true,
})

DOMPurify.addHook('afterSanitizeAttributes', (node) => {
  if (node.tagName === 'A' && node.hasAttribute('href')) {
    node.setAttribute('target', '_blank')
    node.setAttribute('rel', 'noopener noreferrer')
  }
})

export const renderMarkdown = (text: string): string => {
  if (!text) return ''

  try {
    // Step 1: Transpile Markdown -> raw HTML
    let html = marked.parse(text) as string

    // Step 2: Turn text [1], [2] into interactive badges
    html = html.replace(/\[(\d+)\]/g, '<span class="citation-badge" data-ref="$1">[$1]</span>')

    // Step 3: Sanitize
    return DOMPurify.sanitize(html, {
      // ⚠️ CRITICAL: DOMPurify strips classes and data-* attributes by default.
      // We explicitly extend the allowlist so our badge styles don't break.
      // If you use any other attributes (e.g. id), add them here.
      ADD_ATTR: ['target', 'rel', 'data-ref', 'class'],
    })
  } catch (error) {
    console.error('[Markdown Render Error]:', error)
    // Fallback: if the parser fails, return safe raw text
    return DOMPurify.sanitize(text)
  }
}
