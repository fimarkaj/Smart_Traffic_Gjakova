import { useLiveStore } from '../../store'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { ChartTooltip } from '../shared'

const PAL = ['#34d26e','#22d3ee','#f59e0b','#f43f5e','#a78bfa','#fb923c','#2dd4bf','#e879f9']

export default function LiveChart() {
  const history   = useLiveStore((s) => s.history)
  const roiCounts = useLiveStore((s) => s.roiCounts)
  const names     = Object.keys(roiCounts)

  if (!history.length) {
    return (
      <div style={{ height:160, display:'flex', alignItems:'center', justifyContent:'center' }}>
        <span style={{ fontFamily:'var(--fm)', fontSize:10, color:'var(--t4)', letterSpacing:'.2em' }}>COLLECTING DATA...</span>
      </div>
    )
  }

  const data = history.map((h) => ({
    t: new Date(h.ts * 1000).toLocaleTimeString('en-GB', { hour12:false }),
    ...Object.fromEntries(names.map((n) => [n, h[n] ?? 0])),
  }))

  return (
    <ResponsiveContainer width="100%" height={160}>
      <AreaChart data={data} margin={{ top:4, right:0, left:-32, bottom:0 }}>
        <defs>
          {names.map((n, i) => (
            <linearGradient key={n} id={`lg${i}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%"   stopColor={PAL[i%PAL.length]} stopOpacity={.20} />
              <stop offset="100%" stopColor={PAL[i%PAL.length]} stopOpacity={0}   />
            </linearGradient>
          ))}
        </defs>
        <CartesianGrid strokeDasharray="1 8" stroke="rgba(52,210,110,0.05)" vertical={false} />
        <XAxis dataKey="t" tick={{ fill:'var(--t4)', fontFamily:'var(--fm)', fontSize:9 }} axisLine={false} tickLine={false} interval="preserveStartEnd" />
        <YAxis tick={{ fill:'var(--t4)', fontFamily:'var(--fm)', fontSize:9 }} axisLine={false} tickLine={false} allowDecimals={false} />
        <Tooltip content={<ChartTooltip />} />
        {names.map((n, i) => (
          <Area key={n} type="monotone" dataKey={n}
            stroke={PAL[i%PAL.length]} strokeWidth={1.3}
            fill={`url(#lg${i})`} dot={false} isAnimationActive={false} />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  )
}
