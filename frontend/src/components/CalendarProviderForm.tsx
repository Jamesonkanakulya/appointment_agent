import { useState } from 'react'
import { ChevronDown, ChevronUp, ExternalLink } from 'lucide-react'
import { Field } from './InstanceSettings'
import type { Instance } from '../api/client'

interface Props {
  form: Record<string, any>
  setField: (key: string, value: any) => void
  instance: Instance | null
}

export default function CalendarProviderForm({ form, setField, instance }: Props) {
  const [showGuide, setShowGuide] = useState(false)

  return (
    <div className="space-y-6">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <button
          type="button"
          onClick={() => setShowGuide(!showGuide)}
          className="w-full flex items-center justify-between text-sm font-medium text-blue-800"
        >
          <span>📖 Cal.com Setup Guide</span>
          {showGuide ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>
        {showGuide && (
          <ol className="mt-3 text-sm text-blue-700 space-y-2 list-decimal list-inside">
            <li>
              Go to{' '}
              <a
                href="https://cal.com/settings/developer/api-keys"
                target="_blank"
                rel="noreferrer"
                className="underline inline-flex items-center gap-1"
              >
                cal.com → Settings → Developer → API Keys <ExternalLink size={12} />
              </a>
              {' '}→ click <strong>Add</strong> → copy the key
            </li>
            <li>
              Go to{' '}
              <a
                href="https://cal.com/event-types"
                target="_blank"
                rel="noreferrer"
                className="underline inline-flex items-center gap-1"
              >
                cal.com → Event Types <ExternalLink size={12} />
              </a>
              {' '}→ open the event type you want to use
            </li>
            <li>
              Look at the URL — it ends with{' '}
              <code className="bg-blue-100 px-1 rounded">/event-types/<strong>12345</strong></code>{' '}
              — that number is your Event Type ID
            </li>
            <li>Paste both values below and save</li>
          </ol>
        )}
      </div>

      <Field
        label="Cal.com API Key"
        hint={
          instance?.calcom_api_key_configured
            ? '✓ API key is saved — paste a new key to replace it'
            : 'Required — create one at cal.com → Settings → API Keys'
        }
      >
        {instance?.calcom_api_key_configured && !form.calcom_api_key && (
          <div className="flex items-center gap-2 mb-2 px-3 py-2 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">
            <span>✓</span>
            <span>API key saved. Paste a new key below to replace.</span>
          </div>
        )}
        <input
          type="password"
          value={form.calcom_api_key || ''}
          onChange={(e) => setField('calcom_api_key', e.target.value)}
          className="input font-mono text-xs"
          placeholder={
            instance?.calcom_api_key_configured
              ? '(leave blank to keep existing key)'
              : 'cal_live_xxxxxxxxxxxxxxxx'
          }
        />
      </Field>

      <Field
        label="Event Type ID"
        hint="Numeric ID from the Cal.com event type URL (e.g., 12345)"
        required
      >
        <input
          type="number"
          value={form.calcom_event_type_id || ''}
          onChange={(e) => setField('calcom_event_type_id', e.target.value ? parseInt(e.target.value) : '')}
          className="input"
          placeholder="12345"
          min={1}
        />
      </Field>
    </div>
  )
}
