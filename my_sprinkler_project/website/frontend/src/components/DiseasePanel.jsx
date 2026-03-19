import React from 'react'
export default function DiseasePanel({ data }) {
  if (!data) return <p>No prediction yet.</p>
  const color = { low:'#4CAF50', medium:'#FF9800', high:'#F44336', none:'#9E9E9E' }
  return (
    <div style={{ background:'#fff8e1', borderRadius:8, padding:16, margin:'16px 0' }}>
      <h3>Latest Disease Detection</h3>
      <p><b>Disease:</b> {data.disease}</p>
      <p><b>Confidence:</b> {(data.confidence * 100).toFixed(1)}%</p>
      <p><b>Severity:</b> <span style={{ color: color[data.severity] }}>{data.severity}</span></p>
      <p><b>Affected area:</b> {data.affected_area}%</p>
      <p><b>Pesticide:</b> {data.pesticide}</p>
      <p><b>Dosage:</b> {data.dosage_ml} ml/m²</p>
      <p><i>{data.recommendation}</i></p>
    </div>
  )
}
