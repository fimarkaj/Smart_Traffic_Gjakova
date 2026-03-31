import { useState, useEffect } from 'react'
import TopBar from '../components/layout/TopBar'
import { ModuleHeader, KpiBlock, Spinner, Flash } from '../components/shared'
import { getCounts, getTotals, getSummary } from '../api'

const today = () => new Date().toISOString().split('T')[0]
const PAGE = 50
const TABS = ['COUNTS','TOTALS','DAILY SUMMARY']

export default function Database() {
  const [tab,       setTab]       = useState('COUNTS')
  const [startDate, setStartDate] = useState(today())
  const [endDate,   setEndDate]   = useState(today())
  const [counts,    setCounts]    = useState([])
  const [totals,    setTotals]    = useState(null)
  const [summary,   setSummary]   = useState([])
  const [loading,   setLoading]   = useState(false)
  const [page,      setPage]      = useState(0)
  const [flash,     setFlash]     = useState(null)

  const load = async () => {
    setLoading(true); setPage(0)
    try {
      const p = { start:`${startDate}T00:00:00`, end:`${endDate}T23:59:59` }
      const [c, t, s] = await Promise.all([getCounts(p), getTotals(p), getSummary({ start_date:startDate, end_date:endDate })])
      setCounts(c); setTotals(t); setSummary(s)
    } catch { setFlash({ msg:'Query failed', type:'error' }) }
    finally { setLoading(false) }
  }
  useEffect(() => { load() }, [])

  const paged      = counts.slice(page*PAGE, (page+1)*PAGE)
  const totalPages = Math.ceil(counts.length/PAGE)
  const iStyle     = { background:'var(--raised)', border:'1px solid var(--b-dim)', color:'var(--t0)', fontFamily:'var(--fm)', fontSize:12, padding:'7px 10px', outline:'none', colorScheme:'dark' }

  return (
    <div style={{ display:'flex', flexDirection:'column', height:'100%', overflow:'hidden' }}>
      <TopBar title="DATABASE" subtitle="RECORD INSPECTOR · NODE-01" />
      <div className="page-body">

        {flash && <Flash msg={flash.msg} type={flash.type} onClose={() => setFlash(null)} />}

        {/* Controls */}
        <div className="panel" style={{ padding:'11px 16px', display:'flex', alignItems:'flex-end', gap:14, flexWrap:'wrap' }}>
          <span className="mod-label" style={{ alignSelf:'center' }}>QUERY RANGE</span>
          {[['FROM',startDate,setStartDate],['TO',endDate,setEndDate]].map(([l,v,s]) => (
            <div key={l}>
              <p style={{ fontFamily:'var(--fm)', fontSize:9, color:'var(--t3)', letterSpacing:'.18em', marginBottom:5 }}>{l}</p>
              <input type="date" value={v} onChange={e=>s(e.target.value)} style={{ ...iStyle, width:140 }} />
            </div>
          ))}
          <button onClick={load} disabled={loading} className="btn btn-p">{loading?'QUERYING...':'EXECUTE'}</button>
          <div className="tab-bar" style={{ marginLeft:'auto' }}>
            {TABS.map(t => <button key={t} className={`tab${tab===t?' active':''}`} onClick={()=>setTab(t)}>{t}</button>)}
          </div>
        </div>

        {/* Stats strip */}
        {totals && (
          <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:8 }}>
            <KpiBlock label="Rows in Range"   value={counts.length.toLocaleString()} color="green" size="md" />
                        <KpiBlock label="Total Car-Secs"  value={totals.overall_occupancy.toLocaleString()} color="dim"  size="md" />
            <KpiBlock label="Active Zonas"    value={totals.per_roi?.filter(r=>r.total_occupancy>0).length ?? 0} color="amber" size="md" />
          </div>
        )}

        {/* Table panel */}
        <div className="panel" style={{ flex:1, overflow:'hidden', display:'flex', flexDirection:'column' }}>
          <div style={{ padding:'10px 14px', borderBottom:'1px solid var(--b-faint)', display:'flex', alignItems:'center', justifyContent:'space-between', flexShrink:0 }}>
            <span className="mod-label">
              {tab==='COUNTS'        && `RAW COUNTS · ${counts.length.toLocaleString()} ROWS`}
              {tab==='TOTALS'        && `TOTALS · ${totals?.per_roi?.length||0} ZONAS`}
              {tab==='DAILY SUMMARY' && `DAILY SUMMARY · ${summary.length} ENTRIES`}
            </span>
            {tab==='COUNTS' && totalPages>1 && (
              <div style={{ display:'flex', alignItems:'center', gap:8 }}>
                <span style={{ fontFamily:'var(--fm)', fontSize:10, color:'var(--t3)' }}>PAGE {page+1}/{totalPages}</span>
                {[['←',page>0,()=>setPage(p=>p-1)],['→',page<totalPages-1,()=>setPage(p=>p+1)]].map(([l,en,fn])=>(
                  <button key={l} onClick={fn} disabled={!en} className="btn btn-g" style={{ padding:'4px 10px', opacity:en?1:.3 }}>{l}</button>
                ))}
              </div>
            )}
          </div>

          <div style={{ flex:1, overflow:'auto' }}>
            {loading ? <Spinner /> : (
              <>
                {tab==='COUNTS' && (
                  <table className="tbl">
                    <thead><tr>
                      <th>Timestamp</th>
                      <th style={{ textAlign:'right' }}>Zona ID</th>
                      <th style={{ textAlign:'right' }}>Count</th>
                    </tr></thead>
                    <tbody>
                      {paged.length===0
                        ? <tr><td colSpan={3} style={{ textAlign:'center', padding:'3rem', color:'var(--t4)' }}>NO DATA IN RANGE</td></tr>
                        : paged.map((r,i) => (
                          <tr key={i}>
                            <td style={{ color:'var(--t3)', fontSize:11 }}>{r.ts_second}</td>
                            <td style={{ textAlign:'right', color:'var(--cyan)' }}>{r.roi_id}</td>
                            <td style={{ textAlign:'right', fontFamily:'var(--fp)', fontSize:16,
                              color: r.car_count>9?'var(--red)':r.car_count>4?'var(--amber)':'var(--green)' }}>
                              {r.car_count}
                            </td>
                          </tr>
                        ))
                      }
                    </tbody>
                  </table>
                )}

                {tab==='TOTALS' && totals && (
                  <table className="tbl">
                    <thead><tr>
                      <th>Zona</th><th style={{ textAlign:'right' }}>Zona ID</th>
                      <th style={{ textAlign:'right' }}>Crossings</th>
                      <th style={{ textAlign:'right' }}>Car-Secs</th>
                      <th style={{ textAlign:'right' }}>Share</th>
                    </tr></thead>
                    <tbody>
                      {totals.per_roi.map(r => (
                        <tr key={r.roi_id}>
                          <td style={{ color:'var(--t0)' }}>{r.name}</td>
                          <td style={{ textAlign:'right', color:'var(--cyan)' }}>{r.roi_id}</td>
                          <td style={{ textAlign:'right', fontFamily:'var(--fp)', fontSize:16, color:'var(--green)' }}>{r.total_crossings.toLocaleString()}</td>
                          <td style={{ textAlign:'right', color:'var(--t2)' }}>{r.total_occupancy.toLocaleString()}</td>
                          <td style={{ textAlign:'right', color:'var(--t3)' }}>
                            {totals.overall_crossings>0 ? `${((r.total_crossings/totals.overall_crossings)*100).toFixed(1)}%` : '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}

                {tab==='DAILY SUMMARY' && (
                  <table className="tbl">
                    <thead><tr>
                      <th>Date</th><th>Zona</th>
                                            <th style={{ textAlign:'right' }}>Peak Occ</th>
                      <th style={{ textAlign:'right' }}>Active Secs</th>
                    </tr></thead>
                    <tbody>
                      {summary.length===0
                        ? <tr><td colSpan={4} style={{ textAlign:'center', padding:'3rem', color:'var(--t4)' }}>NO SUMMARY DATA</td></tr>
                        : summary.map((r,i)=>(
                          <tr key={i}>
                            <td style={{ color:'var(--t3)' }}>{r.day_date}</td>
                            <td style={{ color:'var(--t0)' }}>{r.name}</td>
                                                        <td style={{ textAlign:'right', color:'var(--amber)' }}>{r.peak_occupancy}</td>
                            <td style={{ textAlign:'right', color:'var(--t2)' }}>{r.active_seconds}</td>
                          </tr>
                        ))
                      }
                    </tbody>
                  </table>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
