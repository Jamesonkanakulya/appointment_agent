import { useState, useEffect } from 'react'
import { Routes, Route, useNavigate } from 'react-router-dom'
import api, { Instance } from '../api/client'
import InstanceSettings from '../components/InstanceSettings'
import GlobalSettings from '../components/GlobalSettings'
import { Calendar, Settings, LogOut, Plus } from 'lucide-react'

export default function Dashboard() {
  const [instances, setInstances] = useState<Instance[]>([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    loadInstances()
  }, [])

  async function loadInstances() {
    try {
      const res = await api.get('/instances')
      setInstances(res.data)
    } finally {
      setLoading(false)
    }
  }

  function handleLogout() {
    localStorage.removeItem('token')
    navigate('/login')
  }

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <div className="bg-blue-600 text-white p-1.5 rounded-lg">
              <Calendar size={18} />
            </div>
            <span className="font-semibold text-gray-800 text-sm">Appointment Agent</span>
          </div>
        </div>

        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          <button
            onClick={() => navigate('/new')}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-blue-600 bg-blue-50 rounded-lg hover:bg-blue-100 font-medium transition-colors"
          >
            <Plus size={16} />
            New Instance
          </button>

          <div className="pt-2">
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wide px-3 mb-1">Instances</p>
            {loading ? (
              <p className="text-xs text-gray-400 px-3">Loading…</p>
            ) : instances.length === 0 ? (
              <p className="text-xs text-gray-400 px-3">No instances yet</p>
            ) : (
              instances.map((inst) => (
                <button
                  key={inst.id}
                  onClick={() => navigate(`/instance/${inst.id}`)}
                  className="w-full text-left px-3 py-2 text-sm text-gray-700 rounded-lg hover:bg-gray-100 truncate transition-colors"
                >
                  {inst.name}
                </button>
              ))
            )}
          </div>
        </nav>

        <div className="p-3 border-t border-gray-200 space-y-1">
          <button
            onClick={() => navigate('/settings')}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <Settings size={16} />
            Global Settings
          </button>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <LogOut size={16} />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <Routes>
          <Route path="/" element={<WelcomeScreen />} />
          <Route path="/new" element={<InstanceSettings isNew onSave={() => { loadInstances(); navigate('/') }} />} />
          <Route path="/instance/:id" element={<InstanceSettings onSave={loadInstances} />} />
          <Route path="/settings" element={<GlobalSettings />} />
        </Routes>
      </main>
    </div>
  )
}

function WelcomeScreen() {
  return (
    <div className="flex items-center justify-center h-full text-center p-8">
      <div>
        <div className="bg-blue-50 rounded-full w-20 h-20 flex items-center justify-center mx-auto mb-4">
          <Calendar size={40} className="text-blue-600" />
        </div>
        <h2 className="text-xl font-semibold text-gray-800 mb-2">Welcome to Appointment Agent</h2>
        <p className="text-gray-500 text-sm max-w-sm">
          Create a new instance to start accepting appointment bookings from your chatbot.
        </p>
      </div>
    </div>
  )
}
