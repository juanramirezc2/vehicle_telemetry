import { useEffect } from "react";
import { io, type Socket } from "socket.io-client";
import { type Anomaly, useAnomalyStore } from "../stores/anomalyStore";
import { useZonesStore } from "../stores/zonesStore";

type ZoneCountChangedEvent = {
  zone_id: string;
};

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const SOCKET_PATH = "/dashboard.io";

export function useDashboardSocket() {
  const upsertAnomaly = useAnomalyStore((store) => store.upsertAnomaly);
  const incrementZoneCount = useZonesStore((store) => store.incrementZoneCount);

  useEffect(() => {
    const socket: Socket = io(API_URL, {
      path: SOCKET_PATH,
      transports: ["websocket"],
    });

    socket.on("anomaly:detected", (anomaly: Anomaly) => {
      upsertAnomaly(anomaly);
    });

    socket.on("zones:count_changed", (event: ZoneCountChangedEvent) => {
      incrementZoneCount(event.zone_id);
    });

    return () => {
      socket.off("anomaly:detected");
      socket.off("zones:count_changed");
      socket.disconnect();
    };
  }, [incrementZoneCount, upsertAnomaly]);
}
