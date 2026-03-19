import { useState, useEffect, useRef } from "react";

// ─── DESIGN TOKENS ───────────────────────────────────────────────────────────
const css = `
  @import url('https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&family=Syne:wght@400;600;700;800&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg:       #0d1208;
    --bg2:      #141a0e;
    --bg3:      #1c2514;
    --bg4:      #222d18;
    --surface:  #2a3620;
    --border:   #3a4a2a;
    --border2:  #4a5e38;
    --green:    #7db547;
    --green2:   #a3d15e;
    --green-dim:#4a7030;
    --amber:    #d4a017;
    --amber2:   #f0be3a;
    --amber-dim:#7a5c0a;
    --red:      #c94040;
    --red2:     #e86060;
    --teal:     #3cb4a0;
    --teal2:    #5cd4be;
    --text:     #dde8cc;
    --text2:    #8fa878;
    --text3:    #5a6e48;
    --mono:     'Space Mono', monospace;
    --sans:     'Syne', sans-serif;
  }

  html, body, #root { height: 100%; background: var(--bg); color: var(--text); }

  ::-webkit-scrollbar { width: 4px; }
  ::-webkit-scrollbar-track { background: var(--bg2); }
  ::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 2px; }

  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
  @keyframes spin  { to { transform: rotate(360deg); } }
  @keyframes fadeUp { from { opacity:0; transform:translateY(12px); } to { opacity:1; transform:translateY(0); } }
  @keyframes scan {
    0%   { transform: translateY(-100%); opacity: 0.6; }
    100% { transform: translateY(400%); opacity: 0; }
  }
  @keyframes blink { 0%,100%{opacity:1} 49%{opacity:1} 50%{opacity:0} 99%{opacity:0} }
  @keyframes dash { to { stroke-dashoffset: 0; } }
  @keyframes glow { 0%,100%{box-shadow:0 0 8px var(--green-dim)} 50%{box-shadow:0 0 24px var(--green2)} }
`;

// ─── MOCK DATA ────────────────────────────────────────────────────────────────
const mockSensors = {
  ph: 6.4, moisture: 62, nitrogen: 180, phosphorus: 45, potassium: 210,
  temperature: 28.3, humidity: 74, light_lux: 42000,
};
const mockDisease = {
  disease: "Leaf Blight", confidence: 0.87, severity: "medium",
  affected_area: 34, recommendation: "Apply copper-based fungicide to affected zones immediately.",
  pesticide: "Copper Oxychloride", dosage_ml: 28.5,
};
const mockHistory = Array.from({ length: 24 }, (_, i) => ({
  time: `${String(i).padStart(2,"0")}:00`,
  ph: 5.8 + Math.random() * 1.4,
  moisture: 50 + Math.random() * 30,
  temperature: 24 + Math.random() * 8,
  humidity: 60 + Math.random() * 20,
}));
const mockLogs = [
  { level:"INFO",  time:"14:32:01", msg:"Sensor poll completed — all values nominal", source:"sensor_manager" },
  { level:"WARN",  time:"14:28:44", msg:"Soil moisture below threshold: 48% < 50%", source:"alert_service" },
  { level:"INFO",  time:"14:25:11", msg:"Gemini inference: Leaf Blight detected (87% conf.)", source:"disease_detector" },
  { level:"INFO",  time:"14:25:09", msg:"Camera snapshot captured: capture_1718123109.jpg", source:"capture" },
  { level:"INFO",  time:"14:20:00", msg:"Motor activated — dosage 28.5 ml/m²", source:"motor_control" },
  { level:"INFO",  time:"14:19:58", msg:"Command received: motor ON", source:"command_handler" },
  { level:"ERROR", time:"13:55:02", msg:"NPK sensor timeout — retrying in 5s", source:"npk_sensor" },
  { level:"INFO",  time:"13:55:07", msg:"NPK sensor recovered: N=180 P=45 K=210", source:"npk_sensor" },
  { level:"INFO",  time:"13:40:00", msg:"Mode switched: auto → manual by user", source:"routes_mode" },
  { level:"INFO",  time:"13:00:00", msg:"System boot complete — all threads started", source:"main" },
];
const mockPredictions = [
  { disease:"Leaf Blight",     confidence:0.87, severity:"medium", time:"14:25", dosage:28.5 },
  { disease:"Healthy",         confidence:0.95, severity:"none",   time:"13:55", dosage:0 },
  { disease:"Powdery Mildew",  confidence:0.78, severity:"low",    time:"12:00", dosage:12.0 },
  { disease:"Bacterial Spot",  confidence:0.91, severity:"high",   time:"10:30", dosage:52.0 },
  { disease:"Healthy",         confidence:0.98, severity:"none",   time:"09:00", dosage:0 },
];
const schedules = [
  { time:"06:00", days:"Mon Wed Fri", dosage:20, active:true },
  { time:"18:00", days:"Daily",       dosage:15, active:false },
];

// ─── SHARED COMPONENTS ────────────────────────────────────────────────────────

function Tag({ children, color = "green" }) {
  const colors = {
    green: { bg:"rgba(125,181,71,.15)", border:"rgba(125,181,71,.4)", text:"var(--green2)" },
    amber: { bg:"rgba(212,160,23,.15)", border:"rgba(212,160,23,.4)", text:"var(--amber2)" },
    red:   { bg:"rgba(201,64,64,.15)",  border:"rgba(201,64,64,.4)",  text:"var(--red2)"  },
    teal:  { bg:"rgba(60,180,160,.15)", border:"rgba(60,180,160,.4)", text:"var(--teal2)" },
    dim:   { bg:"rgba(90,110,72,.1)",   border:"rgba(90,110,72,.3)",  text:"var(--text2)" },
  };
  const c = colors[color] || colors.green;
  return (
    <span style={{
      background: c.bg, border: `1px solid ${c.border}`, color: c.text,
      fontFamily:"var(--mono)", fontSize:10, padding:"2px 8px", borderRadius:2,
      letterSpacing:"0.08em", textTransform:"uppercase", fontWeight:700,
    }}>{children}</span>
  );
}

function Card({ children, style = {}, glow = false }) {
  return (
    <div style={{
      background:"var(--bg2)", border:"1px solid var(--border)",
      borderRadius:4, padding:20,
      boxShadow: glow ? "0 0 20px rgba(125,181,71,.08), inset 0 1px 0 rgba(125,181,71,.1)" : "none",
      animation: glow ? "glow 3s ease-in-out infinite" : "none",
      ...style,
    }}>{children}</div>
  );
}

function Label({ children }) {
  return (
    <div style={{
      fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)",
      letterSpacing:"0.15em", textTransform:"uppercase", marginBottom:6,
    }}>{children}</div>
  );
}

function Val({ children, size = 28, color = "var(--text)" }) {
  return (
    <div style={{
      fontFamily:"var(--mono)", fontSize:size, fontWeight:700, color,
      lineHeight:1, letterSpacing:"-0.02em",
    }}>{children}</div>
  );
}

function StatusDot({ active }) {
  return (
    <span style={{
      display:"inline-block", width:7, height:7, borderRadius:"50%",
      background: active ? "var(--green)" : "var(--text3)",
      boxShadow: active ? "0 0 8px var(--green)" : "none",
      animation: active ? "pulse 2s ease-in-out infinite" : "none",
      marginRight:6,
    }}/>
  );
}

function ProgressBar({ value, max = 100, color = "var(--green)", height = 4 }) {
  return (
    <div style={{ background:"var(--bg4)", borderRadius:2, height, overflow:"hidden" }}>
      <div style={{
        width:`${Math.min((value/max)*100, 100)}%`, height:"100%",
        background:color, borderRadius:2,
        transition:"width .6s cubic-bezier(.4,0,.2,1)",
      }}/>
    </div>
  );
}

