import { useEffect, useMemo, useState } from 'react'
import TopBar from '../components/layout/TopBar'
import { ModuleHeader, KpiBlock } from '../components/shared'
import { useLiveStore } from '../store'
import { getForecastHistory, getForecastLive, getForecastStatus } from '../api'
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

const trendColor = { HIGH: 'var(--red)', MEDIUM: 'var(--amber)', LOW: 'var(--green)' }
const trendLabel = { HIGH: 'HEAVY', MEDIUM: 'MODERATE', LOW: 'LOW' }
const scoreMap = { LOW: 1, MEDIUM: 2, HIGH: 3 }

function ConfBar({ label, value, color }) {
  return (
    <div style={{ marginBottom: 6 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
        <span style={{ fontFamily: 'var(--fm)', fontSize: 10, color: 'var(--t2)' }}>{label}</span>
        <span style={{ fontFamily: 'var(--fp)', fontSize: 14, color }}>{Math.round((value || 0) * 100)}%</span>
      </div>
      <div className="bar">
        <div className="bar-fill" style={{ width: `${(value || 0) * 100}%`, background: color }} />
      </div>
    </div>
  )
}

export default function Forecast() {
  const [forecast, setForecast] = useState(null)
  const [status, setStatus] = useState(null)
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const roiCounts = useLiveStore((s) => s.roiCounts)
  const connected = useLiveStore((s) => s.connected)

  const load = async () => {
    try {
      const [f, s, h] = await Promise.all([getForecastLive(), getForecastStatus(), getForecastHistory()])
      setForecast(f)
      setStatus(s)
      setHistory(h?.items || [])
    } catch {
      setForecast(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    const id = setInterval(load, 2000)
    return () => clearInterval(id)
  }, [])

  const pred = forecast?.prediction
  const conf = forecast?.confidence || {}
  const maxConf = forecast?.max_conf || 0
  const ready = forecast?.ready === true
  const modelExists = status?.model_file_exists

  const chartData = useMemo(() => (history || []).map((item, index) => ({
    idx: index + 1,
    score: scoreMap[item.prediction] || null,
    conf: item.max_conf != null ? Math.round(item.max_conf * 100) : null,
    label: trendLabel[item.prediction] || item.prediction || '—',
    time: item.timestamp?.slice(11, 19) || '—',
  })), [history])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      <TopBar title="TRAFFIC FORECAST" subtitle="" />
      <div className="page-body">
        <div className="panel" style={{ padding: '11px 16px', display: 'flex', alignItems: 'center', gap: 20, flexWrap: 'wrap' }}>
          <span className="mod-label">Model Status</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span className={`dot ${ready ? 'dot-g' : modelExists ? 'dot-a' : 'dot-r'}`} />
            <span style={{ fontFamily: 'var(--fm)', fontSize: 12, color: ready ? 'var(--green)' : modelExists ? 'var(--amber)' : 'var(--red)' }}>
              {ready ? 'MODEL ACTIVE — LIVE PREDICTIONS RUNNING' : modelExists ? 'MODEL FILE FOUND — LOADING...' : 'NO SKLEARN MODEL FOUND'}
            </span>
          </div>
          <div style={{ marginLeft: 'auto', display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {[
              { k: 'ALGORITHM', v: status?.algorithm || 'Sklearn model' },
              { k: 'SOURCE', v: status?.upload_supported ? 'fixed config path' : 'fixed config path' },
              { k: 'CLASSES', v: (status?.classes || []).join(' / ') || 'LOW / MEDIUM / HIGH' },
            ].map(({ k, v }) => (
              <div key={k} style={{ background: 'var(--raised)', border: '1px solid var(--b-faint)', padding: '6px 12px' }}>
                <p style={{ fontFamily: 'var(--fm)', fontSize: 9, color: 'var(--t4)', letterSpacing: '.15em', marginBottom: 3 }}>{k}</p>
                <p style={{ fontFamily: 'var(--fm)', fontSize: 11, color: 'var(--t2)' }}>{v}</p>
              </div>
            ))}
          </div>
        </div>

        {!ready && (
          <div className="panel" style={{ padding: '2.5rem', textAlign: 'center' }}>
            <p style={{ fontFamily: 'var(--fm)', fontSize: 11, color: 'var(--t4)', letterSpacing: '.18em', marginBottom: 12 }}>
              {!modelExists ? 'MODEL NOT FOUND YET' : 'AWAITING FIRST PREDICTION...'}
            </p>
            <div style={{ background: 'var(--raised)', border: '1px solid var(--amber)', borderLeft: '3px solid var(--amber)', padding: '12px 16px', maxWidth: 620, margin: '0 auto', textAlign: 'left' }}>
              <p style={{ fontFamily: 'var(--fm)', fontSize: 12, color: 'var(--t2)', lineHeight: 1.8 }}>
                Default path: <code style={{ color: 'var(--cyan)' }}>{status?.model_path || 'training/out/traffic_congestion_model.pkl'}</code>
              </p>
              <p style={{ fontFamily: 'var(--fm)', fontSize: 11, color: 'var(--t3)', marginTop: 8 }}>
                Backend loads the trained sklearn model from the fixed path in config.yaml and auto-reloads it when the file changes.
              </p>
            </div>
          </div>
        )}

        {ready && pred && (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 8 }}>
              <KpiBlock label="Predicted Congestion" value={trendLabel[pred]} sub="live sklearn output" color={pred === 'HIGH' ? 'red' : pred === 'MEDIUM' ? 'amber' : 'green'} size="lg" />
              <KpiBlock label="Confidence" value={`${Math.round(maxConf * 100)}%`} color="cyan" size="lg" />
              <KpiBlock label="Vehicles Now" value={forecast.total_cars ?? '—'} color="dim" size="lg" />
              <KpiBlock label="Stream" value={connected ? 'LIVE' : 'OFFLINE'} color={connected ? 'green' : 'red'} size="lg" />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: 12 }}>
              <div className="panel" style={{ padding: 16 }}>
                <ModuleHeader label="Recent Prediction Trend" id="FCST-LIVE" />
                {chartData.length > 1 ? (
                  <ResponsiveContainer width="100%" height={220}>
                    <LineChart data={chartData} margin={{ top: 4, right: 8, left: -28, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="1 8" stroke="rgba(52,210,110,.04)" vertical={false} />
                      <XAxis dataKey="time" tick={{ fill:'var(--t4)', fontFamily:'var(--fm)', fontSize:9 }} axisLine={false} tickLine={false} minTickGap={24} />
                      <YAxis domain={[1,3]} ticks={[1,2,3]} tickFormatter={(v) => ({1:'LOW',2:'MED',3:'HIGH'}[v] || v)} tick={{ fill:'var(--t4)', fontFamily:'var(--fm)', fontSize:9 }} axisLine={false} tickLine={false} />
                      <Tooltip formatter={(value, name, props) => name === 'score' ? props.payload.label : `${value}%`} labelFormatter={(label, rows) => rows?.[0]?.payload?.time || label} />
                      <Line type="monotone" dataKey="score" stroke="var(--cyan)" strokeWidth={2} dot={false} isAnimationActive={false} />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <div style={{ padding: '2rem', textAlign: 'center' }}><span style={{ fontFamily:'var(--fm)', fontSize:10, color:'var(--t4)', letterSpacing:'.18em' }}>BUILDING TREND…</span></div>
                )}
              </div>

              <div className="panel" style={{ padding: 16 }}>
                <ModuleHeader label="Class Probabilities" id="FCST-CONF" />
                <ConfBar label="LOW" value={conf.LOW} color="var(--green)" />
                <ConfBar label="MEDIUM" value={conf.MEDIUM} color="var(--amber)" />
                <ConfBar label="HIGH" value={conf.HIGH} color="var(--red)" />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <div className="panel" style={{ padding: 16 }}>
                <ModuleHeader label="Current Zona Input" id="FCST-ZONES" />
                {Object.keys(roiCounts).length === 0 ? (
                  <div style={{ padding: '1.5rem', textAlign: 'center' }}>
                    <span style={{ fontFamily: 'var(--fm)', fontSize: 10, color: 'var(--t4)', letterSpacing: '.18em' }}>AWAITING STREAM</span>
                  </div>
                ) : Object.entries(roiCounts).map(([name, count]) => {
                  const color = count <= 4 ? 'var(--green)' : count <= 9 ? 'var(--amber)' : 'var(--red)'
                  const pct = Math.min((count / 15) * 100, 100)
                  return (
                    <div key={name} className="roi-row">
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 5 }}>
                        <span style={{ fontFamily: 'var(--fm)', fontSize: 12, color: 'var(--t1)' }}>{name}</span>
                        <span style={{ fontFamily: 'var(--fp)', fontSize: 20, color }}>{count}</span>
                      </div>
                      <div className="bar">
                        <div className="bar-fill" style={{ width: `${pct}%`, background: color }} />
                      </div>
                    </div>
                  )
                })}
              </div>

              <div className="panel" style={{ padding: 16 }}>
                <ModuleHeader label="Prediction Details" id="FCST-DETAIL" />
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8 }}>
                  {[
                    { k: 'PREDICTION', v: trendLabel[pred], color: trendColor[pred] },
                    { k: 'CONFIDENCE', v: `${Math.round(maxConf * 100)}%`, color: 'var(--cyan)' },
                    { k: 'TIMESTAMP', v: forecast.timestamp?.slice(11, 19) || '—', color: 'var(--t2)' },
                    { k: 'FEATURES', v: status?.feature_count ?? '—', color: 'var(--t1)' },
                  ].map(({ k, v, color }) => (
                    <div key={k} style={{ background: 'var(--raised)', border: '1px solid var(--b-faint)', padding: '10px 12px' }}>
                      <p style={{ fontFamily: 'var(--fm)', fontSize: 9, color: 'var(--t4)', letterSpacing: '.15em', marginBottom: 5 }}>{k}</p>
                      <p style={{ fontFamily: 'var(--fp)', fontSize: 22, color }}>{v}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
