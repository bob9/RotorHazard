/** Server facts from /app-info (version, enabled hardware, plugin pages...). */
export interface ServerInfo {
  server: Record<string, any>
  admin: boolean
  auth_required: boolean
  first_run: boolean
  debug: boolean
  restart_required: boolean
  num_nodes: number
  imdtabler?: boolean
  led_enabled: boolean
  led_events_enabled: boolean
  vrx_enabled: boolean
  cluster_has_secondaries: boolean
  node_fw_updatable: boolean
  is_raspberry_pi: boolean
  /** plugin loader scripts run on every page (a bar at the top, for example); newer servers only */
  site_scripts?: string[]
  plugin_pages: { name: string, label: string | null, url: string, admin_only: boolean, order: number, source: string }[]
  event: { name: string, description: string }
  timer_name: string
  timer_logo: string
}

const info = ref<ServerInfo | null>(null)
let pending: Promise<void> | null = null

export function useServerInfo() {
  const rh = useRH()
  // taken here, in setup, not inside the fetch callback below
  const { restartRequired } = useMessages()

  function fetchInfo() {
    pending = fetch('/app-info', { headers: rh.authHeader(), cache: 'no-store' })
      .then(r => r.json())
      .then((d) => {
        info.value = d
        if (d.restart_required) restartRequired.value = true
      })
      .catch(() => {})
    return pending
  }

  if (!pending && import.meta.client) {
    fetchInfo()
    // server restarted (new plugins, settings): refresh facts
    rh.on('load_all', () => fetchInfo(), { global: true })
    rh.on('option_update', (d: any) => {
      const o = d?.options || {}
      if (!info.value) return
      if ('eventName' in o) info.value.event.name = o.eventName
      if ('eventDescription' in o) info.value.event.description = o.eventDescription
    }, { global: true })
  }

  return { info, refresh: fetchInfo }
}
