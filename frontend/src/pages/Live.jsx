import { useWebSocket } from '../hooks/useWebSocket'
import TopBar from '../components/layout/TopBar'
import VideoCanvas from '../components/live/VideoCanvas'
import LiveChart from '../components/live/LiveChart'
import { ModuleHeader, KpiBlock, StatusTag, BarRow } from '../components/shared'
import { useLiveStore } from '../store'

function congestionStatus(count) {
  return count <= 4 ? 'low' : count <= 9 ? 'moderate' : 'heavy'
}
function congestionColor(status) {
  return status === 'low' ? 'var(--green)' : status === 'moderate' ? 'var(--amber)' : 'var(--red)'
}
const MAX_COUNT = 15

export default function Live() {
  useWebSocket()

  const roiCounts           = useLiveStore((s) => s.roiCounts)
  const totalCars         = useLiveStore((s) => s.totalCars)
  const cameraHealth     = useLiveStore((s) => s.cameraHealth)
  const connected        = useLiveStore((s) => s.connected)

  const entries      = Object.entries(roiCounts)
  const heavyCount   = entries.filter(([,v]) => v >= 10).length
  const overallSt    = heavyCount >= 2 ? 'heavy' : heavyCount >= 1 ? 'moderate' : 'low'
  const camColor     = { ok:'green', degraded:'amber', down:'red', unknown:'dim' }[cameraHealth?.status] || 'dim'

  return (
    <div style={{ display:'flex', flexDirection:'column', height:'100%', overflow:'hidden' }}>
      <TopBar title="LIVE MONITOR" subtitle="GJAKOVA JUNCTION · NODE-01" />
      <div className="page-body">

        {/* Status KPIs */}
        <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:8 }}>
          <KpiBlock label="Stream Status"     value={cameraHealth?.status?.toUpperCase() || '—'}
            sub={cameraHealth?.fps_actual ? `${cameraHealth.fps_actual} FPS` : undefined}
            color={camColor} size="md" />
          <KpiBlock label="Live Occupancy"
            value={totalCars ?? 0}
            sub={entries.length ? `${entries.filter(([,v]) => v > 0).length} active zona${entries.filter(([,v]) => v > 0).length === 1 ? '' : 's'}` : 'awaiting zonas'} color="cyan" size="md" />
          <KpiBlock label="Congestion"        value={overallSt.toUpperCase()}
            sub={heavyCount > 0 ? `${heavyCount} zona${heavyCount>1?'s':''} heavy` : 'all zona nominal'}
            color={overallSt === 'low' ? 'green' : overallSt === 'moderate' ? 'amber' : 'red'} size="md" />
          <KpiBlock label="Reconnects"
            value={cameraHealth?.reconnect_count ?? '—'}
            sub={`uptime: ${cameraHealth?.uptime_seconds ? `${Math.floor(cameraHealth.uptime_seconds/60)}m` : '—'}`}
            color="dim" size="md" />
        </div>

        {/* Main grid */}
        <div style={{ display:'grid', gridTemplateColumns:'1fr 300px', gap:12, flex:1, minHeight:0 }}>

          {/* Left */}
          <div style={{ display:'flex', flexDirection:'column', gap:12, minWidth:0 }}>
            <div className="panel" style={{ padding:12 }}>
              <ModuleHeader label="Detection Feed" id="VID-01"
                right={<span style={{ fontFamily:'var(--fm)', fontSize:10, color:'var(--t3)' }}>800×600 · 4:3 · CROP ACTIVE</span>}
              />
              <VideoCanvas />
              {/* Stream meta strip */}
              <div style={{ marginTop:10, display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:6 }}>
                {[
                  { k:'RESOLUTION', v:'800 × 600' },
                  { k:'CROP',       v:'[800,600,0,250]' },
                  { k:'MODEL',      v:'YOLOv11 · best.pt' },
                ].map(({ k, v }) => (
                  <div key={k} style={{ background:'var(--raised)', border:'1px solid var(--b-faint)', padding:'6px 10px' }}>
                    <p style={{ fontFamily:'var(--fm)', fontSize:9, color:'var(--t4)', letterSpacing:'.15em', marginBottom:3 }}>{k}</p>
                    <p style={{ fontFamily:'var(--fm)', fontSize:11, color:'var(--t2)', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{v}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="panel" style={{ padding:12 }}>
              <ModuleHeader label="Occupancy Trend — Last 120 Samples" id="PLT-01" />
              <LiveChart />
            </div>
          </div>

          {/* Right */}
          <div style={{ display:'flex', flexDirection:'column', gap:12, minWidth:0 }}>
            <div className="panel" style={{ padding:12, flex:1, overflow:'auto' }}>
              <ModuleHeader label="Zona Occupancy" id="ZONA-01"
                right={<span style={{ fontFamily:'var(--fm)', fontSize:9, color:'var(--t4)' }}>5s INTERVAL</span>}
              />
              {entries.length === 0 ? (
                <div style={{ padding:'2rem', textAlign:'center' }}>
                  <span style={{ fontFamily:'var(--fm)', fontSize:10, color:'var(--t4)', letterSpacing:'.2em' }}>AWAITING DATA</span>
                </div>
              ) : entries.map(([name, count]) => {
                const st = congestionStatus(count)
                return (
                  <BarRow key={name} label={name} value={count} max={MAX_COUNT}
                    color={congestionColor(st)} right={<StatusTag status={st} />}
                  />
                )
              })}
            </div>

            {/* Threshold legend */}
            <div className="panel" style={{ padding:12 }}>
              <ModuleHeader label="Threshold Legend" id="LEG-01" />
              {[
                { label:'LOW',      desc:'0–4 vehicles',  cls:'tag-g' },
                { label:'MODERATE', desc:'5–9 vehicles',  cls:'tag-a' },
                { label:'HEAVY',    desc:'10+ vehicles',  cls:'tag-r' },
              ].map(({ label, desc, cls }) => (
                <div key={label} style={{ display:'flex', alignItems:'center', gap:10, padding:'6px 8px', background:'var(--raised)', border:'1px solid var(--b-faint)', marginBottom:3 }}>
                  <span className={`tag ${cls}`}>{label}</span>
                  <span style={{ fontFamily:'var(--fm)', fontSize:11, color:'var(--t2)' }}>{desc}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
