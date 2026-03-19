import { useEffect } from 'react'
import api from '../services/api'
import { useStore } from '../store'
export function useSensors(interval = 5000) {
  const setSensors = useStore(s => s.setSensors)
  useEffect(() => {
    const fetch = () => api.get('/sensors/latest').then(r => setSensors(r.data))
    fetch()
    const id = setInterval(fetch, interval)
    return () => clearInterval(id)
  }, [])
}