function MiniChart({ data, field, color = "var(--green)", height = 48 }) {
  const w = 200, h = height;
  const vals = data.map(d => d[field]);
  const min = Math.min(...vals), max = Math.max(...vals);
  const range = max - min || 1;
  const pts = vals.map((v, i) => {
    const x = (i / (vals.length - 1)) * w;
    const y = h - ((v - min) / range) * h * 0.85 - h * 0.05;
    return `${x},${y}`;
  }).join(" ");
  const area = `0,${h} ` + pts + ` ${w},${h}`;
  return (
    <svg width="100%" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" style={{ display:"block" }}>
      <defs>
        <linearGradient id={`g${field}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.3"/>
          <stop offset="100%" stopColor={color} stopOpacity="0"/>
        </linearGradient>
      </defs>
      <polygon points={area} fill={`url(#g${field})`}/>
      <polyline points={pts} fill="none" stroke={color} strokeWidth="1.5" strokeLinejoin="round"/>
    </svg>
  );
}

function Toggle({ value, onChange, label }) {
  return (
    <div style={{ display:"flex", alignItems:"center", gap:10, cursor:"pointer" }}
         onClick={() => onChange(!value)}>
      <div style={{
        width:40, height:22, borderRadius:11, position:"relative",
        background: value ? "var(--green)" : "var(--surface)",
        border:`1px solid ${value ? "var(--green2)" : "var(--border)"}`,
        transition:"all .2s",
      }}>
        <div style={{
          position:"absolute", top:2, left: value ? 18 : 2, width:16, height:16,
          borderRadius:"50%", background:"#fff", transition:"left .2s",
          boxShadow:"0 1px 4px rgba(0,0,0,.4)",
        }}/>
      </div>
      {label && <span style={{ fontFamily:"var(--mono)", fontSize:12, color:"var(--text2)" }}>{label}</span>}
    </div>
  );
}

function Btn({ children, onClick, variant = "primary", small = false, style: sx = {} }) {
  const styles = {
    primary: { bg:"var(--green-dim)", border:"var(--green)", color:"var(--green2)", hover:"rgba(125,181,71,.25)" },
    amber:   { bg:"var(--amber-dim)", border:"var(--amber)", color:"var(--amber2)", hover:"rgba(212,160,23,.25)" },
    red:     { bg:"rgba(201,64,64,.15)", border:"var(--red)", color:"var(--red2)", hover:"rgba(201,64,64,.25)" },
    ghost:   { bg:"transparent", border:"var(--border2)", color:"var(--text2)", hover:"var(--surface)" },
  };
  const s = styles[variant];
  const [hover, setHover] = useState(false);
  return (
    <button
      onClick={onClick}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        background: hover ? s.hover : s.bg,
        border:`1px solid ${s.border}`, color:s.color,
        fontFamily:"var(--mono)", fontSize: small ? 10 : 11,
        padding: small ? "5px 12px" : "9px 18px",
        borderRadius:3, cursor:"pointer", letterSpacing:"0.06em",
        textTransform:"uppercase", fontWeight:700, transition:"all .15s",
        ...sx,
      }}
    >{children}</button>
  );
}

// ─── SIDEBAR ──────────────────────────────────────────────────────────────────
const NAV = [
  { id:"dashboard", icon:"◈", label:"Dashboard"  },
  { id:"sensors",   icon:"◉", label:"Sensors"    },
  { id:"camera",    icon:"⬡", label:"Camera"     },
  { id:"disease",   icon:"◍", label:"Disease"    },
  { id:"motor",     icon:"⬢", label:"Motor"      },
  { id:"logs",      icon:"≡",  label:"Logs"       },
  { id:"settings",  icon:"⚙", label:"Settings"   },
];

function Sidebar({ page, setPage }) {
  return (
    <div style={{
      width:64, minHeight:"100vh", background:"var(--bg2)",
      borderRight:"1px solid var(--border)", display:"flex",
      flexDirection:"column", alignItems:"center", paddingTop:16, gap:2,
      position:"fixed", top:0, left:0, zIndex:100,
    }}>
      {/* logo */}
      <div style={{
        width:36, height:36, background:"var(--green-dim)", border:"1px solid var(--green)",
        borderRadius:4, display:"flex", alignItems:"center", justifyContent:"center",
        marginBottom:20,
      }}>
        <span style={{ fontSize:16, color:"var(--green2)" }}>🌿</span>
      </div>
      {NAV.map(n => (
        <button key={n.id} title={n.label} onClick={() => setPage(n.id)}
          style={{
            width:44, height:44, borderRadius:4, border:"none", cursor:"pointer",
            background: page===n.id ? "var(--surface)" : "transparent",
            color: page===n.id ? "var(--green2)" : "var(--text3)",
            fontSize:16, display:"flex", alignItems:"center", justifyContent:"center",
            transition:"all .15s",
            boxShadow: page===n.id ? `inset 2px 0 0 var(--green), 0 0 12px rgba(125,181,71,.12)` : "none",
          }}>
          {n.icon}
        </button>
      ))}
      <div style={{ marginTop:"auto", paddingBottom:16 }}>
        <StatusDot active />
      </div>
    </div>
  );
}

// ─── TOP BAR ─────────────────────────────────────────────────────────────────
function TopBar({ page, mode, setMode }) {
  const [time, setTime] = useState(new Date());
  useEffect(() => { const id = setInterval(() => setTime(new Date()), 1000); return () => clearInterval(id); }, []);
  const label = NAV.find(n => n.id === page)?.label || "";
  return (
    <div style={{
      height:52, background:"var(--bg2)", borderBottom:"1px solid var(--border)",
      display:"flex", alignItems:"center", padding:"0 20px 0 0",
      position:"fixed", top:0, left:64, right:0, zIndex:99, gap:16,
    }}>
      <div style={{
        height:"100%", padding:"0 20px", borderRight:"1px solid var(--border)",
        display:"flex", alignItems:"center", gap:10, minWidth:200,
      }}>
        <span style={{ fontFamily:"var(--sans)", fontWeight:800, fontSize:13, letterSpacing:"0.08em", color:"var(--text)" }}>
          AGRI·WATCH
        </span>
        <span style={{ color:"var(--border2)", fontSize:10 }}>◦</span>
        <span style={{ fontFamily:"var(--mono)", fontSize:10, color:"var(--text2)", letterSpacing:"0.1em", textTransform:"uppercase" }}>
          {label}
        </span>
      </div>
      <div style={{ flex:1 }} />
      {/* mode toggle */}
      <div style={{ display:"flex", alignItems:"center", gap:8 }}>
        <span style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)", letterSpacing:"0.1em" }}>MODE</span>
        <div style={{ display:"flex", background:"var(--bg4)", border:"1px solid var(--border)", borderRadius:3, overflow:"hidden" }}>
          {["auto","manual"].map(m => (
            <button key={m} onClick={() => setMode(m)} style={{
              padding:"5px 12px", fontFamily:"var(--mono)", fontSize:10, border:"none",
              cursor:"pointer", letterSpacing:"0.08em", textTransform:"uppercase", fontWeight:700,
              background: mode===m ? (m==="auto" ? "var(--green-dim)" : "var(--amber-dim)") : "transparent",
              color: mode===m ? (m==="auto" ? "var(--green2)" : "var(--amber2)") : "var(--text3)",
              transition:"all .15s",
            }}>{m}</button>
          ))}
        </div>
      </div>
      <div style={{
        fontFamily:"var(--mono)", fontSize:11, color:"var(--text2)",
        letterSpacing:"0.06em", borderLeft:"1px solid var(--border)", paddingLeft:16,
        animation:"blink 1s step-start infinite",
      }}>
        {time.toLocaleTimeString("en-GB", { hour12:false })}
      </div>
      <div style={{ display:"flex", alignItems:"center", gap:6 }}>
        <StatusDot active />
        <span style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)" }}>LIVE</span>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// PAGE: DASHBOARD
