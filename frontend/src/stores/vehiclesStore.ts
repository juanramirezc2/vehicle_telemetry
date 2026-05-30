import { create } from "zustand";
import { type LoadState } from "./anomalyStore";

export type Vehicle = {
  id: string;
  status: string;
  battery: number;
  current_zone: string | null;
  updated_at: string;
};

type VehiclesStore = {
  vehicles: Vehicle[];
  state: LoadState;
  error: string | null;
  fetchVehicles: (limit?: number) => Promise<void>;
  upsertVehicle: (vehicle: Vehicle) => void;
};

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export const useVehiclesStore = create<VehiclesStore>((set) => ({
  vehicles: [],
  state: "idle",
  error: null,
  async fetchVehicles(limit = 500) {
    set({ state: "loading", error: null });

    try {
      const response = await fetch(`${API_URL}/api/vehicles?limit=${limit}`);

      if (!response.ok) {
        throw new Error(`Vehicles request failed with ${response.status}`);
      }

      const vehicles = (await response.json()) as Vehicle[];
      set({ vehicles, state: "success" });
    } catch (error) {
      set({
        state: "error",
        error: error instanceof Error ? error.message : "Failed to load vehicles",
      });
    }
  },
  upsertVehicle(vehicle) {
    set((store) => {
      const existingIndex = store.vehicles.findIndex(
        (currentVehicle) => currentVehicle.id === vehicle.id,
      );

      if (existingIndex === -1) {
        return { vehicles: [vehicle, ...store.vehicles] };
      }

      const vehicles = [...store.vehicles];
      vehicles[existingIndex] = vehicle;
      return { vehicles };
    });
  },
}));
