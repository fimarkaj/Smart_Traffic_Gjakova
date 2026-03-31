import { useState, useEffect } from 'react'
import TopBar from '../components/layout/TopBar'
import { ModuleHeader, Spinner, Flash } from '../components/shared'
import { getClips, deleteClip, getClipUrl } from '../api'
import { Film, Play, Trash2 } from 'lucide-react'

export default function Clips() {
  const [clips,   setClips]   = useState([])
  const [playing, setPlaying] = useState(null)
  const [loading, setLoading] = useState(true)
  const [flash,   setFlash]   = useState(null)

  const load = async () => {
    setLoading(true)
    try { setClips(await getClips()) }
    catch { setFlash({ msg:'Failed to load clips', type:'error' }) }
    finally { setLoading(false) }
  }
  useEffect(() => { load() }, [])

  const handleDelete = async (filename) => {
    if (!confirm(`Delete ${filename}?`)) return
    try {
      await deleteClip(filename)
      setClips(c => c.filter(x => x.filename !== filename))
      if (playing === filename) setPlaying(null)
      setFlash({ msg:`Deleted ${filename}`, type:'success' })
    } catch { setFlash({ msg:'Delete failed', type:'error' }) }
  }

  return (
    <div style={{ display:'flex', flexDirection:'column', height:'100%', overflow:'hidden' }}>
      <TopBar title="CLIPS" subtitle="INCIDENT RECORDING ARCHIVE" />
      <div className="page-body">
        {flash && <Flash msg={flash.msg} type={flash.type} onClose={() => setFlash(null)} />}

        {/* Video player */}
        {playing && (
          <div className="panel" style={{ padding:12 }}>
            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:10 }}>
              <span className="mod-label">PLAYBACK: {playing}</span>
              <button onClick={() => setPlaying(null)} className="btn btn-g">CLOSE</button>
            </div>
            <video src={getClipUrl(playing)} controls autoPlay style={{ width:'100%', background:'#000', display:'block' }} />
          </div>
        )}

        <div className="panel" style={{ padding:14 }}>
          <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:14 }}>
            <ModuleHeader label={`Recording Index · ${clips.length} files`} id="CLIPS-01" />
            <button onClick={load} className="btn btn-g">REFRESH</button>
          </div>

          {loading ? <Spinner /> : clips.length === 0 ? (
            <div style={{ padding:'4rem', display:'flex', flexDirection:'column', alignItems:'center', gap:10 }}>
              <Film size={32} style={{ color:'var(--t4)', opacity:.35 }} />
              <span style={{ fontFamily:'var(--fm)', fontSize:10, color:'var(--t4)', letterSpacing:'.2em' }}>NO CLIPS RECORDED</span>
              <span style={{ fontFamily:'var(--fm)', fontSize:11, color:'var(--t4)', maxWidth:320, textAlign:'center', lineHeight:1.7 }}>
                Clips are saved automatically when occupancy or crossing thresholds are exceeded.
              </span>
            </div>
          ) : (
            <div style={{ display:'flex', flexDirection:'column', gap:3 }}>
              {clips.map(clip => (
                <div key={clip.filename} style={{
                  display:'flex', alignItems:'center', gap:12, padding:'10px 12px',
                  background:'var(--raised)', border:'1px solid var(--b-faint)',
                  transition:'border-color .15s',
                }}
                  onMouseEnter={e => e.currentTarget.style.borderColor='var(--b-dim)'}
                  onMouseLeave={e => e.currentTarget.style.borderColor='var(--b-faint)'}
                >
                  <Film size={13} style={{ color:'var(--green)', flexShrink:0, opacity:.7 }} />
                  <div style={{ flex:1, minWidth:0 }}>
                    <p style={{ fontFamily:'var(--fm)', fontSize:12, color:'var(--t1)', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{clip.filename}</p>
                    <p style={{ fontFamily:'var(--fm)', fontSize:10, color:'var(--t3)', marginTop:2 }}>
                      {clip.created_at?.slice(0,19).replace('T',' ')} · {clip.size_mb} MB
                    </p>
                  </div>
                  <div style={{ display:'flex', gap:5, flexShrink:0 }}>
                    <button onClick={() => setPlaying(clip.filename)} className="btn btn-p" style={{ padding:'5px 10px', display:'flex', alignItems:'center', gap:4 }}>
                      <Play size={10} /> PLAY
                    </button>
                    <button onClick={() => handleDelete(clip.filename)} className="btn btn-d" style={{ padding:'5px 9px' }}>
                      <Trash2 size={11} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
