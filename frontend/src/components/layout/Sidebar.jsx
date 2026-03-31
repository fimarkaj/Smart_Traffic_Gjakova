import { NavLink } from 'react-router-dom'
import { useAuthStore } from '../../store'
import { Activity, BarChart2, Database, Camera, Bell, Film, LogOut } from 'lucide-react'

const NAV = [
  { to:'/',          icon:Activity,   label:'LIVE'   },
  { to:'/analytics', icon:BarChart2,  label:'ANLT'   },
  { to:'/database',  icon:Database,   label:'DB'     },
  { to:'/clips',     icon:Film,       label:'CLIPS'  },
  { to:'/camera',    icon:Camera,     label:'CAM'    },
  { to:'/alerts',    icon:Bell,       label:'ALRT'   },
]

export default function Sidebar() {
  const logout   = useAuthStore((s) => s.logout)
  const username = useAuthStore((s) => s.username)

  return (
    <aside style={{
      width:66, minHeight:'100vh',
      background:'var(--surface)', borderRight:'1px solid var(--b-faint)',
      display:'flex', flexDirection:'column', alignItems:'center',
      flexShrink:0, zIndex:20,
    }}>
      {/* Logo */}
      <div style={{
        width:'100%', height:56,
        borderBottom:'1px solid var(--b-faint)',
        display:'flex', alignItems:'center', justifyContent:'center',
        flexShrink:0,
      }}>
        <div style={{ textAlign:'center', userSelect:'none' }}>
          <div style={{ fontFamily:'var(--fp)', fontSize:22, color:'var(--green)', textShadow:'0 0 8px rgba(52,210,110,.5)', lineHeight:1 }}>ST</div>
          <div style={{ fontFamily:'var(--fm)', fontSize:7, color:'var(--t4)', letterSpacing:'.25em', marginTop:1 }}>AI·v2</div>
        </div>
      </div>

      {/* Navigation */}
      <nav style={{ flex:1, width:'100%', paddingTop:8 }}>
        {NAV.map(({ to, icon:Icon, label }) => (
          <NavLink key={to} to={to} end={to=='/'}
            style={({ isActive }) => ({
              display:'flex', flexDirection:'column', alignItems:'center',
              justifyContent:'center', gap:3, padding:'12px 0', width:'100%',
              textDecoration:'none',
              color: isActive ? 'var(--green)' : 'var(--t4)',
              background: isActive ? 'var(--green-lo)' : 'transparent',
              borderLeft: `2px solid ${isActive ? 'var(--green)' : 'transparent'}`,
              transition:'all .15s',
            })}
          >
            {({ isActive }) => (<>
              <Icon size={15} strokeWidth={isActive?2:1.5} />
              <span style={{ fontFamily:'var(--fm)', fontSize:7, letterSpacing:'.1em', color:'inherit', marginTop:1 }}>{label}</span>
            </>)}
          </NavLink>
        ))}
      </nav>

      {/* User + logout */}
      <div style={{ borderTop:'1px solid var(--b-faint)', width:'100%', padding:'14px 0', display:'flex', flexDirection:'column', alignItems:'center', gap:10 }}>
        <div style={{ width:28, height:28, border:'1px solid var(--b-dim)', background:'var(--raised)', display:'flex', alignItems:'center', justifyContent:'center' }}>
          <span style={{ fontFamily:'var(--fm)', fontSize:11, color:'var(--green)' }}>{username?.[0]?.toUpperCase() || 'U'}</span>
        </div>
        <button onClick={logout} title="Sign out" style={{ background:'none', border:'none', cursor:'pointer', color:'var(--t3)', transition:'color .15s' }}
          onMouseEnter={e => e.currentTarget.style.color = 'var(--red)'}
          onMouseLeave={e => e.currentTarget.style.color = 'var(--t3)'}
        >
          <LogOut size={13} />
        </button>
      </div>
    </aside>
  )
}