// ═══════════════════════════════════════════════════════════════════════════════
function Dashboard({ mode, setPage }) {
  const [tick, setTick] = useState(0);
  useEffect(() => { const id = setInterval(() => setTick(t => t+1), 3000); return () => clearInterval(id); }, []);

  const sensors = {
    ...mockSensors,
    moisture: mockSensors.moisture + (Math.sin(tick)*3),
    temperature: +(mockSensors.temperature + Math.sin(tick*0.7)*0.3).toFixed(1),
  };

  const sevColor = { none:"green", low:"teal", medium:"amber", high:"red" };

  return (
    <div style={{ padding:24, animation:"fadeUp .4s ease both" }}>
      {/* header strip */}
      <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:24 }}>
        <div>
          <h1 style={{ fontFamily:"var(--sans)", fontSize:22, fontWeight:800, color:"var(--text)", letterSpacing:"-0.02em" }}>
            Field Overview
          </h1>
          <div style={{ fontFamily:"var(--mono)", fontSize:10, color:"var(--text3)", marginTop:3 }}>
            PLOT-A · ZONE-1 · {new Date().toLocaleDateString("en-GB", { weekday:"long", year:"numeric", month:"long", day:"numeric" })}
          </div>
        </div>
        <div style={{ display:"flex", gap:8 }}>
          <Tag color={mode==="auto" ? "green" : "amber"}>{mode} mode</Tag>
          <Tag color="teal">MQTT ●</Tag>
        </div>
      </div>

      {/* top stat row */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:12, marginBottom:16 }}>
        {[
          { label:"Soil pH",       val:sensors.ph.toFixed(1),    unit:"",    color:"var(--teal2)",  ok: sensors.ph >= 5.5 && sensors.ph <= 7.5 },
          { label:"Soil Moisture", val:Math.round(sensors.moisture), unit:"%", color:"var(--green2)", ok: sensors.moisture >= 40 },
          { label:"Air Temp",      val:sensors.temperature,       unit:"°C",  color:"var(--amber2)", ok: sensors.temperature < 35 },
          { label:"Humidity",      val:sensors.humidity,          unit:"%",   color:"var(--text2)",  ok: true },
        ].map(s => (
          <Card key={s.label} style={{ position:"relative", overflow:"hidden" }}>
            <div style={{ position:"absolute", top:0, right:0, width:3, height:"100%",
                          background: s.ok ? "var(--green)" : "var(--red)", borderRadius:"0 4px 4px 0" }}/>
            <Label>{s.label}</Label>
            <div style={{ display:"flex", alignItems:"baseline", gap:4 }}>
              <Val size={32} color={s.color}>{s.val}</Val>
              <span style={{ fontFamily:"var(--mono)", fontSize:12, color:"var(--text3)" }}>{s.unit}</span>
            </div>
            <div style={{ marginTop:10 }}>
              <ProgressBar value={parseFloat(s.val)} max={s.label==="Soil pH" ? 14 : 100}
                           color={s.ok ? s.color : "var(--red)"} />
            </div>
          </Card>
        ))}
      </div>

      {/* main content: NPK + disease + chart */}
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:12, marginBottom:16 }}>

        {/* NPK */}
        <Card>
          <Label>NPK Levels — mg/kg</Label>
          <div style={{ marginTop:12, display:"flex", flexDirection:"column", gap:12 }}>
            {[
              { label:"N — Nitrogen",   val:sensors.nitrogen,   max:300, color:"var(--green2)"  },
              { label:"P — Phosphorus", val:sensors.phosphorus, max:150, color:"var(--amber2)"  },
              { label:"K — Potassium",  val:sensors.potassium,  max:350, color:"var(--teal2)"   },
            ].map(n => (
              <div key={n.label}>
                <div style={{ display:"flex", justifyContent:"space-between", marginBottom:5 }}>
                  <span style={{ fontFamily:"var(--mono)", fontSize:10, color:"var(--text2)" }}>{n.label}</span>
                  <span style={{ fontFamily:"var(--mono)", fontSize:10, color:n.color, fontWeight:700 }}>{n.val}</span>
                </div>
                <ProgressBar value={n.val} max={n.max} color={n.color} height={6} />
              </div>
            ))}
          </div>
        </Card>

        {/* Disease alert */}
        <Card style={{ borderColor: mockDisease.severity==="high" ? "var(--red)" :
                                    mockDisease.severity==="medium" ? "rgba(212,160,23,.4)" : "var(--border)" }}>
          <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start" }}>
            <Label>Latest Detection</Label>
            <Tag color={sevColor[mockDisease.severity]}>{mockDisease.severity}</Tag>
          </div>
          <div style={{ marginTop:10 }}>
            <div style={{ fontFamily:"var(--sans)", fontSize:16, fontWeight:700, color:"var(--amber2)", marginBottom:4 }}>
              {mockDisease.disease}
            </div>
            <div style={{ fontFamily:"var(--mono)", fontSize:10, color:"var(--text2)", marginBottom:12, lineHeight:1.6 }}>
              {mockDisease.recommendation}
            </div>
            <div style={{ display:"flex", gap:16 }}>
              <div>
                <Label>Confidence</Label>
                <Val size={18} color="var(--green2)">{(mockDisease.confidence*100).toFixed(0)}%</Val>
              </div>
              <div>
                <Label>Affected</Label>
                <Val size={18} color="var(--amber2)">{mockDisease.affected_area}%</Val>
              </div>
              <div>
                <Label>Dosage</Label>
                <Val size={18} color="var(--teal2)">{mockDisease.dosage_ml} ml</Val>
              </div>
            </div>
          </div>
          <div style={{ marginTop:12 }}>
            <Btn onClick={() => setPage("disease")} small>View Details →</Btn>
          </div>
        </Card>

        {/* quick motor */}
        <Card>
          <Label>Motor Status</Label>
          <div style={{ textAlign:"center", padding:"16px 0" }}>
            <div style={{
              width:72, height:72, borderRadius:"50%", margin:"0 auto 12px",
              border:"2px solid var(--border2)",
              background:"var(--bg3)", display:"flex", alignItems:"center", justifyContent:"center",
              fontSize:28, position:"relative",
            }}>
              💧
              <div style={{
                position:"absolute", inset:-4, borderRadius:"50%",
                border:"2px solid var(--green)", opacity:0.3,
                animation: mode==="auto" ? "pulse 2s ease infinite" : "none",
              }}/>
            </div>
            <div style={{ fontFamily:"var(--mono)", fontSize:10, color:"var(--text3)", marginBottom:8 }}>
              PUMP · IDLE
            </div>
            <div style={{ display:"flex", gap:8, justifyContent:"center" }}>
              <Btn onClick={() => setPage("motor")} small>Control →</Btn>
            </div>
          </div>
          <div style={{ borderTop:"1px solid var(--border)", paddingTop:12 }}>
            <div style={{ display:"flex", justifyContent:"space-between" }}>
              <div>
                <Label>Last Spray</Label>
                <div style={{ fontFamily:"var(--mono)", fontSize:11, color:"var(--text2)" }}>14:20 · 42ml</div>
              </div>
              <div style={{ textAlign:"right" }}>
                <Label>Total Today</Label>
                <div style={{ fontFamily:"var(--mono)", fontSize:11, color:"var(--green2)" }}>1.2 L</div>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* sparkline row */}
      <Card>
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:16 }}>
          <Label>24-Hour Sensor History</Label>
          <div style={{ display:"flex", gap:12 }}>
            {[
              { label:"Moisture", color:"var(--green2)" },
              { label:"Temp °C", color:"var(--amber2)" },
              { label:"Humidity", color:"var(--teal2)" },
            ].map(l => (
              <div key={l.label} style={{ display:"flex", alignItems:"center", gap:5 }}>
                <div style={{ width:12, height:2, background:l.color, borderRadius:1 }}/>
                <span style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)" }}>{l.label}</span>
              </div>
            ))}
          </div>
        </div>
        <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:12 }}>
          {[
            { field:"moisture",    color:"var(--green2)" },
            { field:"temperature", color:"var(--amber2)" },
            { field:"humidity",    color:"var(--teal2)"  },
          ].map(c => (
            <div key={c.field} style={{ height:60 }}>
              <MiniChart data={mockHistory} field={c.field} color={c.color} height={60} />
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// PAGE: SENSORS
// ═══════════════════════════════════════════════════════════════════════════════
function Sensors() {
  const [selected, setSelected] = useState("moisture");
  const fields = [
    { key:"ph",          label:"Soil pH",         val:mockSensors.ph,          unit:"",     min:0,   max:14,  ok:[5.5,7.5],  color:"var(--teal2)"  },
    { key:"moisture",    label:"Soil Moisture",    val:mockSensors.moisture,    unit:"%",    min:0,   max:100, ok:[40,80],    color:"var(--green2)" },
    { key:"nitrogen",    label:"Nitrogen (N)",     val:mockSensors.nitrogen,    unit:"mg/kg",min:0,   max:300, ok:[100,250],  color:"var(--green2)" },
    { key:"phosphorus",  label:"Phosphorus (P)",   val:mockSensors.phosphorus,  unit:"mg/kg",min:0,   max:150, ok:[30,100],   color:"var(--amber2)" },
    { key:"potassium",   label:"Potassium (K)",    val:mockSensors.potassium,   unit:"mg/kg",min:0,   max:350, ok:[150,300],  color:"var(--teal2)"  },
    { key:"temperature", label:"Air Temperature",  val:mockSensors.temperature, unit:"°C",   min:0,   max:50,  ok:[20,35],    color:"var(--amber2)" },
    { key:"humidity",    label:"Air Humidity",     val:mockSensors.humidity,    unit:"%",    min:0,   max:100, ok:[40,85],    color:"var(--teal2)"  },
    { key:"light_lux",   label:"Light Intensity",  val:mockSensors.light_lux,   unit:"lux",  min:0,   max:80000, ok:[10000,70000], color:"var(--amber2)" },
  ];
  const sel = fields.find(f => f.key === selected);
  const isOk = v => v >= sel.ok[0] && v <= sel.ok[1];

  return (
    <div style={{ padding:24, animation:"fadeUp .4s ease both" }}>
      <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:24 }}>
        <h1 style={{ fontFamily:"var(--sans)", fontSize:22, fontWeight:800 }}>Sensor Readings</h1>
        <div style={{ display:"flex", gap:8 }}>
          <Tag color="green">All Online</Tag>
          <div style={{ fontFamily:"var(--mono)", fontSize:10, color:"var(--text3)", display:"flex", alignItems:"center", gap:6 }}>
            <StatusDot active />POLLING · 5s
          </div>
        </div>
      </div>

      <div style={{ display:"grid", gridTemplateColumns:"1fr 1.5fr", gap:16 }}>
        {/* sensor list */}
        <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
          {fields.map(f => {
            const ok = f.val >= f.ok[0] && f.val <= f.ok[1];
            return (
              <button key={f.key} onClick={() => setSelected(f.key)}
                style={{
                  background: selected===f.key ? "var(--surface)" : "var(--bg2)",
                  border:`1px solid ${selected===f.key ? "var(--green)" : "var(--border)"}`,
                  borderRadius:4, padding:"14px 16px", cursor:"pointer", textAlign:"left",
                  display:"flex", alignItems:"center", gap:14,
                  transition:"all .15s",
                }}>
                <div style={{
                  width:4, height:36, borderRadius:2,
                  background: ok ? f.color : "var(--red)",
                }}/>
                <div style={{ flex:1 }}>
                  <div style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)", letterSpacing:"0.1em", marginBottom:3 }}>
                    {f.label.toUpperCase()}
                  </div>
                  <div style={{ fontFamily:"var(--mono)", fontSize:18, fontWeight:700, color: ok ? f.color : "var(--red2)" }}>
                    {typeof f.val === "number" && f.val > 1000 ? f.val.toLocaleString() : f.val}
                    <span style={{ fontSize:11, fontWeight:400, color:"var(--text3)", marginLeft:4 }}>{f.unit}</span>
                  </div>
                </div>
                <Tag color={ok ? "dim" : "red"}>{ok ? "OK" : "ALERT"}</Tag>
              </button>
            );
          })}
        </div>

        {/* detail panel */}
        <div style={{ display:"flex", flexDirection:"column", gap:12 }}>
          <Card glow style={{ flex:"none" }}>
            <div style={{ display:"flex", justifyContent:"space-between", marginBottom:16 }}>
              <div>
                <Label>{sel.label}</Label>
                <div style={{ display:"flex", alignItems:"baseline", gap:8, marginTop:4 }}>
                  <Val size={48} color={sel.color}>
                    {typeof sel.val === "number" && sel.val > 1000 ? sel.val.toLocaleString() : sel.val}
                  </Val>
                  <span style={{ fontFamily:"var(--mono)", fontSize:14, color:"var(--text3)" }}>{sel.unit}</span>
                </div>
              </div>
              <Tag color={isOk(sel.val) ? "green" : "red"}>{isOk(sel.val) ? "NOMINAL" : "OUT OF RANGE"}</Tag>
            </div>
            {/* range viz */}
            <div style={{ position:"relative", height:8, background:"var(--bg4)", borderRadius:4, marginBottom:8 }}>
              <div style={{
                position:"absolute", left:`${(sel.ok[0]/sel.max)*100}%`,
                width:`${((sel.ok[1]-sel.ok[0])/sel.max)*100}%`,
                height:"100%", background:"rgba(125,181,71,.2)", borderRadius:4,
              }}/>
              <div style={{
                position:"absolute", left:`${(Math.min(sel.val,sel.max)/sel.max)*100}%`,
                transform:"translateX(-50%)", top:-3, width:14, height:14,
                borderRadius:"50%", background: isOk(sel.val) ? sel.color : "var(--red2)",
                border:"2px solid var(--bg2)", boxShadow:`0 0 8px ${isOk(sel.val) ? sel.color : "var(--red)"}`,
              }}/>
            </div>
            <div style={{ display:"flex", justifyContent:"space-between", fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)" }}>
              <span>{sel.min}</span>
              <span>Optimal: {sel.ok[0]}–{sel.ok[1]} {sel.unit}</span>
              <span>{sel.max}</span>
            </div>
          </Card>

          <Card>
            <Label>24-Hour Trend</Label>
            <div style={{ height:120, marginTop:12 }}>
              <MiniChart data={mockHistory} field={sel.key === "nitrogen" || sel.key === "phosphorus" || sel.key === "potassium" || sel.key === "light_lux" ? "moisture" : sel.key} color={sel.color} height={120} />
            </div>
            <div style={{ display:"flex", justifyContent:"space-between", marginTop:8, fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)" }}>
              <span>00:00</span><span>06:00</span><span>12:00</span><span>18:00</span><span>Now</span>
            </div>
          </Card>

          <Card>
            <Label>Statistics</Label>
            <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:12, marginTop:10 }}>
              {[
                { l:"Min", v: (sel.val * 0.88).toFixed(1) },
                { l:"Avg", v: (sel.val * 0.97).toFixed(1) },
                { l:"Max", v: (sel.val * 1.06).toFixed(1) },
              ].map(s => (
                <div key={s.l} style={{ textAlign:"center", background:"var(--bg3)", borderRadius:4, padding:"10px 0" }}>
                  <Label>{s.l}</Label>
                  <Val size={16} color="var(--text)">{s.v}</Val>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// PAGE: CAMERA
// ═══════════════════════════════════════════════════════════════════════════════
function Camera() {
  const [capturing, setCapturing] = useState(false);
  const [lastCapture, setLastCapture] = useState("14:25:09");
  const [scanLine, setScanLine] = useState(false);

  const handleCapture = () => {
    setCapturing(true);
    setScanLine(true);
    setTimeout(() => {
      setLastCapture(new Date().toLocaleTimeString("en-GB", { hour12:false }));
      setCapturing(false);
      setScanLine(false);
    }, 1800);
  };

  return (
    <div style={{ padding:24, animation:"fadeUp .4s ease both" }}>
      <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:24 }}>
        <h1 style={{ fontFamily:"var(--sans)", fontSize:22, fontWeight:800 }}>Camera Feed</h1>
        <div style={{ display:"flex", gap:8, alignItems:"center" }}>
          <Tag color="red">● LIVE</Tag>
          <Tag color="dim">640×480 · 30fps</Tag>
        </div>
      </div>

      <div style={{ display:"grid", gridTemplateColumns:"1fr 280px", gap:16 }}>
        {/* main feed */}
        <div>
          <div style={{
            background:"var(--bg3)", border:"1px solid var(--border)", borderRadius:4,
            aspectRatio:"4/3", position:"relative", overflow:"hidden",
          }}>
            {/* simulated plant feed */}
            <div style={{
              position:"absolute", inset:0,
              background:"linear-gradient(160deg, #0d2010 0%, #1a3a15 40%, #0d2010 100%)",
              display:"flex", alignItems:"center", justifyContent:"center",
            }}>
              <div style={{ fontSize:80, filter:"saturate(0.6) brightness(0.7)" }}>🌿</div>
              {/* scanline overlay */}
              {scanLine && (
                <div style={{
                  position:"absolute", left:0, right:0, height:3,
                  background:"rgba(125,181,71,.8)", boxShadow:"0 0 12px var(--green)",
                  animation:"scan 1.5s linear",
                }}/>
              )}
            </div>
            {/* overlay hud */}
            <div style={{ position:"absolute", top:12, left:12, right:12,
                          display:"flex", justifyContent:"space-between", alignItems:"flex-start" }}>
              <div style={{
                background:"rgba(13,18,8,.7)", border:"1px solid var(--border)",
                borderRadius:3, padding:"5px 10px",
                fontFamily:"var(--mono)", fontSize:9, color:"var(--green2)", letterSpacing:"0.08em",
              }}>
                <StatusDot active />STREAMING · Pi Camera v2
              </div>
              <div style={{
                background:"rgba(13,18,8,.7)", border:"1px solid var(--border)",
                borderRadius:3, padding:"5px 10px",
                fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)",
              }}>
                {new Date().toLocaleTimeString("en-GB", { hour12:false })}
              </div>
            </div>
            {/* corner brackets */}
            {[["top:8px","left:8px","borderTop","borderLeft"],
              ["top:8px","right:8px","borderTop","borderRight"],
              ["bottom:8px","left:8px","borderBottom","borderLeft"],
              ["bottom:8px","right:8px","borderBottom","borderRight"]].map((c,i) => (
              <div key={i} style={{
                position:"absolute", [c[0].split(":")[0]]:c[0].split(":")[1],
                [c[1].split(":")[0]]:c[1].split(":")[1],
                width:20, height:20, [c[2]]:"2px solid var(--green)", [c[3]]:"2px solid var(--green)",
              }}/>
            ))}
          </div>
          <div style={{ display:"flex", gap:8, marginTop:12 }}>
            <Btn onClick={handleCapture} variant={capturing ? "ghost" : "primary"}>
              {capturing ? "Capturing..." : "⬡ Capture Snapshot"}
            </Btn>
            <Btn variant="ghost">⇄ Rotate</Btn>
            <Btn variant="ghost">⛶ Fullscreen</Btn>
          </div>
        </div>

        {/* sidebar */}
        <div style={{ display:"flex", flexDirection:"column", gap:12 }}>
          <Card>
            <Label>Stream Info</Label>
            <div style={{ display:"flex", flexDirection:"column", gap:8, marginTop:10 }}>
              {[
                { l:"URL",        v:"raspberrypi.local:8080" },
                { l:"Resolution", v:"640 × 480 px" },
                { l:"Format",     v:"MJPEG" },
                { l:"Quality",    v:"85%" },
                { l:"Last Capture", v:lastCapture },
              ].map(r => (
                <div key={r.l} style={{ display:"flex", justifyContent:"space-between", borderBottom:"1px solid var(--bg4)", paddingBottom:6 }}>
                  <span style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)" }}>{r.l}</span>
                  <span style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text2)" }}>{r.v}</span>
                </div>
              ))}
            </div>
          </Card>

          <Card>
            <Label>Capture Gallery</Label>
            <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:6, marginTop:10 }}>
              {["14:25","13:55","12:00","10:30"].map((t, i) => (
                <div key={t} style={{
                  background:"var(--bg3)", border:"1px solid var(--border)", borderRadius:3,
                  aspectRatio:"4/3", display:"flex", flexDirection:"column",
                  alignItems:"center", justifyContent:"center", cursor:"pointer",
                  position:"relative", overflow:"hidden",
                }}>
                  <span style={{ fontSize:22, filter:"saturate(0.4) brightness(0.5)" }}>🌿</span>
                  <div style={{
                    position:"absolute", bottom:0, left:0, right:0,
                    background:"rgba(0,0,0,.6)", padding:"3px 5px", textAlign:"center",
                    fontFamily:"var(--mono)", fontSize:8, color:"var(--text3)",
                  }}>{t}</div>
                </div>
              ))}
            </div>
          </Card>

          <Card>
            <Label>Auto-Capture</Label>
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginTop:10 }}>
              <span style={{ fontFamily:"var(--mono)", fontSize:10, color:"var(--text2)" }}>Every 30s</span>
              <Toggle value={true} onChange={() => {}} />
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// PAGE: DISEASE
// ═══════════════════════════════════════════════════════════════════════════════
function Disease() {
  const [analyzing, setAnalyzing] = useState(false);
  const [progress, setProgress] = useState(0);

  const analyze = () => {
    setAnalyzing(true); setProgress(0);
    const steps = [10,30,55,75,90,100];
    steps.forEach((s, i) => setTimeout(() => {
      setProgress(s);
      if (s === 100) setTimeout(() => setAnalyzing(false), 400);
    }, i * 300));
  };

  const sevColor = { none:"teal", low:"green", medium:"amber", high:"red" };

  return (
    <div style={{ padding:24, animation:"fadeUp .4s ease both" }}>
      <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:24 }}>
        <h1 style={{ fontFamily:"var(--sans)", fontSize:22, fontWeight:800 }}>Disease Detection</h1>
        <div style={{ display:"flex", gap:8, alignItems:"center" }}>
          <Tag color="dim">Gemini 1.5 Flash</Tag>
          <Btn onClick={analyze} variant={analyzing ? "ghost" : "amber"}>
            {analyzing ? `Analyzing... ${progress}%` : "◈ Run Analysis"}
          </Btn>
        </div>
      </div>

      {analyzing && (
        <Card style={{ marginBottom:16, borderColor:"var(--amber)", background:"rgba(212,160,23,.05)" }}>
          <div style={{ display:"flex", alignItems:"center", gap:12 }}>
            <div style={{ width:14, height:14, border:"2px solid var(--amber)", borderTopColor:"transparent",
                          borderRadius:"50%", animation:"spin .8s linear infinite" }}/>
            <span style={{ fontFamily:"var(--mono)", fontSize:11, color:"var(--amber2)" }}>
              Sending image to Gemini Vision API...
            </span>
            <div style={{ flex:1, marginLeft:8 }}>
              <ProgressBar value={progress} color="var(--amber)" height={3} />
            </div>
            <span style={{ fontFamily:"var(--mono)", fontSize:10, color:"var(--amber-dim)" }}>{progress}%</span>
          </div>
        </Card>
      )}

      <div style={{ display:"grid", gridTemplateColumns:"1.2fr 1fr", gap:16 }}>
        {/* current result */}
        <div style={{ display:"flex", flexDirection:"column", gap:12 }}>
          <Card glow style={{ borderColor:"rgba(212,160,23,.3)" }}>
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", marginBottom:16 }}>
              <div>
                <Label>Current Detection</Label>
                <div style={{ fontFamily:"var(--sans)", fontSize:24, fontWeight:800, color:"var(--amber2)", marginTop:4 }}>
                  {mockDisease.disease}
                </div>
              </div>
              <Tag color={sevColor[mockDisease.severity]}>
                {mockDisease.severity.toUpperCase()} SEVERITY
              </Tag>
            </div>

            {/* confidence arc */}
            <div style={{ display:"grid", gridTemplateColumns:"auto 1fr", gap:20, alignItems:"center" }}>
              <div style={{ position:"relative", width:90, height:90 }}>
                <svg width="90" height="90" viewBox="0 0 90 90">
                  <circle cx="45" cy="45" r="36" fill="none" stroke="var(--bg4)" strokeWidth="6"/>
                  <circle cx="45" cy="45" r="36" fill="none" stroke="var(--amber)" strokeWidth="6"
                    strokeLinecap="round"
                    strokeDasharray={`${2*Math.PI*36}`}
                    strokeDashoffset={`${2*Math.PI*36*(1-mockDisease.confidence)}`}
                    transform="rotate(-90 45 45)"
                  />
                  <text x="45" y="45" textAnchor="middle" dominantBaseline="central"
                    fill="var(--amber2)" fontSize="15" fontFamily="Space Mono" fontWeight="700">
                    {(mockDisease.confidence*100).toFixed(0)}%
                  </text>
                </svg>
              </div>
              <div style={{ display:"flex", flexDirection:"column", gap:10 }}>
                {[
                  { l:"Affected Area",  v:`${mockDisease.affected_area}%`,   color:"var(--red2)" },
                  { l:"Pesticide",      v:mockDisease.pesticide,              color:"var(--text2)" },
                  { l:"Dosage",         v:`${mockDisease.dosage_ml} ml/m²`,   color:"var(--green2)" },
                ].map(r => (
                  <div key={r.l}>
                    <Label>{r.l}</Label>
                    <div style={{ fontFamily:"var(--mono)", fontSize:12, color:r.color }}>{r.v}</div>
                  </div>
                ))}
              </div>
            </div>

            <div style={{ marginTop:16, padding:12, background:"var(--bg3)", borderRadius:3, borderLeft:"3px solid var(--amber)" }}>
              <Label>Recommendation</Label>
              <div style={{ fontFamily:"var(--mono)", fontSize:11, color:"var(--text2)", lineHeight:1.7, marginTop:4 }}>
                {mockDisease.recommendation}
              </div>
            </div>

            <div style={{ display:"flex", gap:8, marginTop:14 }}>
              <Btn variant="amber">⬡ Spray Now</Btn>
              <Btn variant="ghost" small>Export Report</Btn>
            </div>
          </Card>

          {/* gemini prompt preview */}
          <Card>
            <Label>Gemini Prompt Context</Label>
            <div style={{
              marginTop:10, fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)",
              background:"var(--bg3)", borderRadius:3, padding:12, lineHeight:1.8,
            }}>
              {`Soil pH: ${mockSensors.ph}\nMoisture: ${mockSensors.moisture}%\nTemperature: ${mockSensors.temperature}°C\nHumidity: ${mockSensors.humidity}%\nN: ${mockSensors.nitrogen} P: ${mockSensors.phosphorus} K: ${mockSensors.potassium} mg/kg`}
            </div>
          </Card>
        </div>

        {/* history */}
        <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
          <div style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)", letterSpacing:"0.15em", marginBottom:4 }}>
            DETECTION HISTORY
          </div>
          {mockPredictions.map((p, i) => (
            <div key={i} style={{
              background: i===0 ? "var(--surface)" : "var(--bg2)",
              border:`1px solid ${i===0 ? "var(--green)" : "var(--border)"}`,
              borderRadius:4, padding:"12px 14px",
              display:"flex", alignItems:"center", gap:12,
              animation:`fadeUp ${.2+i*.08}s ease both`,
            }}>
              <div style={{ width:4, height:"100%", minHeight:32, borderRadius:2,
                            background: p.severity==="high" ? "var(--red)" : p.severity==="medium" ? "var(--amber)" : p.severity==="low" ? "var(--teal)" : "var(--border2)" }}/>
              <div style={{ flex:1 }}>
                <div style={{ fontFamily:"var(--mono)", fontSize:11, color:"var(--text)", fontWeight:700 }}>
                  {p.disease}
                </div>
                <div style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)", marginTop:2 }}>
                  {p.time} · {(p.confidence*100).toFixed(0)}% conf · {p.dosage > 0 ? `${p.dosage} ml/m²` : "no spray"}
                </div>
              </div>
              <Tag color={sevColor[p.severity]}>{p.severity}</Tag>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// PAGE: MOTOR
// ═══════════════════════════════════════════════════════════════════════════════
function Motor({ mode }) {
  const [motorOn, setMotorOn] = useState(false);
  const [dosage, setDosage] = useState(25);
  const [flowTotal, setFlowTotal] = useState(1.24);
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!motorOn) { setElapsed(0); return; }
    const id = setInterval(() => {
      setElapsed(e => e + 1);
      setFlowTotal(f => +(f + 0.003).toFixed(3));
    }, 1000);
    return () => clearInterval(id);
  }, [motorOn]);

  const fmt = s => `${String(Math.floor(s/60)).padStart(2,"0")}:${String(s%60).padStart(2,"0")}`;

  return (
    <div style={{ padding:24, animation:"fadeUp .4s ease both" }}>
      <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:24 }}>
        <h1 style={{ fontFamily:"var(--sans)", fontSize:22, fontWeight:800 }}>Motor Control</h1>
        <Tag color={mode==="auto" ? "green" : "amber"}>{mode} mode</Tag>
      </div>

      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:16 }}>
        {/* main control */}
        <Card style={{ textAlign:"center" }}>
          {/* big pump button */}
          <div style={{ position:"relative", width:140, height:140, margin:"0 auto 24px" }}>
            {motorOn && [1,2,3].map(r => (
              <div key={r} style={{
                position:"absolute", inset: -r*14, borderRadius:"50%",
                border:`1px solid var(--green)`, opacity: .3/r,
                animation:`pulse ${r*.5+1}s ease-in-out infinite`,
              }}/>
            ))}
            <button onClick={() => { if(mode==="manual") setMotorOn(!motorOn); }}
              style={{
                width:"100%", height:"100%", borderRadius:"50%",
                background: motorOn ? "var(--green-dim)" : "var(--bg3)",
                border:`2px solid ${motorOn ? "var(--green)" : "var(--border)"}`,
                cursor: mode==="manual" ? "pointer" : "not-allowed",
                display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center",
                gap:6, transition:"all .2s", outline:"none",
                boxShadow: motorOn ? "0 0 30px rgba(125,181,71,.3)" : "none",
              }}>
              <span style={{ fontSize:36 }}>{motorOn ? "💧" : "⭕"}</span>
              <span style={{ fontFamily:"var(--mono)", fontSize:10, color: motorOn ? "var(--green2)" : "var(--text3)",
                             letterSpacing:"0.1em" }}>
                {motorOn ? "RUNNING" : "IDLE"}
              </span>
            </button>
          </div>

          {motorOn && (
            <div style={{ fontFamily:"var(--mono)", fontSize:22, color:"var(--green2)", marginBottom:8 }}>
              {fmt(elapsed)}
            </div>
          )}

          <div style={{ display:"flex", gap:8, justifyContent:"center" }}>
            <Btn onClick={() => { if(mode==="manual") setMotorOn(true); }}
              variant="primary" style={{ opacity: mode!=="manual" || motorOn ? .5 : 1 }}>
              ▶ START
            </Btn>
            <Btn onClick={() => setMotorOn(false)} variant="red"
              style={{ opacity: !motorOn ? .5 : 1 }}>
              ■ STOP
            </Btn>
          </div>

          {mode !== "manual" && (
            <div style={{ marginTop:14, fontFamily:"var(--mono)", fontSize:10, color:"var(--text3)",
                          background:"var(--bg3)", padding:"8px 12px", borderRadius:3 }}>
              Switch to MANUAL mode to control the pump
            </div>
          )}
        </Card>

        {/* dosage + stats */}
        <div style={{ display:"flex", flexDirection:"column", gap:12 }}>
          <Card>
            <Label>Dosage Control</Label>
            <div style={{ marginTop:12 }}>
              <div style={{ display:"flex", justifyContent:"space-between", marginBottom:8 }}>
                <span style={{ fontFamily:"var(--mono)", fontSize:10, color:"var(--text2)" }}>Target: {dosage} ml/m²</span>
                <div style={{ display:"flex", gap:6 }}>
                  {[10,20,30,50].map(v => (
                    <button key={v} onClick={() => setDosage(v)} style={{
                      fontFamily:"var(--mono)", fontSize:9, padding:"3px 8px",
                      background: dosage===v ? "var(--green-dim)" : "var(--bg4)",
                      border:`1px solid ${dosage===v ? "var(--green)" : "var(--border)"}`,
                      color: dosage===v ? "var(--green2)" : "var(--text3)",
                      borderRadius:2, cursor:"pointer",
                    }}>{v}</button>
                  ))}
                </div>
              </div>
              <input type="range" min={0} max={100} value={dosage} onChange={e => setDosage(+e.target.value)}
                style={{ width:"100%", accentColor:"var(--green)" }} />
              <div style={{ display:"flex", justifyContent:"space-between", fontFamily:"var(--mono)", fontSize:8, color:"var(--text3)", marginTop:4 }}>
                <span>0 ml</span><span>100 ml/m²</span>
              </div>
            </div>
          </Card>

          <Card>
            <Label>Session Stats</Label>
            <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:10, marginTop:10 }}>
              {[
                { l:"Flow Rate",     v: motorOn ? "1.8 L/min" : "0.0 L/min", color:"var(--green2)" },
                { l:"Total Today",   v:`${flowTotal} L`,                      color:"var(--teal2)"  },
                { l:"Last Spray",    v:"14:20 · 42ml",                        color:"var(--text2)"  },
                { l:"Sessions",      v:"4 today",                             color:"var(--text2)"  },
              ].map(s => (
                <div key={s.l} style={{ background:"var(--bg3)", borderRadius:3, padding:"10px 12px" }}>
                  <Label>{s.l}</Label>
                  <div style={{ fontFamily:"var(--mono)", fontSize:13, color:s.color, fontWeight:700, marginTop:2 }}>{s.v}</div>
                </div>
              ))}
            </div>
          </Card>

          {/* schedule */}
          <Card>
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:12 }}>
              <Label>Auto Schedules</Label>
              <Btn small variant="ghost">+ Add</Btn>
            </div>
            {schedules.map((s, i) => (
              <div key={i} style={{
                display:"flex", alignItems:"center", gap:10,
                padding:"10px 0", borderBottom: i < schedules.length-1 ? "1px solid var(--bg4)" : "none",
              }}>
                <Toggle value={s.active} onChange={() => {}} />
                <div style={{ flex:1 }}>
                  <div style={{ fontFamily:"var(--mono)", fontSize:11, color:"var(--text)" }}>{s.time} · {s.days}</div>
                  <div style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)" }}>{s.dosage} ml/m²</div>
                </div>
                <Btn small variant="ghost">✕</Btn>
              </div>
            ))}
          </Card>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// PAGE: LOGS
