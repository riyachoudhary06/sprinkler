import React, { useState } from 'react'
export default function ScheduleManager() {
  const [time, setTime]   = useState('06:00')
  const [dose, setDose]   = useState(20)
  const save = () => alert(`Schedule saved: ${time} @ ${dose} ml/m²`)
  return (
    <div style={{ padding:24 }}>
      <h2>Spray Schedule</h2>
      <label>Time: <input type="time" value={time} onChange={e => setTime(e.target.value)} /></label>
      <br /><br />
      <label>Dosage (ml/m²): <input type="number" value={dose} onChange={e => setDose(e.target.value)} /></label>
      <br /><br />
      <button onClick={save}>Save Schedule</button>
    </div>
  )
}
