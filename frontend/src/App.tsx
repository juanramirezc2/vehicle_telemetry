import { useEffect, useState } from 'react'
import { io, type Socket } from 'socket.io-client'

type ServiceState = 'checking' | 'online' | 'offline'
type LoadState = 'idle' | 'loading' | 'success' | 'error'

type ServiceStatus = {
  label: string
  path: string
  state: ServiceState
}

type Anomaly = {
  id: string
  vehicle_id: string
  timestamp: string
  received_at: string
  lat: number
  lon: number
  battery_pct: number
  speed_mps: number
  status: string
  error_codes: string[]
  zone_entered: string | null
  reasons: string[]
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

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'medium',
  }).format(new Date(value))
}

function formatReason(reason: string) {
  return reason.replaceAll('_', ' ')
}

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
  const [anomalies, setAnomalies] = useState<Anomaly[]>([])
  const [anomalyState, setAnomalyState] = useState<LoadState>('idle')
  const [anomalyError, setAnomalyError] = useState<string | null>(null)

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
        setStatuses([
          ...nextStatuses,
          { label: 'Socket.IO', path: SOCKET_PATH, state: socketState },
        ])
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

  useEffect(() => {
    const controller = new AbortController()

    async function loadAnomalies() {
      setAnomalyState('loading')
      setAnomalyError(null)

      try {
        const response = await fetch(`${API_URL}/api/anomalies?limit=25`, {
          signal: controller.signal,
        })

        if (!response.ok) {
          throw new Error(`Anomaly request failed with ${response.status}`)
        }

        const data = (await response.json()) as Anomaly[]
        setAnomalies(data)
        setAnomalyState('success')
      } catch (error) {
        if (controller.signal.aborted) {
          return
        }

        setAnomalyState('error')
        setAnomalyError(
          error instanceof Error ? error.message : 'Failed to load anomalies',
        )
      }
    }

    loadAnomalies()

    return () => {
      controller.abort()
    }
  }, [])

  return (
    <main className="min-h-screen bg-slate-950 px-4 py-8 text-slate-100 sm:px-6 lg:px-8">
      <div className="mx-auto flex max-w-7xl flex-col gap-8">
        <section className="overflow-hidden rounded-3xl border border-white/10 bg-[radial-gradient(circle_at_top_left,_rgba(20,184,166,0.22),_transparent_36%),linear-gradient(135deg,_rgba(15,23,42,0.96),_rgba(30,41,59,0.92))] p-6 shadow-2xl shadow-cyan-950/30 sm:p-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <p className="text-sm font-semibold uppercase tracking-[0.35em] text-cyan-300">
                Qualitara Fleet Ops
              </p>
              <h1 className="mt-4 text-4xl font-black tracking-tight text-white sm:text-6xl">
                Anomaly dashboard
              </h1>
              <p className="mt-4 max-w-2xl text-base leading-7 text-slate-300">
                Monitor derived telemetry anomalies from low battery and overspeed
                events. Data is loaded from the FastAPI anomaly endpoint.
              </p>
            </div>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:min-w-[520px]">
              {statuses.map((service) => (
                <article
                  className="rounded-2xl border border-white/10 bg-white/[0.06] p-4 shadow-lg shadow-black/10 backdrop-blur"
                  key={service.path}
                >
                  <p className="text-xs font-medium text-slate-400">{service.label}</p>
                  <p
                    className={`mt-3 inline-flex rounded-full px-2.5 py-1 text-xs font-bold uppercase tracking-wide ${
                      service.state === 'online'
                        ? 'bg-emerald-400/15 text-emerald-300'
                        : service.state === 'offline'
                          ? 'bg-rose-400/15 text-rose-300'
                          : 'bg-slate-400/15 text-slate-300'
                    }`}
                  >
                    {service.state}
                  </p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="rounded-3xl border border-slate-200 bg-white text-slate-950 shadow-xl shadow-slate-950/10">
          <div className="flex flex-col gap-4 border-b border-slate-200 p-5 sm:flex-row sm:items-center sm:justify-between sm:p-6">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.25em] text-cyan-700">
                Latest 25
              </p>
              <h2 className="mt-2 text-2xl font-black tracking-tight">
                Telemetry anomalies
              </h2>
            </div>
            <div className="rounded-full bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-700">
              {anomalyState === 'loading'
                ? 'Loading anomalies'
                : `${anomalies.length} anomalies`}
            </div>
          </div>

          {anomalyState === 'error' ? (
            <div className="m-6 rounded-2xl border border-rose-200 bg-rose-50 p-5 text-rose-800">
              {anomalyError}
            </div>
          ) : null}

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wider text-slate-500">
                <tr>
                  <th className="px-5 py-4 font-bold">Vehicle</th>
                  <th className="px-5 py-4 font-bold">Reasons</th>
                  <th className="px-5 py-4 font-bold">Battery</th>
                  <th className="px-5 py-4 font-bold">Speed</th>
                  <th className="px-5 py-4 font-bold">Status</th>
                  <th className="px-5 py-4 font-bold">Zone</th>
                  <th className="px-5 py-4 font-bold">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {anomalies.map((anomaly) => (
                  <tr className="transition hover:bg-cyan-50/60" key={anomaly.id}>
                    <td className="whitespace-nowrap px-5 py-4 font-bold text-slate-950">
                      {anomaly.vehicle_id}
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex flex-wrap gap-2">
                        {anomaly.reasons.map((reason) => (
                          <span
                            className="rounded-full bg-amber-100 px-2.5 py-1 text-xs font-bold uppercase tracking-wide text-amber-800"
                            key={reason}
                          >
                            {formatReason(reason)}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="whitespace-nowrap px-5 py-4 font-semibold text-slate-700">
                      {anomaly.battery_pct.toFixed(1)}%
                    </td>
                    <td className="whitespace-nowrap px-5 py-4 font-semibold text-slate-700">
                      {anomaly.speed_mps.toFixed(1)} m/s
                    </td>
                    <td className="whitespace-nowrap px-5 py-4 text-slate-600">
                      {anomaly.status}
                    </td>
                    <td className="whitespace-nowrap px-5 py-4 text-slate-600">
                      {anomaly.zone_entered ?? 'none'}
                    </td>
                    <td className="whitespace-nowrap px-5 py-4 text-slate-600">
                      {formatDateTime(anomaly.timestamp)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {anomalyState === 'success' && anomalies.length === 0 ? (
            <div className="p-10 text-center text-slate-500">
              No anomaly telemetry has been reported yet.
            </div>
          ) : null}
          {anomalyState === 'loading' ? (
            <div className="p-10 text-center text-slate-500">Loading anomaly data...</div>
          ) : null}
        </section>
      </div>
    </main>
  )
}
