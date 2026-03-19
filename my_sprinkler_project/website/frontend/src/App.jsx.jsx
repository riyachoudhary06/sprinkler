import { useState, useEffect, useCallback } from "react";

// ─── DESIGN TOKENS ───────────────────────────────────────────────────────────
const css = `
  @import url('https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&family=Syne:wght@400;600;700;800&display=swap');
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg:#0d1208; --bg2:#141a0e; --bg3:#1c2514; --bg4:#222d18;
    --surface:#2a3620; --border:#3a4a2a; --border2:#4a5e38;
    --green:#7db547; --green2:#a3d15e; --green-dim:#4a7030;
    --amber:#d4a017; --amber2:#f0be3a; --amber-dim:#7a5c0a;
    --red:#c94040; --red2:#e86060; --teal:#3cb4a0; --teal2:#5cd4be;
    --text:#dde8cc; --text2:#8fa878; --text3:#5a6e48;
    --mono:'Space Mono',monospace; --sans:'Syne',sans-serif;
  }
  html,body,#root { height:100%; background:var(--bg); color:var(--text); }
  ::-webkit-scrollbar { width:4px; }
  ::-webkit-scrollbar-track { background:var(--bg2); }
  ::-webkit-scrollbar-thumb { background:var(--border2); border-radius:2px; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
  @keyframes spin  { to { transform:rotate(360deg); } }
  @keyframes fadeUp { from{opacity:0;transform:translateY(12px)} to{opacity:1;transform:translateY(0)} }
  @keyframes scan { 0%{transform:translateY(-100%);opacity:.6} 100%{transform:translateY(400%);opacity:0} }
  @keyframes blink { 0%,100%{opacity:1} 49%{opacity:1} 50%{opacity:0} 99%{opacity:0} }
  @keyframes glow { 0%,100%{box-shadow:0 0 8px var(--green-dim)} 50%{box-shadow:0 0 24px var(--green2)} }
`;

// ─── API ──────────────────────────────────────────────────────────────────────
const API_BASE = (typeof import.meta !== "undefined" && import.meta.env?.VITE_API_URL) || "http://localhost:8000";

async function apiFetch(path, opts = {}) {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...opts,
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (e) {
    console.warn(`[API] ${path}:`, e.message);
    return null;
  }
}

// ─── POLLING HOOK ─────────────────────────────────────────────────────────────
function usePoll(fetcher, interval = 5000) {
  const [data,    setData]    = useState(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(false);

  const run = useCallback(async () => {
    const result = await fetcher();
    if (result !== null) { setData(result); setError(false); }
    else setError(true);
    setLoading(false);
  }, [fetcher]);

  useEffect(() => {
    run();
    const id = setInterval(run, interval);
    return () => clearInterval(id);
  }, [run, interval]);

  return { data, loading, error, refetch: run };
}

// ─── SHARED COMPONENTS ────────────────────────────────────────────────────────

function Spinner() {
  return <span style={{ display:"inline-block", width:12, height:12, border:"2px solid var(--border2)", borderTopColor:"var(--green)", borderRadius:"50%", animation:"spin .7s linear infinite" }}/>;
}

function Tag({ children, color = "dim" }) {
  const C = {
    green:{ bg:"rgba(125,181,71,.15)", bo:"rgba(125,181,71,.4)", tx:"var(--green2)" },
    amber:{ bg:"rgba(212,160,23,.15)", bo:"rgba(212,160,23,.4)", tx:"var(--amber2)" },
    red:  { bg:"rgba(201,64,64,.15)",  bo:"rgba(201,64,64,.4)",  tx:"var(--red2)"   },
    teal: { bg:"rgba(60,180,160,.15)", bo:"rgba(60,180,160,.4)", tx:"var(--teal2)"  },
    dim:  { bg:"rgba(90,110,72,.1)",   bo:"rgba(90,110,72,.3)",  tx:"var(--text2)"  },
  };
  const c = C[color] || C.dim;
  return <span style={{ background:c.bg, border:`1px solid ${c.bo}`, color:c.tx, fontFamily:"var(--mono)", fontSize:10, padding:"2px 8px", borderRadius:2, letterSpacing:"0.08em", textTransform:"uppercase", fontWeight:700 }}>{children}</span>;
}

function Card({ children, style={}, glow=false }) {
  return <div style={{ background:"var(--bg2)", border:"1px solid var(--border)", borderRadius:4, padding:20, boxShadow:glow?"0 0 20px rgba(125,181,71,.08)":"none", animation:glow?"glow 3s ease-in-out infinite":"none", ...style }}>{children}</div>;
}

function Label({ children }) {
  return <div style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)", letterSpacing:"0.15em", textTransform:"uppercase", marginBottom:6 }}>{children}</div>;
}

function Val({ children, size=28, color="var(--text)" }) {
  return <div style={{ fontFamily:"var(--mono)", fontSize:size, fontWeight:700, color, lineHeight:1, letterSpacing:"-0.02em" }}>{children}</div>;
}

function Dot({ active }) {
  return <span style={{ display:"inline-block", width:7, height:7, borderRadius:"50%", background:active?"var(--green)":"var(--text3)", boxShadow:active?"0 0 8px var(--green)":"none", animation:active?"pulse 2s ease-in-out infinite":"none", marginRight:6 }}/>;
}

function Bar({ value, max=100, color="var(--green)", h=4 }) {
  const pct = value==null ? 0 : Math.min((value/max)*100, 100);
  return <div style={{ background:"var(--bg4)", borderRadius:2, height:h, overflow:"hidden" }}><div style={{ width:`${pct}%`, height:"100%", background:color, borderRadius:2, transition:"width .5s" }}/></div>;
}

function MiniChart({ data, field, color="var(--green)", height=48 }) {
  if (!data || data.length < 2) return <div style={{ height, display:"flex", alignItems:"center", justifyContent:"center" }}><span style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)" }}>no data</span></div>;
  const W=200, H=height;
  const vals = data.map(d=>d[field]).filter(v=>v!=null);
  if (vals.length < 2) return null;
  const mn=Math.min(...vals), mx=Math.max(...vals), rng=mx-mn||1;
  const pts = vals.map((v,i)=>`${(i/(vals.length-1))*W},${H-((v-mn)/rng)*H*.85-H*.05}`).join(" ");
  return (
    <svg width="100%" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" style={{ display:"block" }}>
      <defs><linearGradient id={`gc${field}`} x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={color} stopOpacity=".3"/><stop offset="100%" stopColor={color} stopOpacity="0"/></linearGradient></defs>
      <polygon points={`0,${H} ${pts} ${W},${H}`} fill={`url(#gc${field})`}/>
      <polyline points={pts} fill="none" stroke={color} strokeWidth="1.5" strokeLinejoin="round"/>
    </svg>
  );
}

function Toggle({ value, onChange }) {
  return (
    <div style={{ display:"flex", alignItems:"center", cursor:"pointer" }} onClick={()=>onChange(!value)}>
      <div style={{ width:40, height:22, borderRadius:11, position:"relative", background:value?"var(--green)":"var(--surface)", border:`1px solid ${value?"var(--green2)":"var(--border)"}`, transition:"all .2s" }}>
        <div style={{ position:"absolute", top:2, left:value?18:2, width:16, height:16, borderRadius:"50%", background:"#fff", transition:"left .2s", boxShadow:"0 1px 4px rgba(0,0,0,.4)" }}/>
      </div>
    </div>
  );
}

