import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store'
import { login } from '../api'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error,    setError]    = useState('')
  const [loading,  setLoading]  = useState(false)
  const doLogin  = useAuthStore((s) => s.login)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(''); setLoading(true)
    try {
      const data = await login(username, password)
      doLogin(data.access_token, username)
      navigate('/')
    } catch {
      setError('ACCESS DENIED — INVALID CREDENTIALS')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight:'100vh', background:'var(--void)',
      display:'flex', alignItems:'center', justifyContent:'center',
      position:'relative', overflow:'hidden',
    }}>
      {/* Background grid */}
      <div style={{
        position:'absolute', inset:0, pointerEvents:'none',
        backgroundImage:'linear-gradient(rgba(52,210,110,.025) 1px,transparent 1px),linear-gradient(90deg,rgba(52,210,110,.025) 1px,transparent 1px)',
        backgroundSize:'52px 52px',
      }} />
      <div style={{
        position:'absolute', top:'50%', left:'50%', transform:'translate(-50%,-50%)',
        width:500, height:500, pointerEvents:'none',
        background:'radial-gradient(circle,rgba(52,210,110,.04) 0%,transparent 70%)',
      }} />

      <div className="fadein" style={{ width:340, padding:'0 20px', position:'relative', zIndex:1 }}>
        {/* Header */}
        <div style={{ textAlign:'center', marginBottom:44 }}>
          <div style={{
            fontFamily:'var(--fp)', fontSize:30, color:'var(--green)',
            textShadow:'0 0 10px rgba(52,210,110,.5)',
            letterSpacing:'.1em', lineHeight:1, marginBottom:8, userSelect:'none',
          }}>
            SMARTTRAFFIC AI
          </div>
          <p style={{ fontFamily:'var(--fm)', fontSize:9, color:'var(--t4)', letterSpacing:'.3em' }}>
            OPERATIONS TERMINAL · v2.0
          </p>
          <div style={{ width:40, height:1, background:'var(--green)', margin:'14px auto 0', boxShadow:'0 0 6px var(--green)' }} />
        </div>

        <form onSubmit={handleSubmit} style={{ display:'flex', flexDirection:'column', gap:13 }}>
          {[
            { label:'OPERATOR ID', key:'username', value:username, set:setUsername, type:'text' },
            { label:'ACCESS CODE', key:'password', value:password, set:setPassword, type:'password' },
          ].map(({ label, key, value, set, type }) => (
            <div key={key}>
              <p style={{ fontFamily:'var(--fm)', fontSize:9, color:'var(--t2)', letterSpacing:'.18em', marginBottom:5 }}>{label}</p>
              <input
                type={type} value={value}
                onChange={(e) => set(e.target.value)}
                autoComplete={key}
                className="inp"
                style={{ fontSize:13 }}
              />
            </div>
          ))}

          {error && (
            <div style={{
              fontFamily:'var(--fm)', fontSize:11, color:'var(--red)',
              padding:'9px 11px', background:'var(--red-lo)',
              border:'1px solid rgba(244,63,94,.22)', letterSpacing:'.05em',
            }}>
              ⚠ {error}
            </div>
          )}

          <button type="submit" disabled={loading} className="btn btn-p" style={{ marginTop:6, padding:11, fontSize:12 }}>
            {loading ? 'AUTHENTICATING...' : 'INITIALIZE SESSION'}
          </button>
        </form>

        <p style={{ fontFamily:'var(--fm)', fontSize:9, color:'var(--t4)', textAlign:'center', marginTop:22, letterSpacing:'.1em' }}>
          UNAUTHORIZED ACCESS IS PROHIBITED
        </p>
      </div>
    </div>
  )
}
