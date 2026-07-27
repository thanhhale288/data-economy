import { useEffect, useState } from 'react'
import { BrowserRouter, NavLink, Route, Routes, useLocation } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Companies from './pages/Companies'
import CompanyDetail from './pages/CompanyDetail'
import Pipeline from './pages/Pipeline'
import MLLab from './pages/MLLab'
import Benchmark from './pages/Benchmark'

function AppShell() {
  const [navOpen, setNavOpen] = useState(false)
  const location = useLocation()

  useEffect(() => {
    setNavOpen(false)
  }, [location.pathname])

  useEffect(() => {
    if (!navOpen) return undefined

    const onKey = (e) => {
      if (e.key === 'Escape') setNavOpen(false)
    }
    const onResize = () => {
      if (window.matchMedia('(min-width: 769px)').matches) setNavOpen(false)
    }

    document.body.classList.add('nav-open')
    window.addEventListener('keydown', onKey)
    window.addEventListener('resize', onResize)
    return () => {
      document.body.classList.remove('nav-open')
      window.removeEventListener('keydown', onKey)
      window.removeEventListener('resize', onResize)
    }
  }, [navOpen])

  return (
    <div className={`app${navOpen ? ' is-nav-open' : ''}`}>
      <header className="mobile-topbar">
        <button
          type="button"
          className={`nav-toggle${navOpen ? ' is-open' : ''}`}
          aria-label={navOpen ? 'Đóng menu' : 'Mở menu'}
          aria-expanded={navOpen}
          aria-controls="app-sidebar"
          onClick={() => setNavOpen((open) => !open)}
        >
          <span className="nav-toggle-bar" />
          <span className="nav-toggle-bar" />
          <span className="nav-toggle-bar" />
        </button>
        <div className="mobile-topbar-brand">
          <strong>Data Economy</strong>
          <span>Chế biến & Chế tạo</span>
        </div>
      </header>

      <button
        type="button"
        className="sidebar-backdrop"
        aria-label="Đóng menu"
        tabIndex={navOpen ? 0 : -1}
        onClick={() => setNavOpen(false)}
      />

      <aside id="app-sidebar" className={`sidebar${navOpen ? ' is-open' : ''}`}>
        <div className="sidebar-brand">
          <h1>Data Economy</h1>
          <p>Chế biến & Chế tạo</p>
        </div>
        <nav>
          <NavLink to="/" end>Dashboard</NavLink>
          <NavLink to="/benchmark">Benchmark</NavLink>
          <NavLink to="/companies">Doanh nghiệp</NavLink>
          <NavLink to="/pipeline">Pipeline</NavLink>
          <NavLink to="/ml">ML Lab</NavLink>
        </nav>
      </aside>

      <main className="main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/companies" element={<Companies />} />
          <Route path="/companies/:code" element={<CompanyDetail />} />
          <Route path="/pipeline" element={<Pipeline />} />
          <Route path="/ml" element={<MLLab />} />
          <Route path="/benchmark" element={<Benchmark />} />
        </Routes>
      </main>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppShell />
    </BrowserRouter>
  )
}
