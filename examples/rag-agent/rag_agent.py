"""Sample RAG Agent instrumented with AgentPulse SDK."""

import time

from agentpulse.sdk import AgentPulse


def simulate_rag_agent(user_query: str) -> str:
    """Run simulated RAG flow instrumented with AgentPulse."""
    client = AgentPulse(
        api_key="ap_qa_devkey12345",
        base_url="http://localhost:8000",
        flush_interval=0.5,
    )

    print(f"[RAG Agent] Starting query execution: '{user_query}'")

    with client.trace(name="RAG Assistant Interaction", session_id="session-user-101") as trace_ctx:
        # 1. Retrieval Span
        print("[RAG Agent] Step 1: Retrieving relevant knowledge base documents...")
        with client.span(
            name="Vector Store Retrieval",
            kind="retrieval",
            provider="vector_db",
            input_data={"query": user_query},
        ) as retrieve_span:
            time.sleep(0.08)  # simulate vector search latency
            documents = [
                {
                    "id": "doc_1",
                    "text": (
                        "AgentPulse monitors latency, token cost, hallucinations and guardrails."
                    ),
                },
                {
                    "id": "doc_2",
                    "text": (
                        "Phase 1 implements trace and span ingestion with hierarchical trees."
                    ),
                },
            ]
            retrieve_span.attributes["documents"] = documents
            retrieve_span.record_usage(input_tokens=25, output_tokens=0)
            retrieve_span.output = {"count": len(documents), "top_score": 0.94}

        # 2. Guardrail Check Span
        print("[RAG Agent] Step 2: Running input guardrails & moderation...")
        with client.span(
            name="Input Guardrail Moderation",
            kind="guardrail",
            provider="agentpulse_guard",
            input_data={"text": user_query},
        ) as guard_span:
            time.sleep(0.02)
            guard_span.record_usage(input_tokens=30, output_tokens=5)
            guard_span.output = {"passed": True, "category": "safe"}

        # 3. LLM Generation Span
        print("[RAG Agent] Step 3: Generating answer using LLM...")
        with client.span(
            name="OpenAI Chat Completion",
            kind="llm",
            model="gpt-4o-mini",
            provider="openai",
            input_data={"messages": [{"role": "user", "content": user_query}]},
        ) as llm_span:
            time.sleep(0.15)  # simulate LLM response time
            answer = "AgentPulse registra trazas completas con cálculo de tokens y costo en USD."
            llm_span.record_usage(input_tokens=180, output_tokens=65)
            llm_span.output = {"role": "assistant", "content": answer}

    print("[RAG Agent] Flushing trace to AgentPulse API...")
    client.flush()
    time.sleep(0.5)
    print(f"[RAG Agent] Completed successfully! Generated Trace ID: {trace_ctx.id}")
    return answer


if __name__ == "__main__":
    simulate_rag_agent("¿Cómo funciona la ingesta y monitoreo en AgentPulse?")
