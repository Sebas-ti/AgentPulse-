import React, { useState } from 'react'
import { SpanItem, TraceItem } from '../types.ts'
import { ChevronRight, ChevronDown, Cpu, Database, Wrench, Shield, Bot, Coins } from 'lucide-react'

interface TraceWaterfallProps {
  trace: TraceItem
  spans: SpanItem[]
}

function getKindIcon(kind: string): React.JSX.Element {
  switch (kind) {
    case 'llm':
      return <Cpu className="h-3.5 w-3.5 text-purple-400" />
    case 'retrieval':
      return <Database className="h-3.5 w-3.5 text-emerald-400" />
    case 'tool':
      return <Wrench className="h-3.5 w-3.5 text-amber-400" />
    case 'guardrail':
      return <Shield className="h-3.5 w-3.5 text-blue-400" />
    default:
      return <Bot className="h-3.5 w-3.5 text-indigo-400" />
  }
}

function getKindBadgeClass(kind: string): string {
  switch (kind) {
    case 'llm':
      return 'bg-purple-950/70 text-purple-300 border-purple-800/60'
    case 'retrieval':
      return 'bg-emerald-950/70 text-emerald-300 border-emerald-800/60'
    case 'tool':
      return 'bg-amber-950/70 text-amber-300 border-amber-800/60'
    case 'guardrail':
      return 'bg-blue-950/70 text-blue-300 border-blue-800/60'
    default:
      return 'bg-indigo-950/70 text-indigo-300 border-indigo-800/60'
  }
}

export function TraceWaterfall({ trace, spans }: TraceWaterfallProps): React.JSX.Element {
  const [expandedSpanId, setExpandedSpanId] = useState<string | null>(spans[0]?.id || null)

  const maxDuration = Math.max(trace.duration_ms, ...spans.map((s) => s.duration_ms), 1)

  return (
    <div className="flex flex-col gap-4">
      {/* Trace summary header */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4 bg-slate-900/90 rounded-xl border border-slate-800">
        <div>
          <span className="text-xs text-slate-400">Duración Total</span>
          <p className="text-sm font-semibold text-white font-mono mt-0.5">{trace.duration_ms} ms</p>
        </div>
        <div>
          <span className="text-xs text-slate-400">Tokens E/S</span>
          <p className="text-sm font-semibold text-slate-200 font-mono mt-0.5">
            {trace.input_tokens} / {trace.output_tokens}
          </p>
        </div>
        <div>
          <span className="text-xs text-slate-400">Costo Estimado</span>
          <p className="text-sm font-semibold text-emerald-400 font-mono mt-0.5 flex items-center gap-1">
            <Coins className="h-3.5 w-3.5" />
            {trace.cost_usd ? `$${Number(trace.cost_usd).toFixed(6)}` : 'Sin precio'}
          </p>
        </div>
        <div>
          <span className="text-xs text-slate-400">Sesión</span>
          <p className="text-sm font-semibold text-slate-300 truncate mt-0.5" title={trace.session_id || 'N/A'}>
            {trace.session_id || 'N/A'}
          </p>
        </div>
      </div>

      {/* Spans waterfall list */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden">
        <div className="px-4 py-2.5 bg-slate-950/60 border-b border-slate-800 text-xs font-semibold text-slate-400 flex items-center justify-between">
          <span>Árbol de Spans ({spans.length})</span>
          <span>Línea de Tiempo</span>
        </div>

        <div className="divide-y divide-slate-800/60">
          {spans.map((s) => {
            const isExpanded = expandedSpanId === s.id
            const widthPct = Math.min(100, Math.max(4, (s.duration_ms / maxDuration) * 100))

            return (
              <div key={s.id} className="flex flex-col hover:bg-slate-800/20 transition-colors">
                <div
                  onClick={() => {
                    setExpandedSpanId(isExpanded ? null : s.id)
                  }}
                  className="px-4 py-3 flex items-center justify-between cursor-pointer gap-4 text-xs"
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    {isExpanded ? (
                      <ChevronDown className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                    ) : (
                      <ChevronRight className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                    )}
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium border ${getKindBadgeClass(
                        s.kind,
                      )}`}
                    >
                      {getKindIcon(s.kind)}
                      {s.kind}
                    </span>
                    <span className="font-semibold text-slate-200 truncate">{s.name}</span>
                    {s.model && (
                      <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 text-[10px] font-mono">
                        {s.model}
                      </span>
                    )}
                  </div>

                  {/* Waterfall bar */}
                  <div className="w-48 sm:w-64 flex items-center gap-2 shrink-0">
                    <div className="flex-1 bg-slate-950 rounded-full h-2 overflow-hidden">
                      <div
                        className="bg-indigo-500 h-full rounded-full"
                        style={{ width: `${widthPct}%` }}
                      />
                    </div>
                    <span className="w-14 text-right font-mono text-slate-300 text-[11px]">
                      {s.duration_ms} ms
                    </span>
                  </div>
                </div>

                {/* Expanded details */}
                {isExpanded && (
                  <div className="px-6 py-4 bg-slate-950/80 border-t border-slate-800/80 flex flex-col gap-3 text-xs">
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-slate-400 pb-2 border-b border-slate-900">
                      <div>
                        <span>Tokens Entrada:</span>{' '}
                        <strong className="text-slate-200 font-mono">{s.input_tokens}</strong>
                      </div>
                      <div>
                        <span>Tokens Salida:</span>{' '}
                        <strong className="text-slate-200 font-mono">{s.output_tokens}</strong>
                      </div>
                      <div>
                        <span>Costo Span:</span>{' '}
                        <strong className="text-emerald-400 font-mono">
                          {s.cost_usd ? `$${Number(s.cost_usd).toFixed(6)}` : 'N/A'}
                        </strong>
                      </div>
                      <div>
                        <span>Proveedor:</span>{' '}
                        <strong className="text-slate-200">{s.provider || 'N/A'}</strong>
                      </div>
                    </div>

                    {s.input !== null && s.input !== undefined && (
                      <div>
                        <span className="text-slate-400 font-medium block mb-1">Entrada (Input):</span>
                        <pre className="p-2.5 rounded-lg bg-slate-900 text-slate-300 font-mono text-[11px] overflow-x-auto max-h-36">
                          {typeof s.input === 'object'
                            ? JSON.stringify(s.input, null, 2)
                            : String(s.input)}
                        </pre>
                      </div>
                    )}

                    {s.output !== null && s.output !== undefined && (
                      <div>
                        <span className="text-slate-400 font-medium block mb-1">Salida (Output):</span>
                        <pre className="p-2.5 rounded-lg bg-slate-900 text-slate-300 font-mono text-[11px] overflow-x-auto max-h-36">
                          {typeof s.output === 'object'
                            ? JSON.stringify(s.output, null, 2)
                            : String(s.output)}
                        </pre>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
