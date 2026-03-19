import React from 'react'
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import HomePage      from './pages/HomePage'
import SensorsPage   from './pages/SensorsPage'
import CameraPage    from './pages/CameraPage'
import DiseasePage   from './pages/DiseasePage'
import MotorPage     from './pages/MotorPage'
import LogsPage      from './pages/LogsPage'
import SettingsPage  from './pages/SettingsPage'

export default function App() {
  return (
    <BrowserRouter>
      <nav style={{ display:'flex', gap:16, padding:'12px 24px',
                    background:'#1a1a2e', color:'#fff' }}>
        {['/', '/sensors', '/camera', '/disease',
          '/motor', '/logs', '/settings'].map((path, i) => (
          <NavLink key={path} to={path}
            style={({ isActive }) => ({ color: isActive ? '#4FC3F7' : '#ccc',
                                        textDecoration:'none', fontSize:14 })}>
            {['Dashboard','Sensors','Camera','Disease',
              'Motor','Logs','Settings'][i]}
          </NavLink>
        ))}
      </nav>
      <Routes>
        <Route path="/"          element={<HomePage />} />
        <Route path="/sensors"   element={<SensorsPage />} />
        <Route path="/camera"    element={<CameraPage />} />
        <Route path="/disease"   element={<DiseasePage />} />
        <Route path="/motor"     element={<MotorPage />} />
        <Route path="/logs"      element={<LogsPage />} />
        <Route path="/settings"  element={<SettingsPage />} />
      </Routes>
    </BrowserRouter>
  )
}