function Btn({ children, onClick, variant="primary", small=false, disabled=false, style:sx={} }) {
  const S = {
    primary:{ bg:"var(--green-dim)", bo:"var(--green)",   tx:"var(--green2)", hv:"rgba(125,181,71,.25)" },
    amber:  { bg:"var(--amber-dim)", bo:"var(--amber)",   tx:"var(--amber2)", hv:"rgba(212,160,23,.25)" },
    red:    { bg:"rgba(201,64,64,.15)",bo:"var(--red)",   tx:"var(--red2)",   hv:"rgba(201,64,64,.25)" },
    ghost:  { bg:"transparent",      bo:"var(--border2)", tx:"var(--text2)",  hv:"var(--surface)" },
  };
  const s = S[variant]||S.ghost;
  const [hov, setHov] = useState(false);
  return (
    <button onClick={onClick} disabled={disabled} onMouseEnter={()=>setHov(true)} onMouseLeave={()=>setHov(false)}
      style={{ background:hov&&!disabled?s.hv:s.bg, border:`1px solid ${s.bo}`, color:s.tx, fontFamily:"var(--mono)", fontSize:small?10:11, padding:small?"5px 12px":"9px 18px", borderRadius:3, cursor:disabled?"not-allowed":"pointer", letterSpacing:"0.06em", textTransform:"uppercase", fontWeight:700, transition:"all .15s", opacity:disabled?.5:1, ...sx }}>
      {children}
    </button>
  );
}

function Empty({ msg="Waiting for backend..." }) {
  return <div style={{ display:"flex", alignItems:"center", gap:8, fontFamily:"var(--mono)", fontSize:10, color:"var(--text3)" }}><Spinner/>{msg}</div>;
}

// ─── NAV ──────────────────────────────────────────────────────────────────────
const NAV = [
  {id:"dashboard",icon:"◈",label:"Dashboard"},
  {id:"sensors",  icon:"◉",label:"Sensors"  },
  {id:"camera",   icon:"⬡",label:"Camera"   },
  {id:"disease",  icon:"◍",label:"Disease"  },
  {id:"motor",    icon:"⬢",label:"Motor"    },
  {id:"logs",     icon:"≡",label:"Logs"     },
  {id:"settings", icon:"⚙",label:"Settings" },
];

function Sidebar({ page, setPage, ok }) {
  return (
    <div style={{ width:64, minHeight:"100vh", background:"var(--bg2)", borderRight:"1px solid var(--border)", display:"flex", flexDirection:"column", alignItems:"center", paddingTop:16, gap:2, position:"fixed", top:0, left:0, zIndex:100 }}>
      <div style={{ width:36, height:36, background:"var(--green-dim)", border:"1px solid var(--green)", borderRadius:4, display:"flex", alignItems:"center", justifyContent:"center", marginBottom:20 }}>
        <span style={{ fontSize:16 }}>🌿</span>
      </div>
      {NAV.map(n=>(
        <button key={n.id} title={n.label} onClick={()=>setPage(n.id)} style={{ width:44, height:44, borderRadius:4, border:"none", cursor:"pointer", background:page===n.id?"var(--surface)":"transparent", color:page===n.id?"var(--green2)":"var(--text3)", fontSize:16, display:"flex", alignItems:"center", justifyContent:"center", transition:"all .15s", boxShadow:page===n.id?`inset 2px 0 0 var(--green)`:"none" }}>
          {n.icon}
        </button>
      ))}
      <div style={{ marginTop:"auto", paddingBottom:16 }}><Dot active={ok}/></div>
    </div>
  );
}

