import { useState, useEffect } from 'react'
import api, { GuestRecord } from '../api/client'
import { Eye, EyeOff, RefreshCw } from 'lucide-react'

interface Props {
  instanceId: string
}

export default function GuestTable({ instanceId }: Props) {
  const [guests, setGuests] = useState<GuestRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('')
  const [revealedPins, setRevealedPins] = useState<Set<number>>(new Set())

  useEffect(() => {
    loadGuests()
  }, [instanceId, statusFilter])

  async function loadGuests() {
    setLoading(true)
    try {
      const params = statusFilter ? { status: statusFilter } : {}
      const res = await api.get(`/instances/${instanceId}/guests`, { params })
      setGuests(res.data)
    } finally {
      setLoading(false)
    }
  }

  function togglePin(id: number) {
    setRevealedPins((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  function formatDate(dt?: string) {
    if (!dt) return '—'
    return new Date(dt).toLocaleString(undefined, {
      dateStyle: 'medium', timeStyle: 'short'
    })
  }

  const statusColors: Record<string, string> = {
    Active: 'bg-green-100 text-green-700',
    Canceled: 'bg-red-100 text-red-700',
    Rescheduled: 'bg-yellow-100 text-yellow-700',
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div className="flex gap-2">
          {['', 'Active', 'Canceled', 'Rescheduled'].map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-3 py-1.5 text-xs font-medium rounded-full transition-colors ${
                statusFilter === s
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {s || 'All'}
            </button>
          ))}
        </div>
        <button onClick={loadGuests} className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 transition-colors">
          <RefreshCw size={14} />
          Refresh
        </button>
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-400 text-sm">Loading…</div>
      ) : guests.length === 0 ? (
        <div className="text-center py-12 text-gray-400 text-sm">No guest records found</div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-gray-200">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left px-4 py-3 font-medium text-gray-600">Name</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Email</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">PIN</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Booking Time</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Meeting</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {guests.map((g) => (
                <tr key={g.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-800">{g.name || '—'}</td>
                  <td className="px-4 py-3 text-gray-600">{g.email}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1.5">
                      <span className="font-mono">
                        {revealedPins.has(g.id) ? g.pin_code : '●●●●'}
                      </span>
                      <button
                        onClick={() => togglePin(g.id)}
                        className="text-gray-400 hover:text-gray-600 transition-colors"
                      >
                        {revealedPins.has(g.id) ? <EyeOff size={14} /> : <Eye size={14} />}
                      </button>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-gray-600 whitespace-nowrap">{formatDate(g.booking_time)}</td>
                  <td className="px-4 py-3 text-gray-600 max-w-xs truncate">{g.meeting_title || '—'}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusColors[g.status] || 'bg-gray-100 text-gray-600'}`}>
                      {g.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
