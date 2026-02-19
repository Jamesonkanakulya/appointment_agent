import { useState, useEffect } from 'react'
import api, { GlobalSettings as GlobalSettingsType } from '../api/client'
import { Save, CheckCircle, AlertCircle, ExternalLink } from 'lucide-react'
import { Field } from './InstanceSettings'

const PROVIDERS = [
  { id: 'openai_github', label: 'GitHub Models (GPT-4o)', model: 'openai/gpt-4o', base_url: 'https://models.github.ai/inference' },
  { id: 'openai', label: 'OpenAI', model: 'gpt-4o', base_url: '' },
  { id: 'anthropic', label: 'Anthropic (Claude)', model: 'claude-sonnet-4-6', base_url: '' },
  { id: 'mistral', label: 'Mistral', model: 'mistral-large-latest', base_url: '' },
  { id: 'custom', label: 'Custom (OpenAI-compatible)', model: '', base_url: '' },
]

export default function GlobalSettings() {
  const [settings, setSettings] = useState<GlobalSettingsType | null>(null)
  const [provider, setProvider] = useState('openai_github')
  const [apiKey, setApiKey] = useState('')
  const [baseUrl, setBaseUrl] = useState('https://models.github.ai/inference')
  const [model, setModel] = useState('openai/gpt-4o')

  // SMTP state
  const [smtpHost, setSmtpHost] = useState('')
  const [smtpPort, setSmtpPort] = useState('587')
  const [smtpUser, setSmtpUser] = useState('')
  const [smtpPassword, setSmtpPassword] = useState('')
  const [smtpFromEmail, setSmtpFromEmail] = useState('')

  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    api.get('/settings').then((res) => {
      setSettings(res.data)
      const matching = PROVIDERS.find((p) =>
        p.base_url === res.data.llm_base_url && res.data.llm_model.startsWith(p.model.split('-')[0])
      )
      if (matching) setProvider(matching.id)
      else setProvider('custom')
      setBaseUrl(res.data.llm_base_url || '')
      setModel(res.data.llm_model || '')

      // Populate SMTP fields
      setSmtpHost(res.data.smtp_host || '')
      setSmtpPort(String(res.data.smtp_port || 587))
      setSmtpUser(res.data.smtp_user || '')
      setSmtpFromEmail(res.data.smtp_from_email || '')
    })
  }, [])

  function selectProvider(id: string) {
    setProvider(id)
    const p = PROVIDERS.find((x) => x.id === id)
    if (p && id !== 'custom') {
      setBaseUrl(p.base_url)
      setModel(p.model)
    }
  }

  async function handleSave() {
    setSaving(true)
    setError('')
    setSuccess('')
    try {
      await api.put('/settings', {
        llm_provider: provider === 'openai_github' ? 'openai' : provider,
        llm_base_url: baseUrl,
        llm_api_key: apiKey || undefined,
        llm_model: model,
        smtp_host: smtpHost || undefined,
        smtp_port: smtpPort ? parseInt(smtpPort) : undefined,
        smtp_user: smtpUser || undefined,
        smtp_password: smtpPassword || undefined,
        smtp_from_email: smtpFromEmail || undefined,
      })
      setSuccess('Settings saved.')
      setApiKey('')
      setSmtpPassword('')
      // Refresh to get updated smtp_configured status
      const res = await api.get('/settings')
      setSettings(res.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Global Settings</h1>
          <p className="text-sm text-gray-500 mt-0.5">LLM provider and email configuration for all instances</p>
        </div>
        <button
          onClick={handleSave}
          disabled={saving}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          <Save size={14} />
          {saving ? 'Saving…' : 'Save'}
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 mb-4 text-sm">
          <AlertCircle size={16} /> {error}
        </div>
      )}
      {success && (
        <div className="flex items-center gap-2 bg-green-50 border border-green-200 text-green-700 rounded-lg px-4 py-3 mb-4 text-sm">
          <CheckCircle size={16} /> {success}
        </div>
      )}

      {/* ── LLM Settings ── */}
      <div className="space-y-6 mb-8">
        <h2 className="text-base font-semibold text-gray-800 border-b border-gray-200 pb-2">LLM Provider</h2>

        <Field label="Provider">
          <div className="grid grid-cols-2 gap-2">
            {PROVIDERS.map((p) => (
              <button
                key={p.id}
                type="button"
                onClick={() => selectProvider(p.id)}
                className={`py-2.5 px-3 border-2 rounded-xl text-sm font-medium text-left transition-all ${
                  provider === p.id
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-gray-200 text-gray-600 hover:border-gray-300'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </Field>

        <Field
          label="API Key"
          hint={settings?.llm_api_key_set ? '✓ API key is saved — enter a new value to update' : 'Required for LLM access'}
        >
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            className="input"
            placeholder={settings?.llm_api_key_set ? '(unchanged)' : 'Enter your API key'}
          />
        </Field>

        {(provider === 'openai_github' || provider === 'custom') && (
          <Field label="Base URL" hint="OpenAI-compatible API endpoint">
            <input
              type="text"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              className="input"
              placeholder="https://models.github.ai/inference"
            />
          </Field>
        )}

        <Field label="Model">
          <input
            type="text"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="input"
            placeholder="e.g. openai/gpt-4o, claude-sonnet-4-6"
          />
        </Field>

        <div className="bg-gray-50 rounded-xl p-4 text-xs text-gray-500 space-y-1">
          <p className="font-medium text-gray-600 mb-2">Where to get your API key:</p>
          {[
            { label: 'GitHub Models', url: 'https://github.com/settings/tokens' },
            { label: 'OpenAI', url: 'https://platform.openai.com/api-keys' },
            { label: 'Anthropic', url: 'https://console.anthropic.com/settings/keys' },
            { label: 'Mistral', url: 'https://console.mistral.ai/api-keys/' },
          ].map((l) => (
            <a
              key={l.label}
              href={l.url}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1 hover:text-blue-600 transition-colors"
            >
              <ExternalLink size={11} />
              {l.label}
            </a>
          ))}
        </div>
      </div>

      {/* ── SMTP Settings ── */}
      <div className="space-y-6">
        <div className="flex items-center justify-between border-b border-gray-200 pb-2">
          <h2 className="text-base font-semibold text-gray-800">Email (SMTP)</h2>
          {settings?.smtp_configured && (
            <span className="flex items-center gap-1 text-xs text-green-600">
              <CheckCircle size={13} /> Configured
            </span>
          )}
        </div>

        <p className="text-xs text-gray-500">
          Used to send booking confirmation, cancellation, and reschedule emails to guests.
          Leave blank to disable email notifications.
        </p>

        <div className="grid grid-cols-3 gap-4">
          <div className="col-span-2">
            <Field label="SMTP Host" hint="e.g. smtp.gmail.com">
              <input
                type="text"
                value={smtpHost}
                onChange={(e) => setSmtpHost(e.target.value)}
                className="input"
                placeholder="smtp.gmail.com"
              />
            </Field>
          </div>
          <Field label="Port">
            <input
              type="number"
              value={smtpPort}
              onChange={(e) => setSmtpPort(e.target.value)}
              className="input"
              placeholder="587"
            />
          </Field>
        </div>

        <Field label="SMTP Username" hint="Usually your email address">
          <input
            type="text"
            value={smtpUser}
            onChange={(e) => setSmtpUser(e.target.value)}
            className="input"
            placeholder="you@gmail.com"
          />
        </Field>

        <Field
          label="SMTP Password"
          hint={settings?.smtp_configured ? '✓ Password saved — enter new password to update' : 'For Gmail: use an App Password'}
        >
          <input
            type="password"
            value={smtpPassword}
            onChange={(e) => setSmtpPassword(e.target.value)}
            className="input"
            placeholder={settings?.smtp_configured ? '(unchanged)' : 'Enter SMTP password or App Password'}
          />
        </Field>

        <Field label="From Email" hint="Sender address shown to guests (defaults to SMTP username)">
          <input
            type="email"
            value={smtpFromEmail}
            onChange={(e) => setSmtpFromEmail(e.target.value)}
            className="input"
            placeholder="bookings@yourcompany.com"
          />
        </Field>

        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs text-amber-700">
          <strong>Gmail tip:</strong> Enable 2FA → go to{' '}
          <a
            href="https://myaccount.google.com/apppasswords"
            target="_blank"
            rel="noreferrer"
            className="underline"
          >
            App Passwords
          </a>{' '}
          → generate a password for "Mail" and use it here instead of your Gmail password.
        </div>
      </div>
    </div>
  )
}