function TopBar({ page, mode, onMode, ok }) {
  const [t, setT] = useState(new Date());
  useEffect(()=>{ const id=setInterval(()=>setT(new Date()),1000); return()=>clearInterval(id); },[]);

  const switchMode = async (m) => {
    const r = await apiFetch("/mode/", { method:"POST", body:JSON.stringify({mode:m}) });
    if (r) onMode(m);
  };

  return (
    <div style={{ height:52, background:"var(--bg2)", borderBottom:"1px solid var(--border)", display:"flex", alignItems:"center", padding:"0 20px 0 0", position:"fixed", top:0, left:64, right:0, zIndex:99, gap:16 }}>
      <div style={{ height:"100%", padding:"0 20px", borderRight:"1px solid var(--border)", display:"flex", alignItems:"center", gap:10, minWidth:200 }}>
        <span style={{ fontFamily:"var(--sans)", fontWeight:800, fontSize:13, letterSpacing:"0.08em" }}>AGRI·WATCH</span>
        <span style={{ color:"var(--border2)", fontSize:10 }}>◦</span>
        <span style={{ fontFamily:"var(--mono)", fontSize:10, color:"var(--text2)", letterSpacing:"0.1em", textTransform:"uppercase" }}>{NAV.find(n=>n.id===page)?.label}</span>
      </div>
      <div style={{ flex:1 }}/>
      <div style={{ display:"flex", alignItems:"center", gap:6 }}>
        <Dot active={ok}/>
        <span style={{ fontFamily:"var(--mono)", fontSize:9, color:ok?"var(--green2)":"var(--red2)" }}>{ok?"BACKEND OK":"BACKEND OFFLINE"}</span>
      </div>
      <div style={{ display:"flex", alignItems:"center", gap:8 }}>
        <span style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)", letterSpacing:"0.1em" }}>MODE</span>
        <div style={{ display:"flex", background:"var(--bg4)", border:"1px solid var(--border)", borderRadius:3, overflow:"hidden" }}>
          {["auto","manual"].map(m=>(
            <button key={m} onClick={()=>switchMode(m)} style={{ padding:"5px 12px", fontFamily:"var(--mono)", fontSize:10, border:"none", cursor:"pointer", letterSpacing:"0.08em", textTransform:"uppercase", fontWeight:700, background:mode===m?(m==="auto"?"var(--green-dim)":"var(--amber-dim)"):"transparent", color:mode===m?(m==="auto"?"var(--green2)":"var(--amber2)"):"var(--text3)", transition:"all .15s" }}>{m}</button>
          ))}
        </div>
      </div>
      <div style={{ fontFamily:"var(--mono)", fontSize:11, color:"var(--text2)", letterSpacing:"0.06em", borderLeft:"1px solid var(--border)", paddingLeft:16, animation:"blink 1s step-start infinite" }}>
        {t.toLocaleTimeString("en-GB",{hour12:false})}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// DASHBOARD
// ═══════════════════════════════════════════════════════════════════════════════
function Dashboard({ mode, setPage }) {
  const sf = useCallback(()=>apiFetch("/sensors/latest"),[]);
  const df = useCallback(()=>apiFetch("/disease/latest"),[]);
  const hf = useCallback(()=>apiFetch("/sensors/history?limit=24&hours=24"),[]);
  const mf = useCallback(()=>apiFetch("/motor/status"),[]);
  const { data:sensors, loading:sl } = usePoll(sf, 5000);
  const { data:disease }             = usePoll(df, 15000);
  const { data:history }             = usePoll(hf, 30000);
  const { data:motor }               = usePoll(mf, 4000);

  const s = sensors || {};
  const d = disease || {};
  const h = Array.isArray(history) ? [...history].reverse() : [];
  const SC = { none:"dim", low:"teal", medium:"amber", high:"red" };
  const fmt = (v,dp=1) => v==null ? "—" : typeof v==="number" ? v.toFixed(dp) : v;

  return (
    <div style={{ padding:24, animation:"fadeUp .4s ease both" }}>
      <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:24 }}>
        <div>
          <h1 style={{ fontFamily:"var(--sans)", fontSize:22, fontWeight:800, letterSpacing:"-0.02em" }}>Field Overview</h1>
          <div style={{ fontFamily:"var(--mono)", fontSize:10, color:"var(--text3)", marginTop:3 }}>
            PLOT-A · ZONE-1 · {new Date().toLocaleDateString("en-GB",{weekday:"long",year:"numeric",month:"long",day:"numeric"})}
          </div>
        </div>
        <div style={{ display:"flex", gap:8, alignItems:"center" }}>
          <Tag color={mode==="auto"?"green":"amber"}>{mode} mode</Tag>
          {sl && <Spinner/>}
        </div>
      </div>

      {/* stat row */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:12, marginBottom:16 }}>
        {[
          {label:"Soil pH",      val:s.ph,          unit:"",   color:"var(--teal2)",  ok:s.ph>=5.5&&s.ph<=7.5,           dp:2},
          {label:"Soil Moisture",val:s.moisture,    unit:"%",  color:"var(--green2)", ok:s.moisture>=40&&s.moisture<=80,  dp:0},
          {label:"Air Temp",     val:s.temperature, unit:"°C", color:"var(--amber2)", ok:s.temperature<35,                dp:1},
          {label:"Humidity",     val:s.humidity,    unit:"%",  color:"var(--text2)",  ok:s.humidity>=30&&s.humidity<=90,  dp:0},
        ].map(c=>(
          <Card key={c.label} style={{ position:"relative", overflow:"hidden" }}>
            <div style={{ position:"absolute", top:0, right:0, width:3, height:"100%", background:c.val==null?"var(--border)":c.ok?"var(--green)":"var(--red)", borderRadius:"0 4px 4px 0" }}/>
            <Label>{c.label}</Label>
            <div style={{ display:"flex", alignItems:"baseline", gap:4 }}>
              <Val size={32} color={c.color}>{fmt(c.val, c.dp)}</Val>
              <span style={{ fontFamily:"var(--mono)", fontSize:12, color:"var(--text3)" }}>{c.unit}</span>
            </div>
            <div style={{ marginTop:10 }}><Bar value={c.val} max={c.label==="Soil pH"?14:100} color={c.val==null?"var(--border)":c.ok?c.color:"var(--red)"}/></div>
          </Card>
        ))}
      </div>

      {/* middle row */}
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:12, marginBottom:16 }}>
        {/* NPK */}
        <Card>
          <Label>NPK Levels — mg/kg</Label>
          <div style={{ marginTop:12, display:"flex", flexDirection:"column", gap:12 }}>
            {[
              {label:"N — Nitrogen",   val:s.nitrogen,   max:300, color:"var(--green2)"},
              {label:"P — Phosphorus", val:s.phosphorus, max:150, color:"var(--amber2)"},
              {label:"K — Potassium",  val:s.potassium,  max:350, color:"var(--teal2)" },
            ].map(n=>(
              <div key={n.label}>
                <div style={{ display:"flex", justifyContent:"space-between", marginBottom:5 }}>
                  <span style={{ fontFamily:"var(--mono)", fontSize:10, color:"var(--text2)" }}>{n.label}</span>
                  <span style={{ fontFamily:"var(--mono)", fontSize:10, color:n.color, fontWeight:700 }}>{n.val??  "—"}</span>
                </div>
                <Bar value={n.val} max={n.max} color={n.color} h={6}/>
              </div>
            ))}
          </div>
        </Card>

        {/* Disease */}
        <Card style={{ borderColor:d.severity==="high"?"var(--red)":d.severity==="medium"?"rgba(212,160,23,.4)":"var(--border)" }}>
          <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start" }}>
            <Label>Latest Detection</Label>
            <Tag color={SC[d.severity]||"dim"}>{d.severity||"—"}</Tag>
          </div>
          <div style={{ marginTop:10 }}>
            <div style={{ fontFamily:"var(--sans)", fontSize:16, fontWeight:700, color:"var(--amber2)", marginBottom:4 }}>{d.disease||"No data yet"}</div>
            <div style={{ fontFamily:"var(--mono)", fontSize:10, color:"var(--text2)", marginBottom:12, lineHeight:1.6 }}>{d.recommendation||"—"}</div>
            <div style={{ display:"flex", gap:16 }}>
              <div><Label>Conf.</Label>   <Val size={18} color="var(--green2)">{d.confidence?`${(d.confidence*100).toFixed(0)}%`:"—"}</Val></div>
              <div><Label>Area</Label>    <Val size={18} color="var(--amber2)">{d.affected_area!=null?`${d.affected_area}%`:"—"}</Val></div>
              <div><Label>Dosage</Label>  <Val size={18} color="var(--teal2)" >{d.dosage_ml!=null?`${d.dosage_ml}ml`:"—"}</Val></div>
            </div>
          </div>
          <div style={{ marginTop:12 }}><Btn onClick={()=>setPage("disease")} small>View →</Btn></div>
        </Card>

        {/* Motor */}
        <Card>
          <Label>Motor Status</Label>
          <div style={{ textAlign:"center", padding:"16px 0" }}>
            <div style={{ width:72, height:72, borderRadius:"50%", margin:"0 auto 12px", border:`2px solid ${motor?.running?"var(--green)":"var(--border2)"}`, background:"var(--bg3)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:28, position:"relative" }}>
              💧
              {motor?.running && <div style={{ position:"absolute", inset:-4, borderRadius:"50%", border:"2px solid var(--green)", opacity:.3, animation:"pulse 2s ease infinite" }}/>}
            </div>
            <div style={{ fontFamily:"var(--mono)", fontSize:10, color:motor?.running?"var(--green2)":"var(--text3)", marginBottom:8 }}>
              PUMP · {motor?.running?"RUNNING":"IDLE"}
            </div>
            <Btn onClick={()=>setPage("motor")} small>Control →</Btn>
          </div>
        </Card>
      </div>

      {/* sparklines */}
      <Card>
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:16 }}>
          <Label>24-Hour Sensor History</Label>
          <div style={{ display:"flex", gap:12 }}>
            {[{l:"Moisture",color:"var(--green2)"},{l:"Temp",color:"var(--amber2)"},{l:"Humidity",color:"var(--teal2)"}].map(x=>(
              <div key={x.l} style={{ display:"flex", alignItems:"center", gap:5 }}>
                <div style={{ width:12, height:2, background:x.color, borderRadius:1 }}/>
                <span style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)" }}>{x.l}</span>
              </div>
            ))}
          </div>
        </div>
        <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:12 }}>
          {[{f:"moisture",c:"var(--green2)"},{f:"temperature",c:"var(--amber2)"},{f:"humidity",c:"var(--teal2)"}].map(x=>(
            <div key={x.f} style={{ height:60 }}><MiniChart data={h} field={x.f} color={x.c} height={60}/></div>
          ))}
        </div>
        {h.length === 0 && <div style={{ textAlign:"center", paddingTop:8 }}><Empty msg="No history yet — waiting for Pi data"/></div>}
      </Card>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// SENSORS
