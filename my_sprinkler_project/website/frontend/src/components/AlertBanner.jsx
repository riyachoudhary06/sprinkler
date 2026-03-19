import React from 'react'
export default function AlertBanner({ alerts = [] }) {
  if (!alerts.length) return null
  return (
    <div style={{ background:'#fff3cd', border:'1px solid #ffc107',
                  borderRadius:6, padding:'10px 16px', margin:'8px 0' }}>
      {alerts.map((a, i) => (
        <div key={i}>⚠️ {a.sensor} is {a.type.replace('_',' ')} ({a.value})</div>
      ))}
    </div>
  )
}
