import { Routes, Route } from 'react-router-dom'
import Sidebar from './components/layout/Sidebar'
import Navbar from './components/layout/Navbar'
import MapPage from './pages/MapPage'
import DashboardPage from './pages/DashboardPage'
import ComparePage from './pages/ComparePage'
import AlertsPage from './pages/AlertsPage'

export default function App() {
  return (
    <div className="flex h-screen bg-gray-50 dark:bg-[#0a0e1a] text-gray-900 dark:text-white overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Navbar />
        <main className="flex-1 overflow-hidden">
          <Routes>
            <Route path="/" element={<MapPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/compare" element={<ComparePage />} />
            <Route path="/alerts" element={<AlertsPage />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}
