import { create } from "zustand";
import { type LoadState } from "./anomalyStore";

export type ZoneCount = {
  zone_id: string;
  entry_count: number;
  updated_at: string | null;
};

type ZonesStore = {
  zones: ZoneCount[];
  state: LoadState;
  error: string | null;
  fetchZones: () => Promise<void>;
  incrementZoneCount: (zoneId: string) => void;
};

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export const useZonesStore = create<ZonesStore>((set) => ({
  zones: [],
  state: "idle",
  error: null,
  async fetchZones() {
    set({ state: "loading", error: null });

    try {
      const response = await fetch(`${API_URL}/api/zones/counts`);

      if (!response.ok) {
        throw new Error(`Zone counts request failed with ${response.status}`);
      }

      const zones = (await response.json()) as ZoneCount[];
      set({ zones, state: "success" });
    } catch (error) {
      set({
        state: "error",
        error: error instanceof Error ? error.message : "Failed to load zone counts",
      });
    }
  },
  incrementZoneCount(zoneId) {
    set((store) => {
      const existingIndex = store.zones.findIndex((zone) => zone.zone_id === zoneId);

      if (existingIndex === -1) {
        return {
          zones: [
            { zone_id: zoneId, entry_count: 1, updated_at: new Date().toISOString() },
            ...store.zones,
          ],
        };
      }

      const zones = [...store.zones];
      zones[existingIndex] = {
        ...zones[existingIndex],
        entry_count: zones[existingIndex].entry_count + 1,
        updated_at: new Date().toISOString(),
      };
      return { zones };
    });
  },
}));
