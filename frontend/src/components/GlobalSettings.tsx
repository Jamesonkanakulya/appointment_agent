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
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<string | null>(null)

  useEffect(() => {
    api.get('/settings').then((res) => {
      setSettings(res.data)
      // Determine which provider matches
      const matching = PROVIDERS.find((p) =>
        p.base_url === res.data.llm_base_url && res.data.llm_model.startsWith(p.model.split('-')[0])
      )
      if (matching) setProvider(matching.id)
      else setProvider('custom')
      setBaseUrl(res.data.llm_base_url || '')
      setModel(res.data.llm_model || '')
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
      })
      setSuccess('Settings saved.')
      setApiKey('')
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
          <p className="text-sm text-gray-500 mt-0.5">LLM provider configuration used by all instances</p>
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

      <div className="space-y-6">
        {/* Provider selection */}
        <Field label="LLM Provider">
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

        {/* API Key guides */}
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
    </div>
  )
}
