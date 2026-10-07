"""AgentPulse SDK and CLI."""

from pkgutil import extend_path

from agentpulse.sdk import AgentPulse, SpanContext, TraceContext, get_client, span, trace

__path__ = extend_path(__path__, __name__)
__version__ = "0.1.0"

__all__ = [
    "AgentPulse",
    "SpanContext",
    "TraceContext",
    "get_client",
    "span",
    "trace",
]
