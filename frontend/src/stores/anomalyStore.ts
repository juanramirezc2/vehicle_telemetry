import { create } from "zustand";

export type LoadState = "idle" | "loading" | "success" | "error";

export type Anomaly = {
  id: string;
  vehicle_id: string;
  timestamp: string;
  received_at: string;
  lat: number;
  lon: number;
  battery_pct: number;
  speed_mps: number;
  status: string;
  error_codes: string[];
  zone_entered: string | null;
  reasons: string[];
};

type AnomalyStore = {
  anomalies: Anomaly[];
  state: LoadState;
  error: string | null;
  fetchAnomalies: (limit?: number) => Promise<void>;
  upsertAnomaly: (anomaly: Anomaly) => void;
};

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export const useAnomalyStore = create<AnomalyStore>((set) => ({
  anomalies: [],
  state: "idle",
  error: null,
  async fetchAnomalies(limit = 50) {
    set({ state: "loading", error: null });

    try {
      const response = await fetch(`${API_URL}/api/anomalies?limit=${limit}`);

      if (!response.ok) {
        throw new Error(`Anomaly request failed with ${response.status}`);
      }

      const anomalies = (await response.json()) as Anomaly[];
      set({ anomalies, state: "success" });
    } catch (error) {
      set({
        state: "error",
        error: error instanceof Error ? error.message : "Failed to load anomalies",
      });
    }
  },
  upsertAnomaly(anomaly) {
    set((store) => {
      const existingIndex = store.anomalies.findIndex(
        (currentAnomaly) => currentAnomaly.vehicle_id === anomaly.vehicle_id,
      );

      if (existingIndex === -1) {
        return { anomalies: [anomaly, ...store.anomalies] };
      }

      const anomalies = [...store.anomalies];
      anomalies[existingIndex] = anomaly;
      return { anomalies };
    });
  },
}));
