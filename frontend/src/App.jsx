import { BrowserRouter, NavLink, Route, Routes } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Companies from './pages/Companies'
import CompanyDetail from './pages/CompanyDetail'
import Pipeline from './pages/Pipeline'
import MLLab from './pages/MLLab'
import Benchmark from './pages/Benchmark'

export default function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <aside className="sidebar">
          <h1>Data Economy</h1>
          <p>Chế biến & Chế tạo</p>
          <nav>
            <NavLink to="/" end>Dashboard</NavLink>
            <NavLink to="/companies">Doanh nghiệp</NavLink>
            <NavLink to="/pipeline">Pipeline</NavLink>
            <NavLink to="/ml">ML Lab</NavLink>
            <NavLink to="/benchmark">So sánh</NavLink>
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
    </BrowserRouter>
  )
}
