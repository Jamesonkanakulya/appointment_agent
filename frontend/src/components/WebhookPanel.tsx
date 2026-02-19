import { useState } from 'react'
import type { Instance } from '../api/client'
import { Copy, Check, Send } from 'lucide-react'
import axios from 'axios'

interface Props {
  instance: Instance
}

export default function WebhookPanel({ instance }: Props) {
  const [copied, setCopied] = useState(false)
  const [testMessage, setTestMessage] = useState('What times are available tomorrow?')
  const [testSessionId, setTestSessionId] = useState(`test-${Date.now()}`)
  const [testResult, setTestResult] = useState<{ response?: string; error?: string } | null>(null)
  const [testing, setTesting] = useState(false)

  const webhookUrl = `${window.location.origin}/webhook/${instance.webhook_path}`

  async function copyUrl() {
    await navigator.clipboard.writeText(webhookUrl)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  async function sendTest() {
    setTesting(true)
    setTestResult(null)
    try {
      const res = await axios.post(`/webhook/${instance.webhook_path}`, {
        sessionId: testSessionId,
        message: testMessage,
      })
      setTestResult({ response: res.data.response })
    } catch (err: any) {
      setTestResult({ error: err.response?.data?.detail || err.message })
    } finally {
      setTesting(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Webhook URL */}
      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-2">Webhook URL</h3>
        <div className="flex items-center gap-2">
          <code className="flex-1 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2.5 text-sm font-mono text-gray-800 break-all">
            {webhookUrl}
          </code>
          <button
            onClick={copyUrl}
            className="flex items-center gap-1.5 px-3 py-2.5 text-sm bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors shrink-0"
          >
            {copied ? <Check size={14} className="text-green-600" /> : <Copy size={14} />}
            {copied ? 'Copied' : 'Copy'}
          </button>
        </div>
      </div>

      {/* Expected format */}
      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-2">Request Format (POST)</h3>
        <pre className="bg-gray-900 text-green-400 rounded-lg px-4 py-3 text-xs overflow-x-auto">
{`POST ${webhookUrl}
Content-Type: application/json

{
  "sessionId": "unique-session-id",
  "message": "user's message text"
}`}
        </pre>
      </div>

      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-2">Response Format</h3>
        <pre className="bg-gray-900 text-green-400 rounded-lg px-4 py-3 text-xs overflow-x-auto">
{`{
  "response": "agent's reply",
  "sessionId": "unique-session-id"
}`}
        </pre>
      </div>

      {/* Test Console */}
      <div className="border border-gray-200 rounded-xl p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">Test Webhook</h3>
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Session ID</label>
            <input
              type="text"
              value={testSessionId}
              onChange={(e) => setTestSessionId(e.target.value)}
              className="input text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Message</label>
            <textarea
              value={testMessage}
              onChange={(e) => setTestMessage(e.target.value)}
              rows={2}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
          </div>
          <button
            onClick={sendTest}
            disabled={testing}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            <Send size={14} />
            {testing ? 'Sending…' : 'Send Test'}
          </button>
        </div>

        {testResult && (
          <div className={`mt-4 rounded-lg p-3 text-sm ${testResult.error ? 'bg-red-50 text-red-700 border border-red-200' : 'bg-green-50 text-green-700 border border-green-200'}`}>
            <p className="font-medium mb-1">{testResult.error ? 'Error:' : 'Response:'}</p>
            <p className="whitespace-pre-wrap">{testResult.error || testResult.response}</p>
          </div>
        )}
      </div>
    </div>
  )
}
