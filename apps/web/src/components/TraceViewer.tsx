import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { TraceDetail, TraceItem } from '../types.ts'
import { TraceWaterfall } from './TraceWaterfall.tsx'
import { Activity, Clock, CheckCircle2, AlertTriangle, RefreshCw, Eye } from 'lucide-react'

async function fetchTraces(envFilter: string | null): Promise<TraceItem[]> {
  const url = envFilter ? `/v1/traces?environment=${envFilter}` : '/v1/traces'
  const res = await fetch(url)
  if (!res.ok) {
    throw new Error('Error al obtener la lista de trazas')
  }
  return res.json() as Promise<TraceItem[]>
}

async function fetchTraceDetail(traceId: string): Promise<TraceDetail> {
  const res = await fetch(`/v1/traces/${traceId}`)
  if (!res.ok) {
    throw new Error('Error al obtener el detalle de la traza')
  }
  return res.json() as Promise<TraceDetail>
}

export function TraceViewer(): React.JSX.Element {
  const [selectedEnv, setSelectedEnv] = useState<string | null>(null)
  const [selectedTraceId, setSelectedTraceId] = useState<string | null>(null)

  const {
    data: traces,
    isLoading,
    refetch,
    isFetching,
  } = useQuery<TraceItem[]>({
    queryKey: ['traces', selectedEnv],
    queryFn: () => fetchTraces(selectedEnv),
    refetchInterval: 5000,
  })

  // Select first trace automatically if none selected
  const activeTraceId = selectedTraceId ?? traces?.[0]?.id ?? null

  const { data: detailData, isLoading: isDetailLoading } = useQuery<TraceDetail>({
    queryKey: ['trace-detail', activeTraceId],
    queryFn: () => fetchTraceDetail(activeTraceId!),
    enabled: Boolean(activeTraceId),
  })

  return (
    <div className="flex flex-col gap-6">
      {/* Filters and controls */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-slate-900/70 border border-slate-800">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-400">Ambiente:</span>
          <div className="inline-flex rounded-lg bg-slate-950 p-1 border border-slate-800">
            <button
              onClick={() => { setSelectedEnv(null) }}
              className={`px-3 py-1 text-xs rounded-md font-medium transition-colors ${
                selectedEnv === null
                  ? 'bg-indigo-600 text-white shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Todos
            </button>
            <button
              onClick={() => { setSelectedEnv('qa') }}
              className={`px-3 py-1 text-xs rounded-md font-medium transition-colors ${
                selectedEnv === 'qa'
                  ? 'bg-indigo-600 text-white shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              QA
            </button>
            <button
              onClick={() => { setSelectedEnv('prod') }}
              className={`px-3 py-1 text-xs rounded-md font-medium transition-colors ${
                selectedEnv === 'prod'
                  ? 'bg-indigo-600 text-white shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Producción
            </button>
          </div>
        </div>

        <button
          onClick={() => { void refetch() }}
          disabled={isFetching}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? 'animate-spin' : ''}`} />
          Refrescar trazas
        </button>
      </div>

      {/* Main layout: List + Waterfall */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left column: trace list */}
        <div className="lg:col-span-5 flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Activity className="h-4 w-4 text-indigo-400" />
              Trazas Recientes ({traces?.length || 0})
            </h3>
          </div>

          {isLoading && (
            <div className="p-8 text-center text-slate-400 text-xs bg-slate-900/40 rounded-xl border border-slate-800">
              <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2 text-indigo-400" />
              Cargando trazas...
            </div>
          )}

          {traces && traces.length === 0 && (
            <div className="p-8 text-center text-slate-400 text-xs bg-slate-900/40 rounded-xl border border-slate-800">
              No se han recibido trazas aún. Ejecuta `examples/rag-agent` para generar trazas de prueba.
            </div>
          )}

          <div className="flex flex-col gap-2 max-h-[600px] overflow-y-auto pr-1">
            {traces?.map((t) => {
              const isSelected = t.id === activeTraceId
              return (
                <div
                  key={t.id}
                  onClick={() => { setSelectedTraceId(t.id) }}
                  className={`p-3.5 rounded-xl border text-xs cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-indigo-950/40 border-indigo-500/80 shadow-md shadow-indigo-950/40'
                      : 'bg-slate-900/50 border-slate-800/80 hover:bg-slate-800/40'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-mono text-slate-300 font-semibold truncate max-w-[180px]">
                      {t.id.slice(0, 13)}...
                    </span>
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium ${
                        t.status === 'ok'
                          ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                          : 'bg-red-950 text-red-400 border border-red-800'
                      }`}
                    >
                      {t.status === 'ok' ? (
                        <CheckCircle2 className="h-3 w-3" />
                      ) : (
                        <AlertTriangle className="h-3 w-3" />
                      )}
                      {t.status}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-slate-400 text-[11px]">
                    <span className="flex items-center gap-1 font-mono">
                      <Clock className="h-3 w-3" />
                      {t.duration_ms} ms
                    </span>
                    <span className="font-mono">
                      {t.input_tokens + t.output_tokens} tokens
                    </span>
                    <span className="font-mono text-emerald-400 font-semibold">
                      {t.cost_usd ? `$${Number(t.cost_usd).toFixed(6)}` : '—'}
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Right column: Trace details waterfall */}
        <div className="lg:col-span-7 flex flex-col gap-3">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Eye className="h-4 w-4 text-indigo-400" />
            Detalle de Ejecución y Spans
          </h3>

          {isDetailLoading && (
            <div className="p-12 text-center text-slate-400 text-xs bg-slate-900/40 rounded-xl border border-slate-800">
              <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2 text-indigo-400" />
              Cargando árbol de spans...
            </div>
          )}

          {detailData && (
            <TraceWaterfall trace={detailData.trace} spans={detailData.spans} />
          )}

          {!activeTraceId && !isDetailLoading && (
            <div className="p-12 text-center text-slate-400 text-xs bg-slate-900/40 rounded-xl border border-slate-800">
              Selecciona una traza de la lista para ver su cascada de ejecución.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
