import { create } from 'zustand'
export const useStore = create((set) => ({
  mode:    'auto',
  sensors: null,
  disease: null,
  alerts:  [],
  setMode:    (mode)    => set({ mode }),
  setSensors: (sensors) => set({ sensors }),
  setDisease: (disease) => set({ disease }),
  setAlerts:  (alerts)  => set({ alerts }),
}))
