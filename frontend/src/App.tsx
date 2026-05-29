import { useEffect, useState } from 'react'
import { io, type Socket } from 'socket.io-client'

type ServiceState = 'checking' | 'online' | 'offline'

type ServiceStatus = {
  label: string
  path: string
  state: ServiceState
}

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
const SOCKET_PATH = '/dashboard.io'

const initialStatuses: ServiceStatus[] = [
  { label: 'API', path: '/api/health', state: 'checking' },
  { label: 'Postgres', path: '/api/health/db', state: 'checking' },
  { label: 'Redis', path: '/api/health/redis', state: 'checking' },
  { label: 'Socket.IO', path: SOCKET_PATH, state: 'checking' },
]

const healthStatuses = initialStatuses.filter(
  (service) => service.path !== SOCKET_PATH,
)

async function checkService(path: string): Promise<ServiceState> {
  try {
    const response = await fetch(`${API_URL}${path}`)
    return response.ok ? 'online' : 'offline'
  } catch {
    return 'offline'
  }
}

export default function App() {
  const [statuses, setStatuses] = useState<ServiceStatus[]>(initialStatuses)
  const [socketState, setSocketState] = useState<ServiceState>('checking')

  useEffect(() => {
    let isMounted = true

    async function loadStatuses() {
      const nextStatuses = await Promise.all(
        healthStatuses.map(async (service) => ({
          ...service,
          state: await checkService(service.path),
        })),
      )

      if (isMounted) {
        setStatuses([...nextStatuses, { label: 'Socket.IO', path: SOCKET_PATH, state: socketState }])
      }
    }

    loadStatuses()

    return () => {
      isMounted = false
    }
  }, [])

  useEffect(() => {
    const socket: Socket = io(API_URL, {
      path: SOCKET_PATH,
      transports: ['websocket'],
    })

    socket.on('connect', () => {
      setSocketState('online')
    })

    socket.on('connect_error', () => {
      setSocketState('offline')
    })

    socket.on('disconnect', () => {
      setSocketState('offline')
    })

    return () => {
      socket.disconnect()
    }
  }, [])

  useEffect(() => {
    setStatuses((currentStatuses) =>
      currentStatuses.map((service) =>
        service.path === SOCKET_PATH
          ? { ...service, state: socketState }
          : service,
      ),
    )
  }, [socketState])

  return (
    <main className="app-shell">
      <section className="status-panel" aria-labelledby="status-title">
        <p className="eyebrow">Qualitara</p>
        <h1 id="status-title">Service status</h1>
        <div className="status-list">
          {statuses.map((service) => (
            <article className="status-row" key={service.path}>
              <div>
                <h2>{service.label}</h2>
                <p>{service.path}</p>
              </div>
              <span className={`badge ${service.state}`}>{service.state}</span>
            </article>
          ))}
        </div>
      </section>
    </main>
  )
}
