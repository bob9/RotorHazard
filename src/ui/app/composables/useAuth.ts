/**
 * Admin access. RotorHazard protects admin actions with HTTP Basic auth; the
 * web app checks credentials against /app-auth and sends them with the
 * Socket.IO handshake so admin socket events are accepted.
 */
const admin = ref<boolean | null>(null)
const loginOpen = ref(false)

async function check(creds = readCredentials()) {
  const headers: Record<string, string> = {}
  if (creds) headers.Authorization = 'Basic ' + btoa(unescape(encodeURIComponent(`${creds.username}:${creds.password}`)))
  try {
    const res = await fetch('/app-auth', { headers, cache: 'no-store' })
    return res.ok
  } catch {
    return false
  }
}

export function useAuth() {
  const rh = useRH()

  async function refresh() {
    admin.value = await check()
    return admin.value
  }

  async function login(username: string, password: string) {
    const ok = await check({ username, password })
    if (ok) {
      writeCredentials({ username, password })
      admin.value = true
      rh.reconnect()
    }
    return ok
  }

  function logout() {
    writeCredentials(null)
    rh.reconnect()
    refresh()
  }

  return { admin, loginOpen, refresh, login, logout, hasCredentials: () => !!readCredentials() }
}
