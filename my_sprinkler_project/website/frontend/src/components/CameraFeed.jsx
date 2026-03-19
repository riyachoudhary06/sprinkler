import React from 'react'
const STREAM = 'http://raspberrypi.local:8080/stream'
export default function CameraFeed() {
  return (
    <div style={{ padding:24 }}>
      <h2>Live Camera Feed</h2>
      <img src={STREAM} alt="Live feed"
           style={{ width:'100%', maxWidth:640, borderRadius:8, border:'1px solid #ddd' }} />
    </div>
  )
}
