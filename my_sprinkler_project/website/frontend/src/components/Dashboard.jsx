import React, { useEffect, useState } from 'react'
import axios from 'axios'
import SensorCard   from './SensorCard'
import DiseasePanel from './DiseasePanel'
import ModeToggle   from './ModeToggle'

const API = 'http://localhost:8000'

export default function Dashboard() {
  const [sensors, setSensors] = useState(null)
  const [disease, setDisease] = useState(null)

  useEffect(() => {
    const fetch = () => {
      axios.get(`${API}/sensors/latest`).then(r => setSensors(r.data))
      axios.get(`${API}/disease/latest`).then(r => setDisease(r.data))
    }
    fetch()
    const id = setInterval(fetch, 5000)
    return () => clearInterval(id)
  }, [])

  return (
    <div style={{ padding: 24 }}>
      <h1>Pesticide System Dashboard</h1>
      <ModeToggle />
      <SensorCard data={sensors} />
      <DiseasePanel data={disease} />
    </div>
  )
}
