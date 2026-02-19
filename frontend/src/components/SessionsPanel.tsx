import { useState, useEffect } from 'react'
import api, { Session } from '../api/client'
import { Trash2, RefreshCw, MessageSquare } from 'lucide-react'

interface Props {
  instanceId: string
}

export default function SessionsPanel({ instanceId }: Props) {
  const [sessions, setSessions] = useState<Session[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadSessions()
  }, [instanceId])

  async function loadSessions() {
    setLoading(true)
    try {
      const res = await api.get(`/instances/${instanceId}/sessions`)
      setSessions(res.data)
    } finally {
      setLoading(false)
    }
  }

  async function deleteSession(sessionId: string) {
    if (!window.confirm('Clear this conversation session?')) return
    await api.delete(`/instances/${instanceId}/sessions/${sessionId}`)
    await loadSessions()
  }

  function formatDate(dt: string) {
    return new Date(dt).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-700">Active Conversations ({sessions.length})</h3>
        <button onClick={loadSessions} className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 transition-colors">
          <RefreshCw size={14} />
          Refresh
        </button>
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-400 text-sm">Loading…</div>
      ) : sessions.length === 0 ? (
        <div className="text-center py-12 text-gray-400 text-sm">
          <MessageSquare className="mx-auto mb-2 opacity-40" size={32} />
          No active sessions
        </div>
      ) : (
        <div className="space-y-2">
          {sessions.map((s) => (
            <div key={s.session_id} className="flex items-center justify-between bg-white border border-gray-200 rounded-lg px-4 py-3">
              <div>
                <p className="text-sm font-mono text-gray-800">{s.session_id}</p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {s.message_count} messages · Last active: {formatDate(s.updated_at)}
                </p>
              </div>
              <button
                onClick={() => deleteSession(s.session_id)}
                className="text-gray-400 hover:text-red-500 transition-colors p-1.5 rounded-lg hover:bg-red-50"
                title="Clear session"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