// ═══════════════════════════════════════════════════════════════════════════════
function Sensors() {
  const [sel, setSel] = useState("moisture");
  const lf = useCallback(()=>apiFetch("/sensors/latest"),[]);
  const hf = useCallback(()=>apiFetch("/sensors/history?limit=48&hours=24"),[]);
  const sf = useCallback(()=>apiFetch("/sensors/stats?hours=24"),[]);
  const af = useCallback(()=>apiFetch("/sensors/alerts"),[]);
  const {data:latest, loading} = usePoll(lf, 5000);
  const {data:history}         = usePoll(hf, 30000);
  const {data:stats}           = usePoll(sf, 30000);
  const {data:alertsD}         = usePoll(af, 10000);

  const s  = latest || {};
  const h  = Array.isArray(history) ? [...history].reverse() : [];
  const al = alertsD?.alerts || [];

  const FIELDS = [
    {key:"ph",         label:"Soil pH",        val:s.ph,         unit:"",     min:0,max:14,   ok:[5.5,7.5],  color:"var(--teal2)" },
    {key:"moisture",   label:"Moisture",        val:s.moisture,   unit:"%",    min:0,max:100,  ok:[40,80],    color:"var(--green2)"},
    {key:"nitrogen",   label:"Nitrogen (N)",    val:s.nitrogen,   unit:"mg/kg",min:0,max:300,  ok:[100,250],  color:"var(--green2)"},
    {key:"phosphorus", label:"Phosphorus (P)",  val:s.phosphorus, unit:"mg/kg",min:0,max:150,  ok:[30,100],   color:"var(--amber2)"},
    {key:"potassium",  label:"Potassium (K)",   val:s.potassium,  unit:"mg/kg",min:0,max:350,  ok:[150,300],  color:"var(--teal2)" },
    {key:"temperature",label:"Temperature",     val:s.temperature,unit:"°C",   min:0,max:50,   ok:[20,35],    color:"var(--amber2)"},
    {key:"humidity",   label:"Humidity",        val:s.humidity,   unit:"%",    min:0,max:100,  ok:[40,85],    color:"var(--teal2)" },
    {key:"light_lux",  label:"Light",           val:s.light_lux,  unit:"lux",  min:0,max:80000,ok:[10000,70000],color:"var(--amber2)"},
  ];
  const selF    = FIELDS.find(f=>f.key===sel)||FIELDS[0];
  const selOk   = selF.val!=null && selF.val>=selF.ok[0] && selF.val<=selF.ok[1];
  const selStat = stats?.stats?.[selF.key];
  const fmt = (v,k) => v==null?"—":v>1000?v.toLocaleString():v.toFixed(k==="ph"?2:1);

  return (
    <div style={{ padding:24, animation:"fadeUp .4s ease both" }}>
      <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:24 }}>
        <h1 style={{ fontFamily:"var(--sans)", fontSize:22, fontWeight:800 }}>Sensor Readings</h1>
        <div style={{ display:"flex", gap:8, alignItems:"center" }}>
          {al.length>0 && <Tag color="red">{al.length} alert{al.length>1?"s":""}</Tag>}
          {loading ? <Spinner/> : <Tag color="green">Live · 5s</Tag>}
        </div>
      </div>

      <div style={{ display:"grid", gridTemplateColumns:"1fr 1.5fr", gap:16 }}>
        {/* list */}
        <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
          {FIELDS.map(f=>{
            const ok = f.val!=null && f.val>=f.ok[0] && f.val<=f.ok[1];
            const alert = al.some(a=>a.sensor===f.key);
            return (
              <button key={f.key} onClick={()=>setSel(f.key)} style={{ background:sel===f.key?"var(--surface)":"var(--bg2)", border:`1px solid ${sel===f.key?"var(--green)":alert?"var(--red)":"var(--border)"}`, borderRadius:4, padding:"14px 16px", cursor:"pointer", textAlign:"left", display:"flex", alignItems:"center", gap:14, transition:"all .15s" }}>
                <div style={{ width:4, height:36, borderRadius:2, background:f.val==null?"var(--border)":ok?f.color:"var(--red)" }}/>
                <div style={{ flex:1 }}>
                  <div style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)", letterSpacing:"0.1em", marginBottom:3 }}>{f.label.toUpperCase()}</div>
                  <div style={{ fontFamily:"var(--mono)", fontSize:18, fontWeight:700, color:f.val==null?"var(--text3)":ok?f.color:"var(--red2)" }}>
                    {fmt(f.val, f.key)}<span style={{ fontSize:11, fontWeight:400, color:"var(--text3)", marginLeft:4 }}>{f.unit}</span>
                  </div>
                </div>
                {f.val==null ? <Tag>—</Tag> : <Tag color={ok?"dim":"red"}>{ok?"OK":"!"}</Tag>}
              </button>
            );
          })}
        </div>

        {/* detail */}
        <div style={{ display:"flex", flexDirection:"column", gap:12 }}>
          <Card glow>
            <div style={{ display:"flex", justifyContent:"space-between", marginBottom:16 }}>
              <div>
                <Label>{selF.label}</Label>
                <div style={{ display:"flex", alignItems:"baseline", gap:8, marginTop:4 }}>
                  <Val size={48} color={selF.color}>{fmt(selF.val, selF.key)}</Val>
                  <span style={{ fontFamily:"var(--mono)", fontSize:14, color:"var(--text3)" }}>{selF.unit}</span>
                </div>
              </div>
              <Tag color={selF.val==null?"dim":selOk?"green":"red"}>{selF.val==null?"NO DATA":selOk?"NOMINAL":"ALERT"}</Tag>
            </div>
            {/* range slider */}
            <div style={{ position:"relative", height:8, background:"var(--bg4)", borderRadius:4, marginBottom:8 }}>
              <div style={{ position:"absolute", left:`${(selF.ok[0]/selF.max)*100}%`, width:`${((selF.ok[1]-selF.ok[0])/selF.max)*100}%`, height:"100%", background:"rgba(125,181,71,.2)", borderRadius:4 }}/>
              {selF.val!=null && <div style={{ position:"absolute", left:`${Math.min(selF.val/selF.max*100,100)}%`, transform:"translateX(-50%)", top:-3, width:14, height:14, borderRadius:"50%", background:selOk?selF.color:"var(--red2)", border:"2px solid var(--bg2)", boxShadow:`0 0 8px ${selOk?selF.color:"var(--red)"}` }}/>}
            </div>
            <div style={{ display:"flex", justifyContent:"space-between", fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)" }}>
              <span>{selF.min}</span><span>Optimal: {selF.ok[0]}–{selF.ok[1]} {selF.unit}</span><span>{selF.max}</span>
            </div>
          </Card>

          <Card>
            <Label>24-Hour Trend</Label>
            <div style={{ height:120, marginTop:12 }}><MiniChart data={h} field={selF.key} color={selF.color} height={120}/></div>
          </Card>

          <Card>
            <Label>Statistics (24h)</Label>
            {selStat ? (
              <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:12, marginTop:10 }}>
                {[{l:"Min",v:selStat.min},{l:"Avg",v:selStat.avg},{l:"Max",v:selStat.max}].map(x=>(
                  <div key={x.l} style={{ textAlign:"center", background:"var(--bg3)", borderRadius:4, padding:"10px 0" }}>
                    <Label>{x.l}</Label><Val size={16}>{x.v!=null?x.v:"—"}</Val>
                  </div>
                ))}
              </div>
            ) : <div style={{ marginTop:10 }}><Empty msg="Loading stats..."/></div>}
          </Card>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// CAMERA
