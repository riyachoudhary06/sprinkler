import React, { useState } from 'react'
import axios from 'axios'
const API = 'http://localhost:8000'
export default function ModeToggle() {
  const [mode, setMode] = useState('auto')
  const toggle = () => {
    const next = mode === 'auto' ? 'manual' : 'auto'
    axios.post(`${API}/mode/${next}`).then(() => setMode(next))
  }
  return (
    <div style={{ margin:'8px 0' }}>
      <span>Mode: <b>{mode.toUpperCase()}</b></span>
      <button onClick={toggle} style={{ marginLeft:12, padding:'4px 16px' }}>Switch</button>
    </div>
  )
}
