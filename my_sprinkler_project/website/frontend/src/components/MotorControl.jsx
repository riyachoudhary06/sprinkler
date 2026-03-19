import React, { useState } from 'react'
import axios from 'axios'
const API = 'http://localhost:8000'
export default function MotorControl() {
  const [dosage, setDosage] = useState(20)
  const on  = () => axios.post(`${API}/motor/on?dosage_ml=${dosage}`)
  const off = () => axios.post(`${API}/motor/off`)
  return (
    <div style={{ padding:24 }}>
      <h2>Motor Control</h2>
      <label>Dosage (ml/m²): <input type="number" value={dosage}
        onChange={e => setDosage(e.target.value)} style={{ width:80 }} /></label>
      <br /><br />
      <button onClick={on}  style={{ background:'#4CAF50', color:'#fff', padding:'8px 20px', marginRight:12 }}>Spray ON</button>
      <button onClick={off} style={{ background:'#F44336', color:'#fff', padding:'8px 20px' }}>Spray OFF</button>
    </div>
  )
}
