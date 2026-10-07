import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Activity, CheckCircle2, AlertCircle, RefreshCw, Layers, GitFork } from 'lucide-react'
import { TraceViewer } from './components/TraceViewer.tsx'

interface HealthData {
  status: string
  version: string
  environment: string
}

async function fetchHealth(): Promise<HealthData> {
  const response = await fetch('/healthz')
  if (!response.ok) {
    throw new Error('Error al conectar con la API de AgentPulse')
  }
  return response.json() as Promise<HealthData>
}

export function App(): React.JSX.Element {
  const [activeTab, setActiveTab] = useState<'traces' | 'health'>('traces')

  const { data, error, isLoading, refetch, isFetching } = useQuery<HealthData>({
    queryKey: ['health'],
    queryFn: fetchHealth,
  })

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-lg bg-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Activity className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-white">AgentPulse</h1>
            <p className="text-xs text-slate-400">Observabilidad, Evaluación y Guardrails para Agentes y RAG</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="inline-flex rounded-lg bg-slate-900 p-1 border border-slate-800">
            <button
              onClick={() => { setActiveTab('traces') }}
              className={`flex items-center gap-1.5 px-3 py-1 text-xs rounded-md font-medium transition-colors ${
                activeTab === 'traces'
                  ? 'bg-indigo-600 text-white shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <GitFork className="h-3.5 w-3.5" />
              Visor de Trazas
            </button>
            <button
              onClick={() => { setActiveTab('health') }}
              className={`flex items-center gap-1.5 px-3 py-1 text-xs rounded-md font-medium transition-colors ${
                activeTab === 'health'
                  ? 'bg-indigo-600 text-white shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Layers className="h-3.5 w-3.5" />
              Estado
            </button>
          </div>
          <span className="hidden sm:inline-block text-xs px-2.5 py-1 rounded-full bg-slate-800 border border-slate-700 text-slate-300 font-mono">
            Fase 1 · Ingesta
          </span>
        </div>
      </header>

      <main className="flex-1 max-w-6xl w-full mx-auto p-6 md:p-8 flex flex-col gap-6">
        {activeTab === 'traces' ? (
          <TraceViewer />
        ) : (
          <section className="bg-slate-900/70 border border-slate-800 rounded-xl p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Layers className="h-5 w-5 text-indigo-400" />
                <h2 className="text-base font-semibold text-white">Estado de la Plataforma</h2>
              </div>
              <button
                onClick={() => { void refetch() }}
                disabled={isFetching}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors border border-slate-700 disabled:opacity-50"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? 'animate-spin' : ''}`} />
                Actualizar
              </button>
            </div>

            {isLoading && (
              <div className="p-8 text-center text-slate-400 text-sm">
                <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2 text-indigo-400" />
                Verificando estado del servicio API...
              </div>
            )}

            {error && (
              <div className="p-4 rounded-lg bg-red-950/40 border border-red-800/60 flex items-start gap-3 text-red-200">
                <AlertCircle className="h-5 w-5 text-red-400 shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-semibold">No se pudo contactar el backend</p>
                  <p className="text-xs text-red-300/80 mt-1">
                    Asegúrate de que la API esté levantada en el puerto 8000 o mediante `docker compose up`.
                  </p>
                </div>
              </div>
            )}

            {data && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 rounded-lg bg-slate-950/60 border border-slate-800">
                  <span className="text-xs text-slate-400 uppercase font-medium tracking-wider">Estado API</span>
                  <div className="flex items-center gap-2 mt-1">
                    <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                    <span className="text-base font-semibold text-emerald-400 capitalize">{data.status}</span>
                  </div>
                </div>
                <div className="p-4 rounded-lg bg-slate-950/60 border border-slate-800">
                  <span className="text-xs text-slate-400 uppercase font-medium tracking-wider">Versión</span>
                  <p className="text-base font-semibold text-slate-200 mt-1 font-mono">v{data.version}</p>
                </div>
                <div className="p-4 rounded-lg bg-slate-950/60 border border-slate-800">
                  <span className="text-xs text-slate-400 uppercase font-medium tracking-wider">Ambiente</span>
                  <p className="text-base font-semibold text-slate-200 mt-1 capitalize">{data.environment}</p>
                </div>
              </div>
            )}
          </section>
        )}
      </main>

      <footer className="border-t border-slate-900 py-4 px-6 text-center text-xs text-slate-500">
        AgentPulse v0.1.0 · Observabilidad y Auditoría de Agentes Conversacionales
      </footer>
    </div>
  )
}

export default App
