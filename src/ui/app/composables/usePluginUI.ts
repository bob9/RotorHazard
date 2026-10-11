/**
 * Plugin panels arrive through the 'ui' event, one page at a time, and can be
 * pushed by plugins at any time (rhapi.ui.broadcast_ui). Keep every page's
 * panels so each view can show its own.
 */
const pages = reactive<Record<string, any[]>>({})
let listening = false

export function usePluginUI() {
  const rh = useRH()
  if (!listening && import.meta.client) {
    listening = true
    rh.on('ui', (data: any) => {
      if (!data?.page) return
      const incoming: any[] = data.panels || []
      if (data.replace_panels === false && pages[data.page]) {
        const current = [...pages[data.page]!]
        for (const p of incoming) {
          const i = current.findIndex(c => c.panel.name === p.panel.name)
          if (i >= 0) current[i] = p
          else current.push(p)
        }
        pages[data.page] = current
      } else {
        pages[data.page] = incoming
      }
    }, { global: true })
  }

  function panelsFor(page: string) {
    return pages[page] || []
  }

  function saveField(field: any, value: any, binding = false) {
    if (binding) rh.emit('set_ui_binding_value', { name: field.name, value })
    else if (field.section) rh.emit('set_config', { section: field.section, key: field.name, value })
    else rh.emit('set_option', { option: field.name, value })
    field.value = value
  }

  function pressButton(name: string) {
    rh.emit('dispatch_event', { id: name, namespace: 'quickbutton' })
  }

  return { pages, panelsFor, saveField, pressButton }
}