// ═══════════════════════════════════════════════════════════════════════════════
function Logs() {
  const [filter, setFilter] = useState("ALL");
  const [search, setSearch] = useState("");
  const levels = ["ALL","INFO","WARN","ERROR"];
  const levelColor = { INFO:"teal", WARN:"amber", ERROR:"red" };
  const filtered = mockLogs.filter(l =>
    (filter === "ALL" || l.level === filter) &&
    (search === "" || l.msg.toLowerCase().includes(search.toLowerCase()) || l.source.includes(search))
  );

  return (
    <div style={{ padding:24, animation:"fadeUp .4s ease both" }}>
      <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:24 }}>
        <h1 style={{ fontFamily:"var(--sans)", fontSize:22, fontWeight:800 }}>System Logs</h1>
        <Btn variant="ghost" small>↓ Export CSV</Btn>
      </div>

      <Card style={{ marginBottom:12 }}>
        <div style={{ display:"flex", gap:12, alignItems:"center" }}>
          <div style={{ display:"flex", gap:4 }}>
            {levels.map(l => (
              <button key={l} onClick={() => setFilter(l)} style={{
                fontFamily:"var(--mono)", fontSize:9, padding:"5px 12px", letterSpacing:"0.08em",
                background: filter===l ? "var(--surface)" : "transparent",
                border:`1px solid ${filter===l ? "var(--border2)" : "var(--border)"}`,
                color: filter===l ? "var(--text)" : "var(--text3)",
                borderRadius:2, cursor:"pointer",
              }}>{l}</button>
            ))}
          </div>
          <div style={{ flex:1, position:"relative" }}>
            <input
              value={search} onChange={e => setSearch(e.target.value)}
              placeholder="Search logs..."
              style={{
                width:"100%", background:"var(--bg3)", border:"1px solid var(--border)",
                color:"var(--text)", fontFamily:"var(--mono)", fontSize:11,
                padding:"6px 12px", borderRadius:3, outline:"none",
              }}
            />
          </div>
          <div style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)" }}>
            {filtered.length} entries
          </div>
        </div>
      </Card>

      <div style={{ display:"flex", flexDirection:"column", gap:2 }}>
        {filtered.map((l, i) => (
          <div key={i} style={{
            display:"grid", gridTemplateColumns:"70px 80px 1fr 120px",
            gap:12, alignItems:"center",
            padding:"10px 14px", borderRadius:3,
            background: i % 2 === 0 ? "var(--bg2)" : "var(--bg3)",
            border:"1px solid transparent",
            animation:`fadeUp ${.1+i*.03}s ease both`,
          }}>
            <Tag color={levelColor[l.level] || "dim"}>{l.level}</Tag>
            <span style={{ fontFamily:"var(--mono)", fontSize:10, color:"var(--text3)" }}>{l.time}</span>
            <span style={{ fontFamily:"var(--mono)", fontSize:11, color:"var(--text2)" }}>{l.msg}</span>
            <span style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)", textAlign:"right" }}>{l.source}</span>
          </div>
        ))}
        {filtered.length === 0 && (
          <div style={{ textAlign:"center", padding:40, fontFamily:"var(--mono)", fontSize:11, color:"var(--text3)" }}>
            No logs match your filter.
          </div>
        )}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// PAGE: SETTINGS
