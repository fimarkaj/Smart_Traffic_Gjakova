import { useState, useEffect } from 'react'
import TopBar from '../components/layout/TopBar'
import { ModuleHeader, KpiBlock, Spinner, Flash, ChartTooltip } from '../components/shared'
import { getCounts, getTotals, getSession, getSummary, buildSummary, exportCSV } from '../api'
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'

const today = () => new Date().toISOString().split('T')[0]
const PAL = ['#34d26e','#22d3ee','#f59e0b','#f43f5e','#a78bfa','#fb923c','#2dd4bf','#e879f9']

export default function Analytics() {
  const [startDate, setStartDate] = useState(today())
  const [endDate,   setEndDate]   = useState(today())
  const [totals,    setTotals]    = useState(null)
  const [counts,    setCounts]    = useState([])
  const [session,   setSession]   = useState(null)
  const [summary,   setSummary]   = useState([])
  const [loading,   setLoading]   = useState(false)
  const [flash,     setFlash]     = useState(null)
  const [activeTab, setActiveTab] = useState('trend')

  const flash_ = (msg, type='success') => { setFlash({ msg, type }); setTimeout(()=>setFlash(null), 3500) }

  const load = async () => {
    setLoading(true)
    try {
      const p = { start:`${startDate}T00:00:00`, end:`${endDate}T23:59:59` }
      const [t, c, s, sum] = await Promise.all([getTotals(p), getCounts(p), getSession(), getSummary({ start_date:startDate, end_date:endDate })])
      setTotals(t); setCounts(c); setSession(s); setSummary(sum)
    } catch { flash_('Query failed','error') }
    finally { setLoading(false) }
  }
  useEffect(()=>{ load() },[])

  // Build occupancy chart data from raw counts
  const bySecond = {}
  counts.forEach(({ ts_second, roi_id, car_count }) => {
    if (!bySecond[ts_second]) bySecond[ts_second] = { t: ts_second }
    bySecond[ts_second][roi_id] = car_count
  })
  const chartData = Object.values(bySecond).slice(-300)

  const mainRois = totals?.per_roi || []
  const roiIds   = mainRois.map(r => r.roi_id)

  const runtime = session
    ? `${String(Math.floor(session.runtime_seconds/3600)).padStart(2,'0')}:${String(Math.floor((session.runtime_seconds%3600)/60)).padStart(2,'0')}:${String(session.runtime_seconds%60).padStart(2,'0')}`
    : '—'

  // Busiest zone by peak occupancy (more meaningful than crossing count)
  const busiestRoi = mainRois.reduce((a,b) => (b.total_occupancy > (a?.total_occupancy||0) ? b : a), null)

  const iStyle = { background:'var(--raised)', border:'1px solid var(--b-dim)', color:'var(--t0)', fontFamily:'var(--fm)', fontSize:12, padding:'7px 10px', outline:'none', colorScheme:'dark' }

  return (
    <div style={{ display:'flex', flexDirection:'column', height:'100%', overflow:'hidden' }}>
      <TopBar title="ANALYTICS" subtitle="HISTORICAL DATA · NODE-01" />
      <div className="page-body">

        {flash && <Flash msg={flash.msg} type={flash.type} onClose={()=>setFlash(null)} />}

        {/* Query bar */}
        <div className="panel" style={{ padding:'11px 16px', display:'flex', alignItems:'flex-end', gap:14, flexWrap:'wrap' }}>
          <span className="mod-label" style={{ alignSelf:'center' }}>QUERY RANGE</span>
          {[['FROM',startDate,setStartDate],['TO',endDate,setEndDate]].map(([lbl,val,set])=>(
            <div key={lbl}>
              <p style={{ fontFamily:'var(--fm)', fontSize:9, color:'var(--t3)', letterSpacing:'.18em', marginBottom:5 }}>{lbl}</p>
              <input type="date" value={val} onChange={e=>set(e.target.value)} style={{ ...iStyle, width:140 }} />
            </div>
          ))}
          <button onClick={load} disabled={loading} className="btn btn-p">{loading?'QUERYING...':'EXECUTE'}</button>
          <a href={exportCSV({ start:`${startDate}T00:00:00`, end:`${endDate}T23:59:59` })} className="btn btn-g" style={{ textDecoration:'none', display:'inline-block', padding:'7px 14px' }}>EXPORT CSV</a>
          <button onClick={async()=>{ try{ await buildSummary(today()); flash_('Summary built'); await load() }catch{ flash_('Failed','error') }}} className="btn btn-g" style={{ marginLeft:'auto' }}>BUILD TODAY</button>
        </div>

        {/* KPIs — simplified: occupancy-based only */}
        {totals && (
          <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:8 }}>
            <KpiBlock label="Active Zones"     value={`${mainRois.filter(r=>r.total_occupancy>0).length} / ${mainRois.length}`} color="green" size="md" />
            <KpiBlock label="Peak Occupancy"   value={busiestRoi?.name || '—'} sub={busiestRoi ? `peak: ${busiestRoi.total_occupancy.toLocaleString()} car-secs` : ''} color="amber" size="md" />
            <KpiBlock label="Session Runtime"  value={runtime} color="dim" size="md" />
            <KpiBlock label="Total Occupancy"  value={(totals.overall_occupancy||0).toLocaleString()} sub="summed car-seconds" color="cyan" size="md" />
          </div>
        )}

        {/* Tabs */}
        <div className="tab-bar">
          {[['trend','OCCUPANCY TREND'],['zones','ZONES'],['table','ZONA TABLE'],['summary','DAILY SUMMARY']].map(([k,l])=>(
            <button key={k} className={`tab${activeTab===k?' active':''}`} onClick={()=>setActiveTab(k)}>{l}</button>
          ))}
        </div>

        {loading && <Spinner />}

        {/* Occupancy trend */}
        {!loading && activeTab==='trend' && (
          <div className="panel" style={{ padding:14 }}>
            <ModuleHeader label="Zona Occupancy Over Time" id="CHT-01" />
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <AreaChart data={chartData} margin={{ top:4, right:0, left:-32, bottom:0 }}>
                  <defs>
                    {roiIds.map((id,i)=>(
                      <linearGradient key={id} id={`ag${i}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={PAL[i%PAL.length]} stopOpacity={.18}/>
                        <stop offset="100%" stopColor={PAL[i%PAL.length]} stopOpacity={0}/>
                      </linearGradient>
                    ))}
                  </defs>
                  <CartesianGrid strokeDasharray="1 8" stroke="rgba(52,210,110,.04)" vertical={false}/>
                  <XAxis dataKey="t" tick={{ fill:'var(--t4)', fontFamily:'var(--fm)', fontSize:9 }} axisLine={false} tickLine={false} interval="preserveStartEnd"/>
                  <YAxis tick={{ fill:'var(--t4)', fontFamily:'var(--fm)', fontSize:9 }} axisLine={false} tickLine={false} allowDecimals={false}/>
                  <Tooltip content={<ChartTooltip/>}/>
                  {roiIds.map((id,i)=>(
                    <Area key={id} type="monotone" dataKey={id} name={mainRois.find(r=>r.roi_id===id)?.name||id}
                      stroke={PAL[i%PAL.length]} strokeWidth={1.3}
                      fill={`url(#ag${i})`} dot={false} isAnimationActive={false}/>
                  ))}
                </AreaChart>
              </ResponsiveContainer>
            ) : <div style={{ padding:'3rem', textAlign:'center' }}><span style={{ fontFamily:'var(--fm)', fontSize:10, color:'var(--t4)', letterSpacing:'.18em' }}>NO DATA IN RANGE</span></div>}
          </div>
        )}

        {/* Zones bar — peak occupancy */}
        {!loading && activeTab==='zones' && (
          <div className="panel" style={{ padding:14 }}>
            <ModuleHeader label="Total Occupancy by Zone (car-seconds)" id="CHT-02" />
            {mainRois.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={mainRois} margin={{ top:4, right:0, left:-32, bottom:0 }}>
                  <CartesianGrid strokeDasharray="1 8" stroke="rgba(52,210,110,.04)" vertical={false}/>
                  <XAxis dataKey="name" tick={{ fill:'var(--t4)', fontFamily:'var(--fm)', fontSize:9 }} axisLine={false} tickLine={false}/>
                  <YAxis tick={{ fill:'var(--t4)', fontFamily:'var(--fm)', fontSize:9 }} axisLine={false} tickLine={false}/>
                  <Tooltip content={<ChartTooltip/>}/>
                  <Bar dataKey="total_occupancy" name="Car-seconds" fill="var(--green)" opacity={0.75} radius={[1,1,0,0]}/>
                </BarChart>
              </ResponsiveContainer>
            ) : <div style={{ padding:'3rem', textAlign:'center' }}><span style={{ fontFamily:'var(--fm)', fontSize:10, color:'var(--t4)', letterSpacing:'.18em' }}>NO DATA</span></div>}
          </div>
        )}

        {/* Zone table — occupancy focused */}
        {!loading && activeTab==='table' && totals && (
          <div className="panel" style={{ padding:14 }}>
            <ModuleHeader label="Zone Breakdown" id="TBL-01" />
            <div style={{ overflowX:'auto' }}>
              <table className="tbl">
                <thead><tr>
                  {['Zone','Total Occ (car-s)','Peak Count','Active Secs','Share'].map(h=>(
                    <th key={h} style={{ textAlign:h==='Zone'?'left':'right' }}>{h}</th>
                  ))}
                </tr></thead>
                <tbody>
                  {mainRois.map(r=>(
                    <tr key={r.roi_id}>
                      <td style={{ color:'var(--t0)' }}>{r.name}</td>
                      <td style={{ textAlign:'right', fontFamily:'var(--fp)', fontSize:16, color:'var(--green)' }}>{r.total_occupancy.toLocaleString()}</td>
                      <td style={{ textAlign:'right', color:'var(--amber)' }}>{r.peak_occupancy ?? '—'}</td>
                      <td style={{ textAlign:'right', color:'var(--t2)' }}>{r.active_seconds?.toLocaleString() ?? '—'}</td>
                      <td style={{ textAlign:'right', color:'var(--t3)' }}>
                        {totals.overall_occupancy > 0 ? `${((r.total_occupancy/totals.overall_occupancy)*100).toFixed(1)}%` : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Daily summary */}
        {!loading && activeTab==='summary' && (
          <div className="panel" style={{ padding:14 }}>
            <ModuleHeader label="Daily Summary" id="TBL-SUM" />
            {summary.length===0
              ? <div style={{ padding:'2rem', textAlign:'center' }}><span style={{ fontFamily:'var(--fm)', fontSize:10, color:'var(--t4)', letterSpacing:'.18em' }}>NO SUMMARIES — USE BUILD TODAY</span></div>
              : <table className="tbl">
                  <thead><tr>
                    {['Date','Zone','Peak Occ','Active Secs'].map(h=>(
                      <th key={h} style={{ textAlign:h==='Date'||h==='Zone'?'left':'right' }}>{h}</th>
                    ))}
                  </tr></thead>
                  <tbody>
                    {summary.map((r,i)=>(
                      <tr key={i}>
                        <td style={{ color:'var(--t3)' }}>{r.day_date}</td>
                        <td style={{ color:'var(--t0)' }}>{r.name}</td>
                        <td style={{ textAlign:'right', color:'var(--amber)' }}>{r.peak_occupancy}</td>
                        <td style={{ textAlign:'right', color:'var(--t2)' }}>{r.active_seconds}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
            }
          </div>
        )}
      </div>
    </div>
  )
}
