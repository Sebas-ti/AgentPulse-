export interface SpanItem {
  id: string
  trace_id: string
  parent_span_id: string | null
  kind: 'llm' | 'retrieval' | 'tool' | 'agent' | 'guardrail' | string
  name: string
  started_at: string
  duration_ms: number
  provider: string | null
  model: string | null
  input_tokens: number
  output_tokens: number
  cost_usd: string | number | null
  input: unknown
  output: unknown
  attributes: Record<string, unknown>
}

export interface TraceItem {
  id: string
  project_id: string
  environment_id: string
  session_id: string | null
  started_at: string
  duration_ms: number
  status: 'ok' | 'error' | string
  input_tokens: number
  output_tokens: number
  cost_usd: string | number | null
  feedback: number | null
}

export interface TraceDetail {
  trace: TraceItem
  spans: SpanItem[]
}
