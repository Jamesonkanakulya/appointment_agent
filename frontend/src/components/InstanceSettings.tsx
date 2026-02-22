import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api, { Instance } from '../api/client'
import CalendarProviderForm from './CalendarProviderForm'
import WebhookPanel from './WebhookPanel'
import GuestTable from './GuestTable'
import SessionsPanel from './SessionsPanel'
import { Save, Trash2, AlertCircle, CheckCircle, Mail } from 'lucide-react'

const TABS = ['Configuration', 'Calendar', 'Email', 'Webhook', 'Guests', 'Sessions']

const TIMEZONES = [
  'UTC', 'Asia/Dubai', 'America/New_York', 'America/Chicago', 'America/Denver',
  'America/Los_Angeles', 'Europe/London', 'Europe/Paris', 'Europe/Berlin',
  'Asia/Tokyo', 'Asia/Singapore', 'Asia/Kolkata', 'Australia/Sydney',
  'Pacific/Auckland', 'America/Toronto', 'America/Sao_Paulo',
]

const TIMEZONE_OFFSETS: Record<string, string> = {
  'UTC': '+00:00', 'Asia/Dubai': '+04:00', 'America/New_York': '-05:00',
  'America/Chicago': '-06:00', 'America/Denver': '-07:00', 'America/Los_Angeles': '-08:00',
  'Europe/London': '+00:00', 'Europe/Paris': '+01:00', 'Europe/Berlin': '+01:00',
  'Asia/Tokyo': '+09:00', 'Asia/Singapore': '+08:00', 'Asia/Kolkata': '+05:30',
  'Australia/Sydney': '+11:00', 'Pacific/Auckland': '+13:00',
  'America/Toronto': '-05:00', 'America/Sao_Paulo': '-03:00',
}

interface Props {
  isNew?: boolean
  onSave?: () => void
}

