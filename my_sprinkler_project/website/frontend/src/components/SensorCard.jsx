import React from 'react'
export default function SensorCard({ data }) {
  if (!data) return <p>Loading sensors...</p>
  const fields = ['ph','moisture','nitrogen','phosphorus','potassium','temperature','humidity','light_lux']
  return (
    <div style={{ display:'flex', gap:12, flexWrap:'wrap', margin:'16px 0' }}>
      {fields.map(f => (
        <div key={f} style={{ background:'#f0f4ff', borderRadius:8, padding:'12px 16px', minWidth:120 }}>
          <div style={{ fontSize:11, color:'#666', textTransform:'uppercase' }}>{f.replace('_',' ')}</div>
          <div style={{ fontSize:22, fontWeight:600 }}>{data[f] ?? '—'}</div>
        </div>
      ))}
    </div>
  )
}
