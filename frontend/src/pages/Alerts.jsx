import { useState, useEffect } from 'react'
import TopBar from '../components/layout/TopBar'
import { ModuleHeader, KpiBlock, Spinner, Flash } from '../components/shared'
import { getAlerts, createAlert, updateAlert, deleteAlert } from '../api'
import { Bell, Plus, Edit2, Trash2, AlertTriangle, Info } from 'lucide-react'

const METRICS   = ['occupancy','crossings_total','global_unique']
const OPERATORS = ['>','>=','<','<=','==']
const CHANNELS  = ['email','telegram','webhook']
const emptyRule = () => ({ name:'', roi_id:'', metric:'occupancy', operator:'>', threshold:10, duration_seconds:0, channels:[], enabled:true })

function icon(severity) {
  if (severity === 'warning' || severity === 'error') return <AlertTriangle size={15} style={{ color: severity==='error'?'var(--red)':'var(--amber)', flexShrink:0 }} />
  return <Info size={15} style={{ color:'var(--cyan)', flexShrink:0 }} />
}

export default function Alerts() {
  const [rules,   setRules]   = useState([])
  const [editing, setEditing] = useState(null)
  const [saving,  setSaving]  = useState(false)
  const [loading, setLoading] = useState(true)
  const [flash,   setFlash]   = useState(null)

  const flash_ = (msg, type='success') => { setFlash({ msg, type }); setTimeout(()=>setFlash(null), 3500) }

  const load = async () => {
    setLoading(true)
    try { setRules(await getAlerts()) }
    catch { flash_('Failed to load rules','error') }
    finally { setLoading(false) }
  }
  useEffect(() => { load() }, [])

  const handleSave = async () => {
    if (!editing.name) return flash_('Rule name is required','warning')
    setSaving(true)
    try {
      editing.id ? await updateAlert(editing.id, editing) : await createAlert(editing)
      flash_('Rule saved')
      setEditing(null); await load()
    } catch { flash_('Save failed','error') }
    finally { setSaving(false) }
  }

  const toggleCh = (ch) => setEditing(e => ({
    ...e, channels: e.channels.includes(ch) ? e.channels.filter(c=>c!==ch) : [...e.channels, ch]
  }))

  const iStyle = { background:'var(--raised)', border:'1px solid var(--b-dim)', color:'var(--t0)', fontFamily:'var(--fm)', fontSize:12, padding:'7px 10px', outline:'none', width:'100%' }

  return (
    <div style={{ display:'flex', flexDirection:'column', height:'100%', overflow:'hidden' }}>
      <TopBar title="ALERTS" subtitle="RULE ENGINE · SYSTEM NOTIFICATIONS" />
      <div className="page-body">
        {flash && <Flash msg={flash.msg} type={flash.type} onClose={()=>setFlash(null)} />}

        {/* KPIs */}
        <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:8 }}>
          <KpiBlock label="Active Rules"  value={rules.filter(r=>r.enabled).length} color="green" size="md" />
          <KpiBlock label="Total Rules"   value={rules.length}                       color="dim"   size="md" />
          <KpiBlock label="System Status" value="NOMINAL"                            color="green" size="md" />
          <KpiBlock label="Model Status"  value="RUNNING"                            color="cyan"  size="md" />
        </div>

        {/* Rule editor */}
        {editing && (
          <div className="panel" style={{ padding:14, borderColor:'var(--b-mid)' }}>
            <ModuleHeader label={editing.id ? 'Edit Rule' : 'New Rule'} id="RULE-EDIT" />
            <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:10, marginBottom:12 }}>
              {[
                { label:'RULE NAME', el:<input value={editing.name} onChange={e=>setEditing({...editing,name:e.target.value})} style={iStyle} placeholder="e.g. High congestion" /> },
                { label:'Zona ID (blank = all)', el:<input value={editing.roi_id} onChange={e=>setEditing({...editing,roi_id:e.target.value})} style={iStyle} placeholder="e.g. 4" /> },
                { label:'METRIC', el:<select value={editing.metric} onChange={e=>setEditing({...editing,metric:e.target.value})} style={{ ...iStyle, colorScheme:'dark' }}>{METRICS.map(m=><option key={m}>{m}</option>)}</select> },
                { label:'OPERATOR', el:<select value={editing.operator} onChange={e=>setEditing({...editing,operator:e.target.value})} style={{ ...iStyle, colorScheme:'dark' }}>{OPERATORS.map(o=><option key={o}>{o}</option>)}</select> },
                { label:'THRESHOLD', el:<input type="number" value={editing.threshold} onChange={e=>setEditing({...editing,threshold:Number(e.target.value)})} style={iStyle} /> },
                { label:'DURATION (secs)', el:<input type="number" value={editing.duration_seconds} onChange={e=>setEditing({...editing,duration_seconds:Number(e.target.value)})} style={iStyle} /> },
              ].map(({ label, el }) => (
                <div key={label}>
                  <p style={{ fontFamily:'var(--fm)', fontSize:9, color:'var(--t3)', letterSpacing:'.18em', marginBottom:5 }}>{label}</p>
                  {el}
                </div>
              ))}
            </div>

            {/* Channels */}
            <div style={{ marginBottom:14 }}>
              <p style={{ fontFamily:'var(--fm)', fontSize:9, color:'var(--t3)', letterSpacing:'.18em', marginBottom:8 }}>CHANNELS</p>
              <div style={{ display:'flex', gap:6 }}>
                {CHANNELS.map(ch => (
                  <button key={ch} onClick={()=>toggleCh(ch)} style={{
                    background: editing.channels.includes(ch)?'var(--green-lo)':'transparent',
                    border: `1px solid ${editing.channels.includes(ch)?'var(--b-mid)':'var(--b-faint)'}`,
                    color: editing.channels.includes(ch)?'var(--green)':'var(--t3)',
                    fontFamily:'var(--fm)', fontSize:10, letterSpacing:'.12em',
                    padding:'5px 14px', cursor:'pointer', transition:'all .15s',
                  }}>{ch.toUpperCase()}</button>
                ))}
              </div>
            </div>

            <div style={{ display:'flex', gap:8 }}>
              <button onClick={handleSave} disabled={saving} className="btn btn-p">{saving?'SAVING...':'SAVE RULE'}</button>
              <button onClick={()=>setEditing(null)} className="btn btn-g">CANCEL</button>
            </div>
          </div>
        )}

        <div style={{ display:'grid', gridTemplateColumns:'1fr 320px', gap:12 }}>

          {/* Rules list */}
          <div className="panel" style={{ padding:14 }}>
            <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:14 }}>
              <span className="mod-label">Alert Rules · {rules.length}</span>
              <button onClick={()=>setEditing(emptyRule())} className="btn btn-p" style={{ padding:'6px 12px', display:'flex', alignItems:'center', gap:5 }}>
                <Plus size={11} /> NEW RULE
              </button>
            </div>

            {loading ? <Spinner /> : rules.length===0 ? (
              <div style={{ padding:'3rem', display:'flex', flexDirection:'column', alignItems:'center', gap:10 }}>
                <Bell size={28} style={{ color:'var(--t4)', opacity:.35 }} />
                <span style={{ fontFamily:'var(--fm)', fontSize:10, color:'var(--t4)', letterSpacing:'.2em' }}>NO RULES CONFIGURED</span>
              </div>
            ) : (
              <div style={{ display:'flex', flexDirection:'column', gap:3 }}>
                {rules.map(rule => (
                  <div key={rule.id} className="alert-item" style={{ opacity:rule.enabled?1:.5 }}>
                    <span className={`dot ${rule.enabled?'dot-g':'dot-d'}`} style={{ marginTop:3 }} />
                    <div style={{ flex:1, minWidth:0 }}>
                      <p style={{ fontFamily:'var(--fm)', fontSize:12, color:'var(--t0)', marginBottom:4 }}>{rule.name}</p>
                      <p style={{ fontFamily:'var(--fm)', fontSize:10, color:'var(--t3)' }}>
                        {rule.metric} {rule.operator} {rule.threshold}
                        {rule.roi_id ? ` · Zona ${rule.roi_id}` : ' · ALL ZONAS'}
                        {rule.duration_seconds>0 ? ` · ${rule.duration_seconds}s sustained` : ''}
                      </p>
                    </div>
                    <div style={{ display:'flex', gap:5 }}>
                      <button onClick={()=>setEditing({...rule,channels:JSON.parse(rule.channels||'[]')})} className="btn btn-g" style={{ padding:'5px 9px' }}><Edit2 size={11}/></button>
                      <button onClick={()=>deleteAlert(rule.id).then(()=>{flash_('Rule deleted');load()})} className="btn btn-d" style={{ padding:'5px 9px' }}><Trash2 size={11}/></button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* System status panel */}
          <div className="panel" style={{ padding:14 }}>
            <ModuleHeader label="System Status" id="SYS-01" />
            {[
              { label:'Stream',        dotCls:'dot-g', detail:'HLS · live'      },
              { label:'Database',      dotCls:'dot-g', detail:'SQLite · healthy' },
              { label:'Detector',      dotCls:'dot-g', detail:'YOLOv11 · active' },
              { label:'API',           dotCls:'dot-g', detail:'FastAPI · :8000'  },
              { label:'Webhook',       dotCls:'dot-g', detail:'Discord · enabled'  },
            ].map(({ label, dotCls, detail }) => (
              <div key={label} className="meta-row">
                <div style={{ display:'flex', alignItems:'center', gap:8 }}>
                  <span className={`dot ${dotCls}`} />
                  <span style={{ fontFamily:'var(--fm)', fontSize:12, color:'var(--t1)' }}>{label}</span>
                </div>
                <span style={{ fontFamily:'var(--fm)', fontSize:10, color:'var(--t3)' }}>{detail}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
