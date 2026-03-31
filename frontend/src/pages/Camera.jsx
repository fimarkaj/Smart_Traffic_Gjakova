import TopBar from '../components/layout/TopBar'
import { ModuleHeader, KpiBlock } from '../components/shared'
import { useLiveStore } from '../store'

export default function Camera() {
  const cameraHealth = useLiveStore((s) => s.cameraHealth)
  const lastFrame    = useLiveStore((s) => s.lastFrame)
  const roiCounts    = useLiveStore((s) => s.roiCounts)

  const status   = cameraHealth?.status || 'unknown'
  const dotCls   = { ok:'dot-g', degraded:'dot-a', down:'dot-r', unknown:'dot-d' }[status] || 'dot-d'
  const statColor= { ok:'var(--green)', degraded:'var(--amber)', down:'var(--red)', unknown:'var(--t2)' }[status]

  const stats = [
    { label:'STATUS',     value:status.toUpperCase(),                                color:statColor },
    { label:'FPS',        value:cameraHealth?.fps_actual ?? '—',                     color:'var(--green)' },
    { label:'RECONNECTS', value:cameraHealth?.reconnect_count ?? '—',               color:'var(--t2)' },
    { label:'UPTIME',     value:cameraHealth?.uptime_seconds ? `${Math.floor(cameraHealth.uptime_seconds/60)}m` : '—', color:'var(--t2)' },
    { label:'LAST FRAME', value:cameraHealth?.last_frame_age_s != null ? `${cameraHealth.last_frame_age_s}s ago` : '—', color:'var(--t2)' },
    { label:'FAILURES',   value:cameraHealth?.consecutive_failures ?? '—',           color:cameraHealth?.consecutive_failures>0?'var(--red)':'var(--t2)' },
  ]

  return (
    <div style={{ display:'flex', flexDirection:'column', height:'100%', overflow:'hidden' }}>
      <TopBar title="CAMERA / CALIBRATION" subtitle="DEVICE STATE · NODE-01" />
      <div className="page-body">

        <div style={{ display:'grid', gridTemplateColumns:'1fr 320px', gap:12 }}>

          {/* Feed + crop info */}
          <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
            <div className="panel" style={{ padding:12 }}>
              <ModuleHeader label="Live Preview — 800×600 Crop" id="CAM-PREV"
                right={<div style={{ display:'flex', alignItems:'center', gap:6 }}><span className={`dot ${dotCls}`} /><span style={{ fontFamily:'var(--fm)', fontSize:11, color:statColor }}>{status.toUpperCase()}</span></div>}
              />
              {/* Strict 4:3 container */}
              <div style={{ position:'relative', width:'100%', paddingBottom:'75%', background:'#000' }}>
                {lastFrame ? (
                  <img src={`data:image/jpeg;base64,${lastFrame}`} alt="cam"
                    style={{ position:'absolute', top:0, left:0, width:'100%', height:'100%', objectFit:'contain' }} />
                ) : (
                  <div style={{ position:'absolute', inset:0, display:'flex', alignItems:'center', justifyContent:'center', background:'var(--base)' }}>
                    <span style={{ fontFamily:'var(--fm)', fontSize:10, color:'var(--t4)', letterSpacing:'.2em' }}>NO SIGNAL</span>
                  </div>
                )}
                {/* Corner brackets */}
                {[['top','left'],['top','right'],['bottom','left'],['bottom','right']].map(([v,h])=>(
                  <div key={`${v}${h}`} style={{ position:'absolute',[v]:10,[h]:10,width:14,height:14,
                    borderTop:v==='top'?'1px solid var(--green)':'none',borderBottom:v==='bottom'?'1px solid var(--green)':'none',
                    borderLeft:h==='left'?'1px solid var(--green)':'none',borderRight:h==='right'?'1px solid var(--green)':'none',opacity:.6 }} />
                ))}
              </div>

              {/* Crop + model meta */}
              <div style={{ marginTop:10, display:'grid', gridTemplateColumns:'1fr 1fr', gap:8 }}>
                <div style={{ background:'var(--raised)', border:'1px solid var(--b-faint)', padding:'10px 12px' }}>
                  <p style={{ fontFamily:'var(--fm)', fontSize:9, color:'var(--t4)', letterSpacing:'.15em', marginBottom:8 }}>CROP SETTINGS</p>
                  {[['X1/X2','0 / 800'],['Y1/Y2','0 / 600'],['Resolution','800 × 600'],['Aspect','4:3']].map(([k,v])=>(
                    <div key={k} className="meta-row" style={{ padding:'5px 0' }}>
                      <span style={{ fontFamily:'var(--fm)', fontSize:11, color:'var(--t3)' }}>{k}</span>
                      <span style={{ fontFamily:'var(--fm)', fontSize:11, color:'var(--t1)' }}>{v}</span>
                    </div>
                  ))}
                </div>
                <div style={{ background:'var(--raised)', border:'1px solid var(--b-faint)', padding:'10px 12px' }}>
                  <p style={{ fontFamily:'var(--fm)', fontSize:9, color:'var(--t4)', letterSpacing:'.15em', marginBottom:8 }}>MODEL SETTINGS</p>
                  {[['Model','YOLOv11 / best.pt'],['Confidence','0.15'],['IoU','0.45'],['Car class','ID 0']].map(([k,v])=>(
                    <div key={k} className="meta-row" style={{ padding:'5px 0' }}>
                      <span style={{ fontFamily:'var(--fm)', fontSize:11, color:'var(--t3)' }}>{k}</span>
                      <span style={{ fontFamily:'var(--fm)', fontSize:11, color:'var(--t1)' }}>{v}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Right column */}
          <div style={{ display:'flex', flexDirection:'column', gap:12 }}>

            {/* Health stats grid */}
            <div className="panel" style={{ padding:12 }}>
              <ModuleHeader label="Camera Health" id="CAM-HLTH" />
              <div style={{ display:'grid', gridTemplateColumns:'repeat(2,1fr)', gap:6 }}>
                {stats.map(({ label, value, color }) => (
                  <div key={label} style={{ background:'var(--raised)', border:'1px solid var(--b-faint)', padding:'9px 11px' }}>
                    <p style={{ fontFamily:'var(--fm)', fontSize:9, color:'var(--t4)', letterSpacing:'.15em', marginBottom:4 }}>{label}</p>
                    <p style={{ fontFamily:'var(--fp)', fontSize:18, color }}>{value}</p>
                  </div>
                ))}
              </div>
              {cameraHealth?.last_error && (
                <div style={{ marginTop:8, padding:'7px 10px', background:'var(--red-lo)', border:'1px solid rgba(244,63,94,.22)' }}>
                  <p style={{ fontFamily:'var(--fm)', fontSize:10, color:'var(--red)', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>
                    ERR: {cameraHealth.last_error}
                  </p>
                </div>
              )}
            </div>

            {/* ROI list (live) */}
            <div className="panel" style={{ padding:12, flex:1, overflow:'auto' }}>
              <ModuleHeader label="Live Zona Counts" id="CAM-ZONA" />
              {Object.keys(roiCounts).length === 0 ? (
                <div style={{ padding:'1.5rem', textAlign:'center' }}>
                  <span style={{ fontFamily:'var(--fm)', fontSize:10, color:'var(--t4)', letterSpacing:'.18em' }}>AWAITING STREAM</span>
                </div>
              ) : Object.entries(roiCounts).map(([name, count]) => {
                const color = count<=4?'var(--green)':count<=9?'var(--amber)':'var(--red)'
                return (
                  <div key={name} className="meta-row">
                    <span style={{ fontFamily:'var(--fm)', fontSize:12, color:'var(--t1)' }}>{name}</span>
                    <span style={{ fontFamily:'var(--fp)', fontSize:20, color }}>{count}</span>
                  </div>
                )
              })}
            </div>

            {/* Config paths */}
            <div className="panel" style={{ padding:12 }}>
              <ModuleHeader label="Config Paths" id="CAM-PATH" />
              {[
                { label:'Zona CSV',    value:'D:/Yolov11/rois_polygons.csv' },
                { label:'Lines JSON', value:'D:/Yolov11/finalcode3/counting_lines.json' },
              ].map(({ label, value }) => (
                <div key={label} style={{ marginBottom:10 }}>
                  <p style={{ fontFamily:'var(--fm)', fontSize:9, color:'var(--t4)', letterSpacing:'.15em', marginBottom:3 }}>{label}</p>
                  <p style={{ fontFamily:'var(--fm)', fontSize:11, color:'var(--t2)', wordBreak:'break-all', lineHeight:1.6 }}>{value}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
