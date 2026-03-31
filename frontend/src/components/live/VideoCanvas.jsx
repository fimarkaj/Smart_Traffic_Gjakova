import { useEffect, useRef } from 'react'
import { useLiveStore } from '../../store'

export default function VideoCanvas() {
  const canvasRef = useRef(null)
  const lastFrame = useLiveStore((s) => s.lastFrame)
  const connected = useLiveStore((s) => s.connected)

  useEffect(() => {
    if (!lastFrame || !canvasRef.current) return
    const img = new Image()
    img.onload = () => {
      const ctx = canvasRef.current?.getContext('2d')
      if (!ctx) return
      canvasRef.current.width  = img.width
      canvasRef.current.height = img.height
      ctx.drawImage(img, 0, 0)
    }
    img.src = `data:image/jpeg;base64,${lastFrame}`
  }, [lastFrame])

  return (
    <div className="scanpanel" style={{ position:'relative', background:'#000', width:'100%' }}>
      {/* Strict 4:3 (800×600) */}
      <div style={{ position:'relative', width:'100%', paddingBottom:'75%' }}>
        <canvas ref={canvasRef} style={{ position:'absolute', top:0, left:0, width:'100%', height:'100%', display:'block', objectFit:'contain' }} />

        {/* Corner brackets */}
        {[['top','left'],['top','right'],['bottom','left'],['bottom','right']].map(([v,h]) => (
          <div key={`${v}${h}`} style={{
            position:'absolute', [v]:10, [h]:10,
            width:14, height:14,
            borderTop:    v==='top'    ? '1px solid var(--green)' : 'none',
            borderBottom: v==='bottom' ? '1px solid var(--green)' : 'none',
            borderLeft:   h==='left'   ? '1px solid var(--green)' : 'none',
            borderRight:  h==='right'  ? '1px solid var(--green)' : 'none',
            opacity:.65,
          }} />
        ))}

        {/* LIVE / NO SIGNAL badge */}
        <div style={{
          position:'absolute', top:12, left:12,
          display:'flex', alignItems:'center', gap:5,
          background:'rgba(6,11,15,.78)', border:'1px solid var(--b-dim)', padding:'3px 8px',
        }}>
          <span className={`dot ${connected ? 'dot-r' : 'dot-d'}`} style={{ width:4, height:4 }} />
          <span style={{ fontFamily:'var(--fm)', fontSize:9, letterSpacing:'.2em', color: connected ? 'var(--t0)' : 'var(--t3)' }}>
            {connected ? 'LIVE' : 'NO SIGNAL'}
          </span>
        </div>

        {/* Resolution / cam label */}
        <div style={{
          position:'absolute', bottom:10, right:12,
          fontFamily:'var(--fm)', fontSize:9, color:'var(--t4)', letterSpacing:'.1em',
          background:'rgba(6,11,15,.65)', padding:'2px 6px',
        }}>
          CAM·01 · 800×600 · GJAKOVA
        </div>

        {/* Awaiting signal */}
        {!lastFrame && (
          <div style={{ position:'absolute', inset:0, display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', background:'var(--base)', gap:12 }}>
            <div className="spinner" />
            <span style={{ fontFamily:'var(--fm)', fontSize:10, color:'var(--t4)', letterSpacing:'.2em' }}>AWAITING SIGNAL</span>
          </div>
        )}
      </div>
    </div>
  )
}
