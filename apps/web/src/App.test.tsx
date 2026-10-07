import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
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
  it('renders AgentPulse header and platform status', () => {
    // Mock fetch for healthz
    globalThis.fetch = vi.fn().mockImplementation(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ status: 'ok', version: '0.1.0', environment: 'test' }),
      }),
    )

    render(
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>,
    )

    expect(screen.getByText('AgentPulse')).toBeInTheDocument()
    expect(screen.getByText('Estado de la Plataforma')).toBeInTheDocument()
  })
})
