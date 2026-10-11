/**
 * Translation using the server's language tables (the same strings as the
 * classic interface). Strings are keyed by their English text.
 */
export function useI18n() {
  const { state } = useRH()
  const lang = computed<string>(() => state.language?.language || '')
  const table = computed<Record<string, string>>(() => {
    const l = lang.value
    return (l && state.all_languages?.languages?.[l]?.values) || {}
  })
  function t(text: string | null | undefined, ...args: (string | number)[]) {
    if (text === null || text === undefined) return ''
    let out = table.value[text] || text
    args.forEach((a, i) => { out = out.replace(`{${i}}`, String(a)) })
    return out
  }
  return { t, lang }
}