export default function InstanceSettings({ isNew = false, onSave }: Props) {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [tab, setTab] = useState('Configuration')
  const [instance, setInstance] = useState<Instance | null>(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const [form, setForm] = useState<Record<string, any>>({
    name: '', webhook_path: '', business_name: '',
    timezone: 'UTC', timezone_offset: '+00:00',
    workday_start: '09:00', workday_end: '17:00',
    calcom_api_key: '',
    calcom_event_type_id: '',
    // SMTP
    smtp_host: '',
    smtp_port: '587',
    smtp_user: '',
    smtp_password: '',
    smtp_from_email: '',
  })

  useEffect(() => {
    if (!isNew && id) {
      api.get(`/instances/${id}`).then((res) => {
        setInstance(res.data)
        const d = res.data
        setForm((f) => ({
          ...f,
          name: d.name,
          webhook_path: d.webhook_path,
          business_name: d.business_name,
          timezone: d.timezone,
          timezone_offset: d.timezone_offset,
          workday_start: d.workday_start,
          workday_end: d.workday_end,
          calcom_event_type_id: d.calcom_event_type_id || '',
          // calcom_api_key intentionally left blank — shows "configured" badge instead
          smtp_host: d.smtp_host || '',
          smtp_port: String(d.smtp_port || 587),
          smtp_user: d.smtp_user || '',
          smtp_from_email: d.smtp_from_email || '',
          // smtp_password intentionally left blank
        }))
      })
    }
  }, [id, isNew])

  function setField(key: string, value: any) {
    setForm((f) => {
      const updated = { ...f, [key]: value }
      if (key === 'timezone') {
        updated.timezone_offset = TIMEZONE_OFFSETS[value] || '+00:00'
      }
      return updated
    })
  }

  async function handleSave() {
    setError('')
    setSuccess('')
    setSaving(true)
    try {
      const payload: Record<string, any> = {
        name: form.name,
        webhook_path: form.webhook_path,
        business_name: form.business_name,
        timezone: form.timezone,
        timezone_offset: form.timezone_offset,
        workday_start: form.workday_start,
        workday_end: form.workday_end,
      }

      if (form.calcom_api_key) payload.calcom_api_key = form.calcom_api_key
      if (form.calcom_event_type_id) payload.calcom_event_type_id = parseInt(form.calcom_event_type_id)

      // SMTP — only send fields that are set
      if (form.smtp_host !== undefined) payload.smtp_host = form.smtp_host || null
      if (form.smtp_port) payload.smtp_port = parseInt(form.smtp_port) || 587
      if (form.smtp_user !== undefined) payload.smtp_user = form.smtp_user || null
      if (form.smtp_password) payload.smtp_password = form.smtp_password
      if (form.smtp_from_email !== undefined) payload.smtp_from_email = form.smtp_from_email || null

      if (isNew) {
        const res = await api.post('/instances', payload)
        setSuccess('Instance created successfully.')
        onSave?.()
        navigate(`/instance/${res.data.id}`)
      } else {
        const res = await api.put(`/instances/${id}`, payload)
        setInstance(res.data)
        setSuccess('Settings saved successfully.')
        setForm((f) => ({ ...f, smtp_password: '' }))
        onSave?.()
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save settings.')
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete() {
    if (!window.confirm(`Delete instance "${form.name}"? This cannot be undone.`)) return
    try {
      await api.delete(`/instances/${id}`)
      onSave?.()
      navigate('/')
    } catch {
      setError('Failed to delete instance.')
    }
  }

  const showTabs = !isNew
  const displayTabs = showTabs ? TABS : ['Configuration', 'Calendar', 'Email']
  const saveableTabs = ['Configuration', 'Calendar', 'Email']

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-900">
            {isNew ? 'New Instance' : form.name || 'Instance Settings'}
          </h1>
          {!isNew && instance && (
            <p className="text-sm text-gray-500 mt-0.5">
              Webhook: <code className="bg-gray-100 px-1 rounded text-xs">/webhook/{instance.webhook_path}</code>
            </p>
          )}
        </div>
        <div className="flex gap-2">
          {!isNew && (
            <button
              onClick={handleDelete}
              className="flex items-center gap-1.5 px-3 py-2 text-sm text-red-600 border border-red-200 rounded-lg hover:bg-red-50 transition-colors"
            >
              <Trash2 size={14} />
              Delete
            </button>
          )}
          {(saveableTabs.includes(tab) || isNew) && (
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex items-center gap-1.5 px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              <Save size={14} />
              {saving ? 'Saving…' : isNew ? 'Create Instance' : 'Save Changes'}
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 mb-4 text-sm">
          <AlertCircle size={16} />
          {error}
        </div>
      )}
      {success && (
        <div className="bg-green-50 border border-green-200 text-green-700 rounded-lg px-4 py-3 mb-4 text-sm">
          {success}
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex gap-1">
          {displayTabs.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                tab === t
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {t}
              {t === 'Email' && instance?.smtp_configured && (
                <span className="ml-1.5 inline-block w-2 h-2 bg-green-500 rounded-full" />
              )}
            </button>
          ))}
        </nav>
      </div>

      {tab === 'Configuration' && (
        <ConfigTab form={form} setField={setField} TIMEZONES={TIMEZONES} />
      )}
      {tab === 'Calendar' && (
        <CalendarProviderForm form={form} setField={setField} instance={instance} />
      )}
      {tab === 'Email' && (
        <EmailTab form={form} setField={setField} instance={instance} />
      )}
      {tab === 'Webhook' && instance && (
        <WebhookPanel instance={instance} />
      )}
      {tab === 'Guests' && instance && (
        <GuestTable instanceId={instance.id} />
      )}
      {tab === 'Sessions' && instance && (
        <SessionsPanel instanceId={instance.id} />
      )}
    </div>
  )
}

function EmailTab({ form, setField, instance }: any) {
  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-sm font-semibold text-gray-900">Instance Email (SMTP)</h2>
          <p className="text-xs text-gray-500 mt-0.5">
            Configure a dedicated sender for this instance. Overrides the global SMTP settings.
          </p>
        </div>
        {instance?.smtp_configured && (
          <span className="flex items-center gap-1 text-xs text-green-700 bg-green-50 border border-green-200 px-2 py-1 rounded-full">
            <CheckCircle size={12} />
            Configured
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Field label="SMTP Host">
          <input
            type="text"
            value={form.smtp_host}
            onChange={(e) => setField('smtp_host', e.target.value)}
            className="input"
            placeholder="smtp.gmail.com"
          />
        </Field>
        <Field label="SMTP Port">
          <input
            type="number"
            value={form.smtp_port}
            onChange={(e) => setField('smtp_port', e.target.value)}
            className="input"
            placeholder="587"
          />
        </Field>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Field label="Username / Email">
          <input
            type="text"
            value={form.smtp_user}
            onChange={(e) => setField('smtp_user', e.target.value)}
            className="input"
            placeholder="you@gmail.com"
          />
        </Field>
        <Field
          label="Password / App Password"
          hint={instance?.smtp_configured ? 'Leave blank to keep existing password' : ''}
        >
          <input
            type="password"
            value={form.smtp_password}
            onChange={(e) => setField('smtp_password', e.target.value)}
            className="input"
            placeholder={instance?.smtp_configured ? '••••••••' : 'Enter password'}
            autoComplete="new-password"
          />
        </Field>
      </div>

      <Field label="From Email" hint="Displayed as the sender address. Defaults to username if blank.">
        <input
          type="email"
          value={form.smtp_from_email}
          onChange={(e) => setField('smtp_from_email', e.target.value)}
          className="input"
          placeholder="bookings@yourbusiness.com"
        />
      </Field>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-xs text-blue-800 space-y-1">
        <div className="flex items-center gap-1.5 font-medium">
          <Mail size={13} />
          Gmail App Password
        </div>
        <p>Go to Google Account → Security → 2-Step Verification → App passwords. Generate one for "Mail" and paste it as the password above.</p>
      </div>
    </div>
  )
}

function ConfigTab({ form, setField, TIMEZONES }: any) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <Field label="Instance Name" required>
          <input
            type="text"
            value={form.name}
            onChange={(e) => setField('name', e.target.value)}
            className="input"
            placeholder="e.g. My Website Bookings"
          />
        </Field>
        <Field label="Webhook Path" required hint="Letters, numbers, hyphens only">
          <div className="flex items-center border border-gray-300 rounded-lg overflow-hidden focus-within:ring-2 focus-within:ring-blue-500">
            <span className="bg-gray-50 px-3 py-2 text-sm text-gray-500 border-r border-gray-300">/webhook/</span>
            <input
              type="text"
              value={form.webhook_path}
              onChange={(e) => setField('webhook_path', e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, '-'))}
              className="flex-1 px-3 py-2 text-sm outline-none"
              placeholder="my-website"
            />
          </div>
        </Field>
      </div>

      <Field label="Business Name" required>
        <input
          type="text"
          value={form.business_name}
          onChange={(e) => setField('business_name', e.target.value)}
          className="input"
          placeholder="e.g. Acme Corp"
        />
      </Field>

      <div className="grid grid-cols-2 gap-4">
        <Field label="Timezone">
          <select value={form.timezone} onChange={(e) => setField('timezone', e.target.value)} className="input">
            {TIMEZONES.map((tz: string) => (
              <option key={tz} value={tz}>{tz}</option>
            ))}
          </select>
        </Field>
        <Field label="UTC Offset">
          <input
            type="text"
            value={form.timezone_offset}
            onChange={(e) => setField('timezone_offset', e.target.value)}
            className="input"
            placeholder="+04:00"
          />
        </Field>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Field label="Business Hours Start">
          <input type="time" value={form.workday_start} onChange={(e) => setField('workday_start', e.target.value)} className="input" />
        </Field>
        <Field label="Business Hours End">
          <input type="time" value={form.workday_end} onChange={(e) => setField('workday_end', e.target.value)} className="input" />
        </Field>
      </div>
    </div>
  )
}

export function Field({ label, children, hint, required }: {
  label: string
  children: React.ReactNode
  hint?: string
  required?: boolean
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label} {required && <span className="text-red-500">*</span>}
      </label>
      {children}
      {hint && <p className="text-xs text-gray-400 mt-1">{hint}</p>}
    </div>
  )
}
