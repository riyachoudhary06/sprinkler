import React, { useEffect, useState } from 'react'
import axios from 'axios'
const API = 'http://localhost:8000'
export default function LogViewer() {
  const [logs, setLogs] = useState([])
  useEffect(() => {
    axios.get(`${API}/logs/?limit=100`).then(r => setLogs(r.data))
  }, [])
  return (
    <div style={{ padding:24 }}>
      <h2>System Logs</h2>
      <div style={{ fontFamily:'monospace', fontSize:12, maxHeight:400,
                    overflowY:'auto', background:'#111', color:'#0f0', padding:12 }}>
        {logs.map((l, i) => <div key={i}>[{l.level}] {l.message}</div>)}
      </div>
    </div>
  )
}
