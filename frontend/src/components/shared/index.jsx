// ── Shared primitive components ───────────────────────

export function ModuleHeader({ label, id, right }) {
  return (
    <div className="mod-head">
      <span className="mod-label">{label}</span>
      <div style={{ display:'flex', alignItems:'center', gap:10 }}>
        {right}
        {id && <span className="mod-id">MOD·{id}</span>}
      </div>
    </div>
  )
}

// color: 'green' | 'cyan' | 'amber' | 'red' | 'dim'
export function KpiBlock({ label, value, sub, color = 'green', size = 'lg' }) {
  const sz = { lg:'2.2rem', md:'1.75rem', sm:'1.35rem' }
  const col = {
    green:'var(--green)', cyan:'var(--cyan)',
    amber:'var(--amber)', red:'var(--red)', dim:'var(--t2)',
  }
  const c = col[color] || col.green
  return (
    <div className={`kpi-block c-${color}`}>
      <p className="kpi-lbl">{label}</p>
      <p style={{
        fontFamily:'var(--fp)', fontSize: sz[size] || sz.lg,
        lineHeight:1, color: c,
        textShadow: `0 0 8px ${c}55`,
        letterSpacing:'.04em',
      }}>
        {value ?? '—'}
      </p>
      {sub && <p className="kpi-sub">{sub}</p>}
    </div>
  )
}

export function StatusTag({ status }) {
  const map = {
    ok:'tag-g',online:'tag-g',live:'tag-g',low:'tag-g',
    moderate:'tag-a',warning:'tag-a',rising:'tag-a',
    heavy:'tag-r',offline:'tag-r',error:'tag-r',
    stable:'tag-d',falling:'tag-c',info:'tag-c',
    placeholder:'tag-d',pending:'tag-d',
  }
  const cls = map[status] || 'tag-d'
  const lbl = status?.toUpperCase() || '—'
  return <span className={`tag ${cls}`}>{lbl}</span>
}

export function BarRow({ label, value, max, color = 'var(--green)', right }) {
  const pct = Math.round((value / Math.max(max, 1)) * 100)
  return (
    <div className="roi-row">
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:6 }}>
        <span style={{ fontFamily:'var(--fm)', fontSize:13, color:'var(--t1)' }}>{label}</span>
        <div style={{ display:'flex', alignItems:'center', gap:8 }}>
          {right}
          <span style={{ fontFamily:'var(--fp)', fontSize:22, color, textShadow:`0 0 5px ${color}80` }}>{value}</span>
        </div>
      </div>
      <div className="bar">
        <div className="bar-fill" style={{ width:`${pct}%`, background:color }} />
      </div>
    </div>
  )
}

// Tiny inline SVG sparkline — no recharts
export function Sparkline({ data = [], width = 80, height = 28, color = 'var(--green)' }) {
  if (data.length < 2) return null
  const max = Math.max(...data, 1)
  const min = Math.min(...data, 0)
  const range = max - min || 1
  const pad = 2
  const W = width - pad * 2
  const H = height - pad * 2
  const pts = data.map((v, i) => [
    pad + (i / (data.length - 1)) * W,
    pad + H - ((v - min) / range) * H,
  ])
  const line = pts.map((p, i) => `${i===0?'M':'L'}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' ')
  const fill = line + ` L${pts[pts.length-1][0].toFixed(1)},${(pad+H).toFixed(1)} L${pad},${(pad+H).toFixed(1)} Z`
  return (
    <svg width={width} height={height} style={{ overflow:'visible', display:'inline-block', verticalAlign:'middle' }}>
      <path d={fill} fill={color} opacity={.13} />
      <path d={line} fill="none" stroke={color} strokeWidth={1.3} opacity={.85} />
      <circle cx={pts[pts.length-1][0]} cy={pts[pts.length-1][1]} r={2.5} fill={color} opacity={.9} />
    </svg>
  )
}

export function Spinner() {
  return (
    <div style={{ display:'flex', alignItems:'center', justifyContent:'center', padding:'2.5rem' }}>
      <div className="spinner" />
    </div>
  )
}

export function EmptyState({ label }) {
  return (
    <div style={{ padding:'2.5rem', textAlign:'center' }}>
      <span style={{ fontFamily:'var(--fm)', fontSize:11, color:'var(--t4)', letterSpacing:'.2em', textTransform:'uppercase' }}>
        {label}
      </span>
    </div>
  )
}

export function Flash({ msg, type = 'success', onClose }) {
  if (!msg) return null
  const c = type === 'error' ? 'var(--red)' : type === 'warning' ? 'var(--amber)' : 'var(--green)'
  const bg = type === 'error' ? 'var(--red-lo)' : type === 'warning' ? 'var(--amber-lo)' : 'var(--green-lo)'
  return (
    <div style={{
      padding:'10px 14px', background:bg, border:`1px solid ${c}40`,
      display:'flex', alignItems:'center', justifyContent:'space-between', gap:12,
    }}>
      <span style={{ fontFamily:'var(--fm)', fontSize:12, color:c, letterSpacing:'.04em' }}>{msg}</span>
      {onClose && <button onClick={onClose} style={{ background:'none', border:'none', cursor:'pointer', color:c, fontSize:14 }}>✕</button>}
    </div>
  )
}

// Recharts custom tooltip
export function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div style={{ background:'var(--panel)', border:'1px solid var(--b-mid)', padding:'8px 12px', minWidth:100 }}>
      <p style={{ fontFamily:'var(--fm)', fontSize:9, color:'var(--t3)', marginBottom:5, letterSpacing:'.1em' }}>{label}</p>
      {payload.map((p) => (
        <div key={p.dataKey} style={{ display:'flex', gap:7, alignItems:'center', marginBottom:2 }}>
          <span style={{ width:6, height:6, background:p.color, display:'inline-block', flexShrink:0 }} />
          <span style={{ fontFamily:'var(--fm)', fontSize:10, color:'var(--t2)' }}>{p.name ?? p.dataKey}</span>
          <span style={{ fontFamily:'var(--fp)', fontSize:16, color:p.color }}>{p.value}</span>
        </div>
      ))}
    </div>
  )
}
