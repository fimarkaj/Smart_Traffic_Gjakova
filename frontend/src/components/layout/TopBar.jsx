import { useEffect, useState } from 'react'
import { useLiveStore } from '../../store'

export default function TopBar({ title, subtitle }) {
  const [time, setTime] = useState('')
  const connected    = useLiveStore((s) => s.connected)
  const cameraHealth = useLiveStore((s) => s.cameraHealth)
  const timestamp    = useLiveStore((s) => s.timestamp)

  useEffect(() => {
    const tick = () => {
      const d = timestamp ? new Date(timestamp * 1000) : new Date()
      setTime(d.toLocaleTimeString('en-GB', { hour12:false }))
    }
    tick()
    const id = setInterval(tick, 1000)
    return () => clearInterval(id)
  }, [timestamp])

  const camStatus = cameraHealth?.status || 'unknown'
  const camDot  = { ok:'dot-g', degraded:'dot-a', down:'dot-r', unknown:'dot-d' }[camStatus] || 'dot-d'
  const camColor = { ok:'var(--green)', degraded:'var(--amber)', down:'var(--red)', unknown:'var(--t2)' }[camStatus]

  return (
    <header style={{
      height:56, background:'var(--surface)',
      borderBottom:'1px solid var(--b-faint)',
      display:'flex', alignItems:'center', justifyContent:'space-between',
      padding:'0 20px', flexShrink:0, gap:20, position:'relative',
    }}>
      {/* Left */}
      <div style={{ display:'flex', alignItems:'baseline', gap:12, minWidth:0 }}>
        <span style={{
          fontFamily:'var(--fp)', fontSize:22, color:'var(--green)',
          textShadow:'0 0 8px rgba(52,210,110,.4)',
          letterSpacing:'.1em', lineHeight:1, whiteSpace:'nowrap', userSelect:'none',
        }}>
          {title}
        </span>
        {subtitle && (
          <span style={{ fontFamily:'var(--fm)', fontSize:10, color:'var(--t4)', letterSpacing:'.2em', whiteSpace:'nowrap' }}>
            {subtitle}
          </span>
        )}
      </div>

      {/* Center divider */}
      <div style={{ flex:1, height:1, background:'linear-gradient(90deg,var(--b-faint),var(--b-dim),var(--b-faint))' }} />

      {/* Right cluster */}
      <div style={{ display:'flex', alignItems:'center', gap:24, flexShrink:0 }}>

        {/* Clock */}
        <div style={{ display:'flex', alignItems:'center', gap:6 }}>
          <span style={{ fontFamily:'var(--fm)', fontSize:9, color:'var(--t3)', letterSpacing:'.15em' }}>UTC+1</span>
          <span style={{ fontFamily:'var(--fp)', fontSize:18, color:'var(--t1)', letterSpacing:'.05em' }}>{time}</span>
        </div>

        {/* Camera */}
        <div style={{ display:'flex', alignItems:'center', gap:6 }}>
          <span style={{ fontFamily:'var(--fm)', fontSize:9, color:'var(--t3)', letterSpacing:'.12em' }}>CAM·01</span>
          <span className={`dot ${camDot}`} />
          <span style={{ fontFamily:'var(--fm)', fontSize:11, color:camColor }}>
            {camStatus.toUpperCase()}
            {cameraHealth?.fps_actual ? ` · ${cameraHealth.fps_actual}FPS` : ''}
          </span>
        </div>

        {/* Stream */}
        <div style={{ display:'flex', alignItems:'center', gap:6 }}>
          <span style={{ fontFamily:'var(--fm)', fontSize:9, color:'var(--t3)', letterSpacing:'.12em' }}>STREAM</span>
          <span className={`dot ${connected ? 'dot-g' : 'dot-r'}`} />
          <span style={{ fontFamily:'var(--fm)', fontSize:11, color: connected ? 'var(--green)' : 'var(--red)' }}>
            {connected ? 'LIVE' : 'OFFLINE'}
          </span>
        </div>

        <span style={{ fontFamily:'var(--fm)', fontSize:9, color:'var(--t4)', letterSpacing:'.12em' }}>STAI·v2.0</span>
      </div>

      {/* Bottom accent */}
      <div style={{ position:'absolute', bottom:0, left:0, right:0, height:1, background:'linear-gradient(90deg,transparent,var(--green),transparent)', opacity:.12 }} />
    </header>
  )
}
