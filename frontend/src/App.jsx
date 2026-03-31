import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import ProtectedRoute from './components/layout/ProtectedRoute'
import Sidebar   from './components/layout/Sidebar'
import Login     from './pages/Login'
import Live      from './pages/Live'
import Analytics from './pages/Analytics'
import Database  from './pages/Database'
import Clips     from './pages/Clips'
import Camera    from './pages/Camera'
import Alerts    from './pages/Alerts'

function Shell({ children }) {
  return (
    <div className="shell">
      <Sidebar />
      <div className="main-col">{children}</div>
    </div>
  )
}

const P = ({ children }) => (
  <ProtectedRoute><Shell>{children}</Shell></ProtectedRoute>
)

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login"     element={<Login />} />
        <Route path="/"          element={<P><Live /></P>} />
        <Route path="/analytics" element={<P><Analytics /></P>} />
        <Route path="/database"  element={<P><Database /></P>} />
        <Route path="/clips"     element={<P><Clips /></P>} />
        <Route path="/camera"    element={<P><Camera /></P>} />
        <Route path="/alerts"    element={<P><Alerts /></P>} />
        <Route path="*"          element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
