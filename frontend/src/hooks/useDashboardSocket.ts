import { useEffect } from "react";
import { io, type Socket } from "socket.io-client";
import { type Anomaly, useAnomalyStore } from "../stores/anomalyStore";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const SOCKET_PATH = "/dashboard.io";

export function useDashboardSocket() {
  const upsertAnomaly = useAnomalyStore((store) => store.upsertAnomaly);

  useEffect(() => {
    const socket: Socket = io(API_URL, {
      path: SOCKET_PATH,
      transports: ["websocket"],
    });

    socket.on("anomaly:detected", (anomaly: Anomaly) => {
      upsertAnomaly(anomaly);
    });

    return () => {
      socket.off("anomaly:detected");
      socket.disconnect();
    };
  }, [upsertAnomaly]);
}
