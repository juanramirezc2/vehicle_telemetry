import { useEffect } from "react";
import { useDashboardSocket } from "./hooks/useDashboardSocket";
import { useAnomalyStore } from "./stores/anomalyStore";

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "medium",
  }).format(new Date(value));
}

function formatReason(reason: string) {
  return reason.replaceAll("_", " ");
}

export default function App() {
  useDashboardSocket();
  const anomalies = useAnomalyStore((store) => store.anomalies);
  const anomalyState = useAnomalyStore((store) => store.state);
  const anomalyError = useAnomalyStore((store) => store.error);
  const fetchAnomalies = useAnomalyStore((store) => store.fetchAnomalies);

  useEffect(() => {
    fetchAnomalies(50);
  }, [fetchAnomalies]);

  return (
    <main className="min-h-screen bg-slate-950 px-4 py-8 text-slate-100 sm:px-6 lg:px-8">
      <div className="mx-auto flex max-w-7xl flex-col gap-8">
        <section className="overflow-hidden rounded-3xl border border-white/10 bg-[radial-gradient(circle_at_top_left,_rgba(20,184,166,0.22),_transparent_36%),linear-gradient(135deg,_rgba(15,23,42,0.96),_rgba(30,41,59,0.92))] p-6 shadow-2xl shadow-cyan-950/30 sm:p-8">
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
        </section>

        <section className="rounded-3xl border border-slate-200 bg-white text-slate-950 shadow-xl shadow-slate-950/10">
          <div className="flex flex-col gap-4 border-b border-slate-200 p-5 sm:flex-row sm:items-center sm:justify-between sm:p-6">
            <div className="max-w-3xl">
              <p className="text-sm font-semibold uppercase tracking-[0.25em] text-cyan-700">
                Latest 50
              </p>
              <h2 className="mt-2 text-2xl font-black tracking-tight">
                Telemetry anomalies
              </h2>
            </div>
            <div className="rounded-full bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-700">
              {anomalyState === "loading"
                ? "Loading anomalies"
                : `${anomalies.length} anomalies`}
            </div>
          </div>

          {anomalyState === "error" ? (
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
                  <tr
                    className="transition hover:bg-cyan-50/60"
                    key={anomaly.id}
                  >
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
                      {anomaly.zone_entered ?? "none"}
                    </td>
                    <td className="whitespace-nowrap px-5 py-4 text-slate-600">
                      {formatDateTime(anomaly.timestamp)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {anomalyState === "success" && anomalies.length === 0 ? (
            <div className="p-10 text-center text-slate-500">
              No anomaly telemetry has been reported yet.
            </div>
          ) : null}
          {anomalyState === "loading" ? (
            <div className="p-10 text-center text-slate-500">
              Loading anomaly data...
            </div>
          ) : null}
        </section>
      </div>
    </main>
  );
}
