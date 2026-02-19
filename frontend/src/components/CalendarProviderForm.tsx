import { useState } from 'react'
import { ChevronDown, ChevronUp, ExternalLink } from 'lucide-react'
import { Field } from './InstanceSettings'
import type { Instance } from '../api/client'

interface Props {
  form: Record<string, string>
  setField: (key: string, value: string) => void
  instance: Instance | null
}

export default function CalendarProviderForm({ form, setField, instance }: Props) {
  const [showGuide, setShowGuide] = useState(false)

  return (
    <div className="space-y-6">
      {/* Provider Selector */}
      <Field label="Calendar Provider">
        <div className="flex gap-3">
          {(['google', 'microsoft'] as const).map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => setField('calendar_provider', p)}
              className={`flex-1 py-3 px-4 border-2 rounded-xl text-sm font-medium transition-all ${
                form.calendar_provider === p
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-gray-200 text-gray-600 hover:border-gray-300'
              }`}
            >
              {p === 'google' ? '🗓 Google Calendar' : '📅 Microsoft 365'}
            </button>
          ))}
        </div>
      </Field>

      {/* Google Calendar Settings */}
      {form.calendar_provider === 'google' && (
        <div className="space-y-4">
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
            <button
              type="button"
              onClick={() => setShowGuide(!showGuide)}
              className="w-full flex items-center justify-between text-sm font-medium text-amber-800"
            >
              <span>📖 Google Calendar Setup Guide</span>
              {showGuide ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </button>
            {showGuide && (
              <ol className="mt-3 text-sm text-amber-700 space-y-2 list-decimal list-inside">
                <li>Go to <a href="https://console.cloud.google.com" target="_blank" rel="noreferrer" className="underline inline-flex items-center gap-1">Google Cloud Console <ExternalLink size={12} /></a></li>
                <li>Create or select a project → Enable <strong>Google Calendar API</strong></li>
                <li>Go to <strong>IAM & Admin → Service Accounts</strong></li>
                <li>Create a service account → Click it → Go to <strong>Keys</strong> tab</li>
                <li>Click <strong>Add Key → Create new key → JSON</strong> → Download</li>
                <li>Paste the entire JSON file content in the field below</li>
                <li>Open Google Calendar → Share your calendar with the service account email (found in the JSON as <code>client_email</code>)</li>
                <li>Enter the calendar ID below (your email or from calendar settings)</li>
              </ol>
            )}
          </div>

          <Field label="Service Account JSON">
            {instance?.google_service_account_configured && !form.google_service_account_json && (
              <div className="flex items-center gap-2 mb-2 px-3 py-2 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">
                <span>✓</span>
                <span>Service account credentials saved. Paste new JSON below to replace.</span>
              </div>
            )}
            <textarea
              value={form.google_service_account_json}
              onChange={(e) => setField('google_service_account_json', e.target.value)}
              rows={8}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-xs font-mono focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              placeholder={instance?.google_service_account_configured
                ? '(Leave blank to keep existing credentials, or paste new JSON to replace)'
                : '{"type": "service_account", "project_id": "...", "private_key": "...", ...}'}
            />
          </Field>

          <Field label="Calendar ID" required hint="e.g., your-email@gmail.com or the calendar ID from Google Calendar settings">
            <input
              type="text"
              value={form.google_calendar_id}
              onChange={(e) => setField('google_calendar_id', e.target.value)}
              className="input"
              placeholder="user@yourdomain.com"
            />
          </Field>
        </div>
      )}

      {/* Microsoft 365 Settings */}
      {form.calendar_provider === 'microsoft' && (
        <div className="space-y-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <button
              type="button"
              onClick={() => setShowGuide(!showGuide)}
              className="w-full flex items-center justify-between text-sm font-medium text-blue-800"
            >
              <span>📖 Microsoft 365 Setup Guide</span>
              {showGuide ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </button>
            {showGuide && (
              <ol className="mt-3 text-sm text-blue-700 space-y-2 list-decimal list-inside">
                <li>Go to <a href="https://portal.azure.com" target="_blank" rel="noreferrer" className="underline inline-flex items-center gap-1">Azure Portal <ExternalLink size={12} /></a> → <strong>Azure Active Directory</strong></li>
                <li>Click <strong>App registrations → New registration</strong></li>
                <li>Name your app, select <strong>Accounts in this organizational directory only</strong></li>
                <li>Copy the <strong>Application (client) ID</strong> and <strong>Directory (tenant) ID</strong></li>
                <li>Go to <strong>Certificates & secrets → New client secret</strong> → copy the value</li>
                <li>Go to <strong>API permissions → Add a permission → Microsoft Graph → Application</strong></li>
                <li>Add <strong>Calendars.ReadWrite</strong> permission → <strong>Grant admin consent</strong></li>
                <li>Enter the email of the calendar owner (the person whose calendar to manage)</li>
              </ol>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Field label="Client ID (Application ID)" required>
              <input
                type="text"
                value={form.microsoft_client_id}
                onChange={(e) => setField('microsoft_client_id', e.target.value)}
                className="input font-mono text-xs"
                placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
              />
            </Field>
            <Field label="Tenant ID (Directory ID)" required>
              <input
                type="text"
                value={form.microsoft_tenant_id}
                onChange={(e) => setField('microsoft_tenant_id', e.target.value)}
                className="input font-mono text-xs"
                placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
              />
            </Field>
          </div>

          <Field label="Client Secret">
            {instance?.microsoft_secret_configured && !form.microsoft_client_secret && (
              <div className="flex items-center gap-2 mb-2 px-3 py-2 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">
                <span>✓</span>
                <span>Client secret saved. Enter a new value to replace it.</span>
              </div>
            )}
            <input
              type="password"
              value={form.microsoft_client_secret}
              onChange={(e) => setField('microsoft_client_secret', e.target.value)}
              className="input"
              placeholder={instance?.microsoft_secret_configured ? '(leave blank to keep existing secret)' : 'Paste your client secret here'}
            />
          </Field>

          <Field label="Calendar Owner Email" required hint="The Microsoft 365 / Outlook email whose calendar you want to manage">
            <input
              type="email"
              value={form.microsoft_user_email}
              onChange={(e) => setField('microsoft_user_email', e.target.value)}
              className="input"
              placeholder="user@yourcompany.com"
            />
          </Field>
        </div>
      )}
    </div>
  )
}
