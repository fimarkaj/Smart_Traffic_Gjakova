import { create } from 'zustand'
import { persist } from 'zustand/middleware'

// ── Auth ──────────────────────────────────────────────
export const useAuthStore = create(
  persist(
    (set) => ({
      token:    null,
      username: null,
      login:  (token, username) => set({ token, username }),
      logout: () => set({ token: null, username: null }),
    }),
    {
      name: 'stai-auth',
      storage: {
        getItem:    (k) => sessionStorage.getItem(k),
        setItem:    (k, v) => sessionStorage.setItem(k, v),
        removeItem: (k) => sessionStorage.removeItem(k),
      },
    }
  )
)

// ── Live WebSocket state ──────────────────────────────
export const useLiveStore = create((set) => ({
  connected:         false,
  lastFrame:         null,
  roiCounts:         {},
  crossingTotals:    {},
  overallCrossings:  0,
  uniqueCrossers:    0,
  estimatedVehicles: 0,   // unique_crossers // 2 — accurate vehicle count
  globalUnique:      0,
  totalCars:         0,
  cameraHealth:      {},
  timestamp:         null,
  history:           [],  // [{ts, ...roiCounts}] last 120 points

  setConnected: (v) => set({ connected: v }),

  handleFrame: (payload) => set((s) => {
    const entry = { ts: payload.timestamp, ...payload.roi_counts }
    return {
      lastFrame:         payload.frame,
      roiCounts:         payload.roi_counts         || {},
      crossingTotals:    payload.crossing_totals    || {},
      overallCrossings:  payload.overall_crossings  || 0,
      uniqueCrossers:    payload.unique_crossers     || 0,
      estimatedVehicles: payload.estimated_vehicles  || 0,
      globalUnique:      payload.global_unique       || 0,
      totalCars:         payload.total_cars          || 0,
      cameraHealth:      payload.camera_health       || {},
      timestamp:         payload.timestamp,
      history:           [...s.history.slice(-119), entry],
    }
  }),
}))
