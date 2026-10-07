import { fireEvent, render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App.tsx'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
})

describe('App Component', () => {
  beforeEach(() => {
    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/healthz')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ status: 'ok', version: '0.1.0', environment: 'test' }),
        })
      }
      if (url.includes('/v1/traces')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([]),
        })
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({}),
      })
    })
  })

  it('renders AgentPulse header and traces viewer tab', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>,
    )

    expect(screen.getByText('AgentPulse')).toBeInTheDocument()
    expect(screen.getByText('Visor de Trazas')).toBeInTheDocument()
    expect(screen.getByText('Trazas Recientes (0)')).toBeInTheDocument()
  })

  it('switches to platform status tab upon clicking Estado', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>,
    )

    const statusButton = screen.getByText('Estado')
    fireEvent.click(statusButton)

    expect(screen.getByText('Estado de la Plataforma')).toBeInTheDocument()
  })
})