// ═══════════════════════════════════════════════════════════════════════════════
function Settings() {
  const [geminiKey, setGeminiKey] = useState("AIza••••••••••••••••••••••••••••");
  const [mqttBroker, setMqttBroker] = useState("192.168.1.100");
  const [pollInterval, setPollInterval] = useState(5);
  const [inferInterval, setInferInterval] = useState(30);
  const [saved, setSaved] = useState(false);

  const save = () => { setSaved(true); setTimeout(() => setSaved(false), 2000); };

  return (
    <div style={{ padding:24, animation:"fadeUp .4s ease both" }}>
      <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:24 }}>
        <h1 style={{ fontFamily:"var(--sans)", fontSize:22, fontWeight:800 }}>Settings</h1>
        <Btn onClick={save} variant={saved ? "ghost" : "primary"}>
          {saved ? "✓ Saved" : "Save Changes"}
        </Btn>
      </div>

      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:16 }}>
        {/* API config */}
        <div style={{ display:"flex", flexDirection:"column", gap:12 }}>
          <Card>
            <Label>Gemini API</Label>
            <div style={{ marginTop:12 }}>
              <div style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)", marginBottom:6 }}>API KEY</div>
              <input value={geminiKey} onChange={e => setGeminiKey(e.target.value)}
                type="password"
                style={{
                  width:"100%", background:"var(--bg3)", border:"1px solid var(--border)",
                  color:"var(--text2)", fontFamily:"var(--mono)", fontSize:11,
                  padding:"8px 12px", borderRadius:3, outline:"none", marginBottom:12,
                }}/>
              <div style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)", marginBottom:6 }}>MODEL</div>
              <div style={{ display:"flex", gap:6 }}>
                {["gemini-1.5-flash","gemini-1.5-pro"].map(m => (
                  <button key={m} style={{
                    fontFamily:"var(--mono)", fontSize:9, padding:"5px 10px",
                    background: m==="gemini-1.5-flash" ? "var(--green-dim)" : "var(--bg4)",
                    border:`1px solid ${m==="gemini-1.5-flash" ? "var(--green)" : "var(--border)"}`,
                    color: m==="gemini-1.5-flash" ? "var(--green2)" : "var(--text3)",
                    borderRadius:2, cursor:"pointer",
                  }}>{m}</button>
                ))}
              </div>
            </div>
          </Card>

          <Card>
            <Label>MQTT Broker</Label>
            <div style={{ marginTop:12 }}>
              {[
                { l:"Broker IP", v:mqttBroker, set:setMqttBroker },
              ].map(f => (
                <div key={f.l} style={{ marginBottom:12 }}>
                  <div style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)", marginBottom:6 }}>{f.l}</div>
                  <input value={f.v} onChange={e => f.set(e.target.value)}
                    style={{
                      width:"100%", background:"var(--bg3)", border:"1px solid var(--border)",
                      color:"var(--text2)", fontFamily:"var(--mono)", fontSize:11,
                      padding:"8px 12px", borderRadius:3, outline:"none",
                    }}/>
                </div>
              ))}
              <div style={{ display:"flex", gap:8 }}>
                <Btn small variant="ghost">Test Connection</Btn>
                <Tag color="green">Connected</Tag>
              </div>
            </div>
          </Card>
        </div>

        {/* polling + thresholds */}
        <div style={{ display:"flex", flexDirection:"column", gap:12 }}>
          <Card>
            <Label>Polling Intervals</Label>
            <div style={{ marginTop:12, display:"flex", flexDirection:"column", gap:14 }}>
              {[
                { l:"Sensor Poll", v:pollInterval, set:setPollInterval, unit:"sec", min:1, max:60 },
                { l:"AI Inference", v:inferInterval, set:setInferInterval, unit:"sec", min:10, max:300 },
              ].map(f => (
                <div key={f.l}>
                  <div style={{ display:"flex", justifyContent:"space-between", marginBottom:6 }}>
                    <span style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)" }}>{f.l}</span>
                    <span style={{ fontFamily:"var(--mono)", fontSize:10, color:"var(--green2)", fontWeight:700 }}>{f.v}s</span>
                  </div>
                  <input type="range" min={f.min} max={f.max} value={f.v}
                    onChange={e => f.set(+e.target.value)}
                    style={{ width:"100%", accentColor:"var(--green)" }}/>
                </div>
              ))}
            </div>
          </Card>

          <Card>
            <Label>Alert Thresholds</Label>
            <div style={{ marginTop:12, display:"flex", flexDirection:"column", gap:10 }}>
              {[
                { l:"pH Range",       lo:5.5, hi:7.5, unit:"" },
                { l:"Moisture",       lo:40,  hi:80,  unit:"%" },
                { l:"Humidity",       lo:30,  hi:90,  unit:"%" },
                { l:"Temperature",    lo:15,  hi:35,  unit:"°C" },
              ].map(t => (
                <div key={t.l} style={{ display:"flex", justifyContent:"space-between", alignItems:"center",
                                        borderBottom:"1px solid var(--bg4)", paddingBottom:8 }}>
                  <span style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)" }}>{t.l}</span>
                  <div style={{ display:"flex", gap:6, alignItems:"center" }}>
                    <span style={{ fontFamily:"var(--mono)", fontSize:10, color:"var(--teal2)" }}>{t.lo}{t.unit}</span>
                    <span style={{ color:"var(--text3)", fontSize:9 }}>—</span>
                    <span style={{ fontFamily:"var(--mono)", fontSize:10, color:"var(--amber2)" }}>{t.hi}{t.unit}</span>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Card>
            <Label>System</Label>
            <div style={{ display:"flex", flexDirection:"column", gap:10, marginTop:10 }}>
              {[
                { l:"OLED Display",       v:true  },
                { l:"Email Alerts",       v:false },
                { l:"Auto-Spray on Alert",v:true  },
                { l:"Log to File",        v:true  },
              ].map(s => (
                <div key={s.l} style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
                  <span style={{ fontFamily:"var(--mono)", fontSize:10, color:"var(--text2)" }}>{s.l}</span>
                  <Toggle value={s.v} onChange={() => {}} />
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// APP ROOT
// ═══════════════════════════════════════════════════════════════════════════════
export default function App() {
  const [page, setPage] = useState("dashboard");
  const [mode, setMode] = useState("auto");

  const pageComponents = {
    dashboard: <Dashboard mode={mode} setPage={setPage} />,
    sensors:   <Sensors />,
    camera:    <Camera />,
    disease:   <Disease />,
    motor:     <Motor mode={mode} />,
    logs:      <Logs />,
    settings:  <Settings />,
  };

  return (
    <>
      <style>{css}</style>
      <div style={{ display:"flex", minHeight:"100vh", background:"var(--bg)" }}>
        <Sidebar page={page} setPage={setPage} />
        <div style={{ flex:1, marginLeft:64, paddingTop:52, minHeight:"100vh" }}>
          <TopBar page={page} mode={mode} setMode={setMode} />
          <div style={{ maxWidth:1200, margin:"0 auto" }}>
            {pageComponents[page]}
          </div>
        </div>
      </div>
    </>
  );
}