// ═══════════════════════════════════════════════════════════════════════════════
function Camera() {
  const [cap,    setCap]    = useState(false);
  const [scan,   setScan]   = useState(false);
  const [capMsg, setCapMsg] = useState("");
  const sif = useCallback(()=>apiFetch("/camera/stream-url"),[]);
  const caf = useCallback(()=>apiFetch("/camera/captures?limit=8"),[]);
  const {data:si}                        = usePoll(sif, 60000);
  const {data:capData, refetch:reCaps}   = usePoll(caf, 15000);
  const caps = capData?.captures || [];
  const streamUrl = si?.url || "http://raspberrypi.local:8080/stream";

  const doCapture = async () => {
    setCap(true); setScan(true); setCapMsg("");
    const r = await apiFetch("/camera/capture",{method:"POST"});
    setTimeout(()=>{ setCap(false); setScan(false); setCapMsg(r?"Snapshot triggered!":"Failed — check Pi"); reCaps(); }, 1800);
  };

  return (
    <div style={{ padding:24, animation:"fadeUp .4s ease both" }}>
      <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:24 }}>
        <h1 style={{ fontFamily:"var(--sans)", fontSize:22, fontWeight:800 }}>Camera Feed</h1>
        <div style={{ display:"flex", gap:8 }}><Tag color="red">● LIVE</Tag><Tag color="dim">MJPEG</Tag></div>
      </div>
      <div style={{ display:"grid", gridTemplateColumns:"1fr 280px", gap:16 }}>
        <div>
          <div style={{ background:"var(--bg3)", border:"1px solid var(--border)", borderRadius:4, aspectRatio:"4/3", position:"relative", overflow:"hidden" }}>
            {/* fallback bg */}
            <div style={{ position:"absolute", inset:0, display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center", zIndex:0 }}>
              <span style={{ fontSize:48, opacity:.15 }}>📷</span>
              <span style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)", marginTop:8 }}>Connecting to {streamUrl}</span>
            </div>
            {/* real stream */}
            <img src={streamUrl} alt="Pi camera stream" style={{ position:"absolute", inset:0, width:"100%", height:"100%", objectFit:"cover", zIndex:1 }} onError={e=>{e.target.style.opacity=0;}}/>
            {scan && <div style={{ position:"absolute", left:0, right:0, height:3, background:"rgba(125,181,71,.8)", boxShadow:"0 0 12px var(--green)", animation:"scan 1.5s linear", zIndex:2 }}/>}
            {/* HUD */}
            <div style={{ position:"absolute", top:12, left:12, right:12, display:"flex", justifyContent:"space-between", zIndex:3 }}>
              <div style={{ background:"rgba(13,18,8,.75)", border:"1px solid var(--border)", borderRadius:3, padding:"5px 10px", fontFamily:"var(--mono)", fontSize:9, color:"var(--green2)" }}><Dot active/>Pi Camera</div>
              <div style={{ background:"rgba(13,18,8,.75)", border:"1px solid var(--border)", borderRadius:3, padding:"5px 10px", fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)" }}>{new Date().toLocaleTimeString("en-GB",{hour12:false})}</div>
            </div>
          </div>
          <div style={{ display:"flex", gap:8, marginTop:12, alignItems:"center" }}>
            <Btn onClick={doCapture} disabled={cap}>{cap?"Capturing...":"⬡ Capture Snapshot"}</Btn>
            {capMsg && <span style={{ fontFamily:"var(--mono)", fontSize:10, color:capMsg.includes("Failed")?"var(--red2)":"var(--green2)" }}>{capMsg}</span>}
          </div>
        </div>
        <div style={{ display:"flex", flexDirection:"column", gap:12 }}>
          <Card>
            <Label>Stream Info</Label>
            <div style={{ marginTop:10, display:"flex", flexDirection:"column", gap:6 }}>
              {[{l:"Host",v:si?.host||"raspberrypi.local"},{l:"Port",v:si?.port||8080},{l:"Format",v:si?.format||"MJPEG"}].map(r=>(
                <div key={r.l} style={{ display:"flex", justifyContent:"space-between", borderBottom:"1px solid var(--bg4)", paddingBottom:5 }}>
                  <span style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)" }}>{r.l}</span>
                  <span style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text2)" }}>{r.v}</span>
                </div>
              ))}
            </div>
          </Card>
          <Card>
            <Label>Capture Gallery ({caps.length})</Label>
            {caps.length===0 ? <div style={{ marginTop:8 }}><Empty msg="No captures yet"/></div> : (
              <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:6, marginTop:10 }}>
                {caps.slice(0,4).map((c,i)=>(
                  <div key={i} style={{ background:"var(--bg3)", border:"1px solid var(--border)", borderRadius:3, aspectRatio:"4/3", display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center", position:"relative", overflow:"hidden" }}>
                    <span style={{ fontSize:20, opacity:.3 }}>🌿</span>
                    <div style={{ position:"absolute", bottom:0, left:0, right:0, background:"rgba(0,0,0,.7)", padding:"2px 4px", textAlign:"center", fontFamily:"var(--mono)", fontSize:8, color:"var(--text3)" }}>
                      {c.captured_at?.slice(11,16)||"—"} · {c.size_kb}KB
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// DISEASE
// ═══════════════════════════════════════════════════════════════════════════════
function Disease() {
  const [analyzing, setAnalyzing] = useState(false);
  const lf = useCallback(()=>apiFetch("/disease/latest"),[]);
  const hf = useCallback(()=>apiFetch("/disease/predictions?limit=10"),[]);
  const sf = useCallback(()=>apiFetch("/disease/summary"),[]);
  const {data:latest, refetch:reL}  = usePoll(lf, 15000);
  const {data:history, refetch:reH} = usePoll(hf, 15000);
  const {data:summary}              = usePoll(sf, 30000);

  const d    = latest || {};
  const preds = Array.isArray(history) ? history : [];
  const SC   = {none:"dim",low:"teal",medium:"amber",high:"red"};

  const triggerAnalysis = async () => {
    setAnalyzing(true);
    await apiFetch("/camera/capture",{method:"POST"});
    let n = 0;
    const poll = setInterval(()=>{ n++; reL(); reH(); if(n>=9){clearInterval(poll);setAnalyzing(false);} }, 5000);
  };

  return (
    <div style={{ padding:24, animation:"fadeUp .4s ease both" }}>
      <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:24 }}>
        <h1 style={{ fontFamily:"var(--sans)", fontSize:22, fontWeight:800 }}>Disease Detection</h1>
        <div style={{ display:"flex", gap:8, alignItems:"center" }}>
          <Tag color="dim">Gemini 1.5 Flash</Tag>
          <Btn onClick={triggerAnalysis} variant="amber" disabled={analyzing}>
            {analyzing ? <span style={{ display:"flex", alignItems:"center", gap:6 }}><Spinner/>Analyzing...</span> : "◈ Trigger Analysis"}
          </Btn>
        </div>
      </div>

      {analyzing && (
        <Card style={{ marginBottom:16, borderColor:"var(--amber)", background:"rgba(212,160,23,.05)" }}>
          <div style={{ display:"flex", alignItems:"center", gap:12 }}>
            <Spinner/>
            <span style={{ fontFamily:"var(--mono)", fontSize:11, color:"var(--amber2)" }}>
              Capturing → Gemini Vision API → awaiting result (up to 45s)...
            </span>
          </div>
        </Card>
      )}

      <div style={{ display:"grid", gridTemplateColumns:"1.2fr 1fr", gap:16 }}>
        <div style={{ display:"flex", flexDirection:"column", gap:12 }}>
          <Card glow style={{ borderColor:"rgba(212,160,23,.3)" }}>
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", marginBottom:16 }}>
              <div>
                <Label>Current Detection</Label>
                <div style={{ fontFamily:"var(--sans)", fontSize:24, fontWeight:800, color:"var(--amber2)", marginTop:4 }}>{d.disease||"No data yet"}</div>
              </div>
              <Tag color={SC[d.severity]||"dim"}>{d.severity||"—"} severity</Tag>
            </div>
            <div style={{ display:"grid", gridTemplateColumns:"auto 1fr", gap:20, alignItems:"center" }}>
              <svg width="90" height="90" viewBox="0 0 90 90">
                <circle cx="45" cy="45" r="36" fill="none" stroke="var(--bg4)" strokeWidth="6"/>
                <circle cx="45" cy="45" r="36" fill="none" stroke="var(--amber)" strokeWidth="6" strokeLinecap="round"
                  strokeDasharray={`${2*Math.PI*36}`}
                  strokeDashoffset={`${2*Math.PI*36*(1-(d.confidence||0))}`}
                  transform="rotate(-90 45 45)"/>
                <text x="45" y="45" textAnchor="middle" dominantBaseline="central" fill="var(--amber2)" fontSize="15" fontFamily="Space Mono" fontWeight="700">
                  {d.confidence?`${(d.confidence*100).toFixed(0)}%`:"—"}
                </text>
              </svg>
              <div style={{ display:"flex", flexDirection:"column", gap:10 }}>
                {[
                  {l:"Affected Area",v:d.affected_area!=null?`${d.affected_area}%`:"—",c:"var(--red2)"},
                  {l:"Pesticide",    v:d.pesticide||"—",                                 c:"var(--text2)"},
                  {l:"Dosage",       v:d.dosage_ml!=null?`${d.dosage_ml} ml/m²`:"—",     c:"var(--green2)"},
                ].map(r=>(
                  <div key={r.l}><Label>{r.l}</Label><div style={{ fontFamily:"var(--mono)", fontSize:12, color:r.c }}>{r.v}</div></div>
                ))}
              </div>
            </div>
            {d.recommendation && (
              <div style={{ marginTop:16, padding:12, background:"var(--bg3)", borderRadius:3, borderLeft:"3px solid var(--amber)" }}>
                <Label>Recommendation</Label>
                <div style={{ fontFamily:"var(--mono)", fontSize:11, color:"var(--text2)", lineHeight:1.7, marginTop:4 }}>{d.recommendation}</div>
              </div>
            )}
            {d.recorded_at && <div style={{ marginTop:8, fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)" }}>Last scan: {new Date(d.recorded_at).toLocaleString()}</div>}
          </Card>

          {summary?.by_disease?.length > 0 && (
            <Card>
              <Label>Disease Summary (7 days)</Label>
              <div style={{ marginTop:10, display:"flex", flexDirection:"column", gap:4 }}>
                {summary.by_disease.slice(0,5).map((r,i)=>(
                  <div key={i} style={{ display:"flex", justifyContent:"space-between", padding:"5px 0", borderBottom:"1px solid var(--bg4)" }}>
                    <span style={{ fontFamily:"var(--mono)", fontSize:10, color:"var(--text2)" }}>{r.disease}</span>
                    <span style={{ fontFamily:"var(--mono)", fontSize:10, color:"var(--green2)", fontWeight:700 }}>{r.count}×</span>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>

        <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
          <div style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)", letterSpacing:"0.15em", marginBottom:4 }}>DETECTION HISTORY</div>
          {preds.length===0 ? <Card><Empty msg="No predictions yet"/></Card> : preds.map((p,i)=>(
            <div key={i} style={{ background:i===0?"var(--surface)":"var(--bg2)", border:`1px solid ${i===0?"var(--green)":"var(--border)"}`, borderRadius:4, padding:"12px 14px", display:"flex", alignItems:"center", gap:12, animation:`fadeUp ${.2+i*.06}s ease both` }}>
              <div style={{ width:4, minHeight:32, borderRadius:2, background:p.severity==="high"?"var(--red)":p.severity==="medium"?"var(--amber)":p.severity==="low"?"var(--teal)":"var(--border2)" }}/>
              <div style={{ flex:1 }}>
                <div style={{ fontFamily:"var(--mono)", fontSize:11, color:"var(--text)", fontWeight:700 }}>{p.disease}</div>
                <div style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)", marginTop:2 }}>
                  {p.recorded_at?new Date(p.recorded_at).toLocaleString():"—"} · {p.confidence?`${(p.confidence*100).toFixed(0)}%`:""} · {p.dosage_ml>0?`${p.dosage_ml}ml/m²`:"no spray"}
                </div>
              </div>
              <Tag color={SC[p.severity]||"dim"}>{p.severity||"—"}</Tag>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// MOTOR
// ═══════════════════════════════════════════════════════════════════════════════
function Motor({ mode }) {
  const [dosage, setDosage] = useState(25);
  const [busy,   setBusy]   = useState(false);
  const [msg,    setMsg]    = useState("");
  const stf = useCallback(()=>apiFetch("/motor/status"),[]);
  const ssf = useCallback(()=>apiFetch("/motor/stats"),[]);
  const hf  = useCallback(()=>apiFetch("/motor/history?limit=8"),[]);
  const {data:status,  refetch:reSt} = usePoll(stf, 3000);
  const {data:stats}                 = usePoll(ssf, 10000);
  const {data:history, refetch:reH}  = usePoll(hf,  10000);
  const running = status?.running || false;
  const evts    = Array.isArray(history) ? history : [];

  const cmd = async (action) => {
    setBusy(true); setMsg("");
    const r = await apiFetch(`/motor/${action}`, { method:"POST", body:action==="on"?JSON.stringify({dosage_ml:dosage,trigger:"manual"}):undefined });
    setMsg(r ? (action==="on"?"Pump started!":"Pump stopped!") : "Command failed");
    setBusy(false); reSt(); reH();
  };

  return (
    <div style={{ padding:24, animation:"fadeUp .4s ease both" }}>
      <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:24 }}>
        <h1 style={{ fontFamily:"var(--sans)", fontSize:22, fontWeight:800 }}>Motor Control</h1>
        <Tag color={mode==="auto"?"green":"amber"}>{mode} mode</Tag>
      </div>
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:16 }}>
        <Card style={{ textAlign:"center" }}>
          <div style={{ position:"relative", width:140, height:140, margin:"0 auto 24px" }}>
            {running && [1,2,3].map(r=>(
              <div key={r} style={{ position:"absolute", inset:-r*14, borderRadius:"50%", border:"1px solid var(--green)", opacity:.3/r, animation:`pulse ${r*.5+1}s ease-in-out infinite` }}/>
            ))}
            <div style={{ width:"100%", height:"100%", borderRadius:"50%", background:running?"var(--green-dim)":"var(--bg3)", border:`2px solid ${running?"var(--green)":"var(--border)"}`, display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center", gap:6, boxShadow:running?"0 0 30px rgba(125,181,71,.3)":"none" }}>
              <span style={{ fontSize:36 }}>{running?"💧":"⭕"}</span>
              <span style={{ fontFamily:"var(--mono)", fontSize:10, color:running?"var(--green2)":"var(--text3)", letterSpacing:"0.1em" }}>{running?"RUNNING":"IDLE"}</span>
            </div>
          </div>
          {msg && <div style={{ fontFamily:"var(--mono)", fontSize:10, color:msg.includes("failed")?"var(--red2)":"var(--green2)", marginBottom:12 }}>{msg}</div>}
          {mode!=="manual" && <div style={{ marginBottom:12, fontFamily:"var(--mono)", fontSize:10, color:"var(--text3)", background:"var(--bg3)", padding:"8px 12px", borderRadius:3 }}>Switch to MANUAL mode to control</div>}
          <div style={{ display:"flex", gap:8, justifyContent:"center" }}>
            <Btn onClick={()=>cmd("on")}  variant="primary" disabled={busy||running||mode!=="manual"}>▶ START</Btn>
            <Btn onClick={()=>cmd("off")} variant="red"     disabled={busy||!running}>■ STOP</Btn>
          </div>
        </Card>

        <div style={{ display:"flex", flexDirection:"column", gap:12 }}>
          <Card>
            <Label>Dosage</Label>
            <div style={{ marginTop:12 }}>
              <div style={{ display:"flex", justifyContent:"space-between", marginBottom:8 }}>
                <span style={{ fontFamily:"var(--mono)", fontSize:10, color:"var(--text2)" }}>Target: {dosage} ml/m²</span>
                <div style={{ display:"flex", gap:6 }}>
                  {[10,20,30,50].map(v=>(
                    <button key={v} onClick={()=>setDosage(v)} style={{ fontFamily:"var(--mono)", fontSize:9, padding:"3px 8px", background:dosage===v?"var(--green-dim)":"var(--bg4)", border:`1px solid ${dosage===v?"var(--green)":"var(--border)"}`, color:dosage===v?"var(--green2)":"var(--text3)", borderRadius:2, cursor:"pointer" }}>{v}</button>
                  ))}
                </div>
              </div>
              <input type="range" min={0} max={100} value={dosage} onChange={e=>setDosage(+e.target.value)} style={{ width:"100%", accentColor:"var(--green)" }}/>
            </div>
          </Card>
          <Card>
            <Label>Stats</Label>
            <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:10, marginTop:10 }}>
              {[
                {l:"Today (L)",  v:stats?.today?.litres??  "—", c:"var(--green2)"},
                {l:"Sessions",   v:stats?.today?.sessions??"—", c:"var(--teal2)" },
                {l:"Week (L)",   v:stats?.this_week?.litres??"—",c:"var(--text2)"},
                {l:"Mode",       v:status?.mode??"—",             c:"var(--amber2)"},
              ].map(s=>(
                <div key={s.l} style={{ background:"var(--bg3)", borderRadius:3, padding:"10px 12px" }}>
                  <Label>{s.l}</Label>
                  <div style={{ fontFamily:"var(--mono)", fontSize:13, color:s.c, fontWeight:700, marginTop:2 }}>{s.v}</div>
                </div>
              ))}
            </div>
          </Card>
          <Card>
            <Label>Recent Events</Label>
            <div style={{ marginTop:8, display:"flex", flexDirection:"column", gap:3 }}>
              {evts.length===0 ? <Empty msg="No events yet"/> : evts.slice(0,6).map((e,i)=>(
                <div key={i} style={{ display:"flex", justifyContent:"space-between", padding:"5px 0", borderBottom:"1px solid var(--bg4)", fontFamily:"var(--mono)", fontSize:9 }}>
                  <span style={{ color:e.event_type?.includes("on")?"var(--green2)":"var(--red2)" }}>{(e.event_type||"").toUpperCase()}</span>
                  <span style={{ color:"var(--text3)" }}>{e.dosage_ml!=null?`${e.dosage_ml}ml/m²`:""}</span>
                  <span style={{ color:"var(--text3)" }}>{e.recorded_at?new Date(e.recorded_at).toLocaleTimeString():""}</span>
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
// LOGS
// ═══════════════════════════════════════════════════════════════════════════════
function Logs() {
  const [filter, setFilter] = useState("ALL");
  const [search, setSearch] = useState("");
  const [hours,  setHours]  = useState(24);
  const LC = {INFO:"teal",WARN:"amber",ERROR:"red"};

  const lf = useCallback(()=>{
    const lv = filter!=="ALL"?`&level=${filter}`:"";
    const q  = search?`&search=${encodeURIComponent(search)}`:"";
    return apiFetch(`/logs/?limit=200&hours=${hours}${lv}${q}`);
  },[filter,search,hours]);

  const {data:logs, loading, refetch} = usePoll(lf, 5000);
  const entries = Array.isArray(logs) ? logs : [];

  return (
    <div style={{ padding:24, animation:"fadeUp .4s ease both" }}>
      <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:24 }}>
        <h1 style={{ fontFamily:"var(--sans)", fontSize:22, fontWeight:800 }}>System Logs</h1>
        <div style={{ display:"flex", gap:8 }}>
          {loading && <Spinner/>}
          <Btn variant="ghost" small onClick={()=>window.open(`${API_BASE}/logs/export?hours=${hours}${filter!=="ALL"?`&level=${filter}`:""}`)}>↓ CSV</Btn>
        </div>
      </div>

      <Card style={{ marginBottom:12 }}>
        <div style={{ display:"flex", gap:12, alignItems:"center", flexWrap:"wrap" }}>
          <div style={{ display:"flex", gap:4 }}>
            {["ALL","INFO","WARN","ERROR"].map(l=>(
              <button key={l} onClick={()=>setFilter(l)} style={{ fontFamily:"var(--mono)", fontSize:9, padding:"5px 12px", letterSpacing:"0.08em", background:filter===l?"var(--surface)":"transparent", border:`1px solid ${filter===l?"var(--border2)":"var(--border)"}`, color:filter===l?"var(--text)":"var(--text3)", borderRadius:2, cursor:"pointer" }}>{l}</button>
            ))}
          </div>
          <input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search..."
            style={{ flex:1, background:"var(--bg3)", border:"1px solid var(--border)", color:"var(--text)", fontFamily:"var(--mono)", fontSize:11, padding:"6px 12px", borderRadius:3, outline:"none", minWidth:150 }}/>
          <select value={hours} onChange={e=>setHours(+e.target.value)} style={{ background:"var(--bg3)", border:"1px solid var(--border)", color:"var(--text2)", fontFamily:"var(--mono)", fontSize:9, padding:"6px 8px", borderRadius:3, outline:"none" }}>
            {[1,6,12,24,48,168].map(h=><option key={h} value={h}>{h}h</option>)}
          </select>
          <span style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)" }}>{entries.length} entries</span>
        </div>
      </Card>

      <div style={{ display:"flex", flexDirection:"column", gap:2 }}>
        {entries.length===0 ? (
          <Card><div style={{ textAlign:"center", padding:32 }}><Empty msg={loading?"Loading...":"No logs match filter"}/></div></Card>
        ) : entries.map((l,i)=>(
          <div key={i} style={{ display:"grid", gridTemplateColumns:"70px 90px 1fr 120px", gap:12, alignItems:"center", padding:"10px 14px", borderRadius:3, background:i%2===0?"var(--bg2)":"var(--bg3)" }}>
            <Tag color={LC[l.level]||"dim"}>{l.level}</Tag>
            <span style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)" }}>{l.created_at?new Date(l.created_at).toLocaleTimeString():"—"}</span>
            <span style={{ fontFamily:"var(--mono)", fontSize:11, color:"var(--text2)" }}>{l.message}</span>
            <span style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)", textAlign:"right" }}>{l.source||"—"}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// SETTINGS
// ═══════════════════════════════════════════════════════════════════════════════
function Settings() {
  const [health, setHealth]   = useState(null);
  const [saved,  setSaved]    = useState(false);
  useEffect(()=>{ apiFetch("/health").then(d=>setHealth(d)); },[]);

  return (
    <div style={{ padding:24, animation:"fadeUp .4s ease both" }}>
      <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:24 }}>
        <h1 style={{ fontFamily:"var(--sans)", fontSize:22, fontWeight:800 }}>Settings</h1>
        <Btn onClick={()=>{setSaved(true);setTimeout(()=>setSaved(false),2000);}} variant={saved?"ghost":"primary"}>{saved?"✓ Saved":"Save"}</Btn>
      </div>
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:16 }}>
        <div style={{ display:"flex", flexDirection:"column", gap:12 }}>
          <Card>
            <Label>Backend Status</Label>
            <div style={{ marginTop:12, display:"flex", flexDirection:"column", gap:8 }}>
              {health ? (
                <>
                  <div style={{ display:"flex", justifyContent:"space-between" }}>
                    <span style={{ fontFamily:"var(--mono)", fontSize:10, color:"var(--text3)" }}>API</span>
                    <Tag color="green">Online · v{health.version}</Tag>
                  </div>
                  <div style={{ display:"flex", justifyContent:"space-between" }}>
                    <span style={{ fontFamily:"var(--mono)", fontSize:10, color:"var(--text3)" }}>MQTT Bridge</span>
                    <Tag color={health.mqtt_connected?"green":"red"}>{health.mqtt_connected?"Connected":"Disconnected"}</Tag>
                  </div>
                  <div style={{ display:"flex", justifyContent:"space-between" }}>
                    <span style={{ fontFamily:"var(--mono)", fontSize:10, color:"var(--text3)" }}>API URL</span>
                    <span style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text2)" }}>{API_BASE}</span>
                  </div>
                </>
              ) : <Empty msg={`Checking ${API_BASE}...`}/>}
            </div>
          </Card>

          <Card>
            <Label>API Endpoint</Label>
            <div style={{ marginTop:10 }}>
              <div style={{ fontFamily:"var(--mono)", fontSize:10, color:"var(--text3)", marginBottom:6 }}>
                Set in <code style={{ color:"var(--green2)" }}>frontend/.env.local</code>
              </div>
              <div style={{ padding:"8px 12px", background:"var(--bg3)", borderRadius:3, fontFamily:"var(--mono)", fontSize:11, color:"var(--amber2)", marginBottom:10 }}>
                VITE_API_URL={API_BASE}
              </div>
              <a href={`${API_BASE}/docs`} target="_blank" rel="noreferrer" style={{ fontFamily:"var(--mono)", fontSize:10, color:"var(--teal2)" }}>
                → Open Swagger API Docs
              </a>
            </div>
          </Card>

          <Card>
            <Label>Quick Links</Label>
            <div style={{ display:"flex", flexDirection:"column", gap:6, marginTop:10 }}>
              {[
                {l:"Health Check",   u:`${API_BASE}/health`},
                {l:"Latest Sensors", u:`${API_BASE}/sensors/latest`},
                {l:"Latest Disease", u:`${API_BASE}/disease/latest`},
                {l:"Motor Status",   u:`${API_BASE}/motor/status`},
                {l:"System Logs",    u:`${API_BASE}/logs/`},
              ].map(r=>(
                <a key={r.l} href={r.u} target="_blank" rel="noreferrer" style={{ display:"flex", justifyContent:"space-between", fontFamily:"var(--mono)", fontSize:10, color:"var(--teal2)", textDecoration:"none", padding:"5px 0", borderBottom:"1px solid var(--bg4)" }}>
                  <span>{r.l}</span><span style={{ color:"var(--text3)" }}>→</span>
                </a>
              ))}
            </div>
          </Card>
        </div>

        <div style={{ display:"flex", flexDirection:"column", gap:12 }}>
          <Card>
            <Label>Alert Thresholds</Label>
            <div style={{ marginTop:12, display:"flex", flexDirection:"column", gap:10 }}>
              {[
                {l:"pH",         lo:5.5, hi:7.5, unit:"",   env:"PH_MIN / PH_MAX"},
                {l:"Moisture",   lo:40,  hi:80,  unit:"%",  env:"MOISTURE_MIN / MAX"},
                {l:"Humidity",   lo:30,  hi:90,  unit:"%",  env:"HUMIDITY_MIN / MAX"},
                {l:"Temperature",lo:15,  hi:35,  unit:"°C", env:"TEMP_MIN / TEMP_MAX"},
              ].map(t=>(
                <div key={t.l} style={{ borderBottom:"1px solid var(--bg4)", paddingBottom:8 }}>
                  <div style={{ display:"flex", justifyContent:"space-between" }}>
                    <span style={{ fontFamily:"var(--mono)", fontSize:10, color:"var(--text3)" }}>{t.l}</span>
                    <div style={{ display:"flex", gap:6 }}>
                      <span style={{ fontFamily:"var(--mono)", fontSize:10, color:"var(--teal2)" }}>{t.lo}{t.unit}</span>
                      <span style={{ color:"var(--text3)", fontSize:9 }}>—</span>
                      <span style={{ fontFamily:"var(--mono)", fontSize:10, color:"var(--amber2)" }}>{t.hi}{t.unit}</span>
                    </div>
                  </div>
                  <div style={{ fontFamily:"var(--mono)", fontSize:8, color:"var(--text3)", marginTop:3 }}>backend/.env: {t.env}</div>
                </div>
              ))}
            </div>
          </Card>

          <Card>
            <Label>Environment Variables</Label>
            <div style={{ marginTop:10, display:"flex", flexDirection:"column", gap:8 }}>
              {[
                {file:"raspberry_pi/.env",   key:"GEMINI_API_KEY",        note:"Required for disease detection"},
                {file:"raspberry_pi/.env",   key:"MQTT_BROKER_IP",        note:"IP of your Mosquitto broker"},
                {file:"raspberry_pi/.env",   key:"INFERENCE_INTERVAL",    note:"Seconds between AI scans"},
                {file:"backend/.env",        key:"DATABASE_URL",          note:"sqlite:///./agriwatch.db"},
                {file:"frontend/.env.local", key:"VITE_API_URL",          note:"http://localhost:8000"},
              ].map(r=>(
                <div key={r.key} style={{ background:"var(--bg3)", borderRadius:3, padding:"8px 12px" }}>
                  <div style={{ display:"flex", justifyContent:"space-between", marginBottom:2 }}>
                    <span style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--green2)", fontWeight:700 }}>{r.key}</span>
                    <span style={{ fontFamily:"var(--mono)", fontSize:8, color:"var(--text3)" }}>{r.file}</span>
                  </div>
                  <div style={{ fontFamily:"var(--mono)", fontSize:8, color:"var(--text3)" }}>{r.note}</div>
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
  const [ok,   setOk]   = useState(false);

  useEffect(()=>{
    const check = async () => {
      const h = await apiFetch("/health");
      setOk(!!h);
      const m = await apiFetch("/mode/");
      if (m?.mode) setMode(m.mode);
    };
    check();
    const id = setInterval(check, 10000);
    return ()=>clearInterval(id);
  },[]);

  const pages = {
    dashboard:<Dashboard mode={mode} setPage={setPage}/>,
    sensors:  <Sensors/>,
    camera:   <Camera/>,
    disease:  <Disease/>,
    motor:    <Motor mode={mode}/>,
    logs:     <Logs/>,
    settings: <Settings/>,
  };

  return (
    <>
      <style>{css}</style>
      <div style={{ display:"flex", minHeight:"100vh", background:"var(--bg)" }}>
        <Sidebar page={page} setPage={setPage} ok={ok}/>
        <div style={{ flex:1, marginLeft:64, paddingTop:52, minHeight:"100vh" }}>
          <TopBar page={page} mode={mode} onMode={setMode} ok={ok}/>
          <div style={{ maxWidth:1200, margin:"0 auto" }}>
            {pages[page]}
          </div>
        </div>
      </div>
    </>
  );
}
