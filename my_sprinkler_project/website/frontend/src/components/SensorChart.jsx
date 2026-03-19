import React from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts'
export default function SensorChart({ data = [], field = 'ph' }) {
  return (
    <LineChart width={600} height={250} data={data}>
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis dataKey="recorded_at" hide />
      <YAxis />
      <Tooltip />
      <Legend />
      <Line type="monotone" dataKey={field} stroke="#8884d8" dot={false} />
    </LineChart>
  )
}
