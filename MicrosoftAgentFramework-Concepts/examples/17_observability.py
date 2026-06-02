# """
# 17 — Observability (OpenTelemetry Tracing & Metrics)
# ====================================================

# CONCEPT
# -------
# Production agents are non-deterministic and multi-step, so you MUST be able to
# see what happened: which tools were called, with what args, how long each model
# call took, token usage, and where it failed. MAF is instrumented with
# **OpenTelemetry** (the vendor-neutral standard), so every agent run, tool call,
# and workflow step can emit spans, metrics and logs to any OTel backend
# (console, Jaeger, Azure Monitor, Grafana, etc.).

# KEY API
# -------
# * `configure_otel_providers(enable_console_exporters=True)`  -> wire exporters
# * `enable_instrumentation()`                                 -> instrument MAF
# * `get_tracer()` / `create_processing_span(...)`             -> custom spans
# After that, just run agents normally — spans print to your console.

# Interview soundbite:
#   "MAF emits OpenTelemetry semantic-convention 'gen_ai' spans out of the box.
#    Turn on instrumentation and point an exporter at Jaeger/Azure Monitor to get
#    full traces of tool calls, latencies and token usage — essential for
#    debugging and SLOs in production."

# RUN
# ---
#     python examples/17_observability.py
# (You'll see structured OTel spans printed below the agent's answer.)
# """

# import asyncio

# from agent_framework import tool
# from agent_framework.observability import (
#     configure_otel_providers,
#     enable_instrumentation,
#     get_tracer,
# )

# from _shared import banner, build_chat_client


# @tool
# def roll_die(sides: int = 6) -> int:
#     """Roll a die with the given number of sides and return the result."""
#     import random

#     return random.randint(1, sides)


# async def main() -> None:
#     banner("17 — Observability (OpenTelemetry)")

#     # 1) Send all telemetry to the console (swap the exporter for Jaeger/Azure
#     #    Monitor/OTLP in production). enable_sensitive_data also logs prompts.
#     configure_otel_providers(enable_console_exporters=True, enable_sensitive_data=True)
#     enable_instrumentation()

#     agent = build_chat_client().as_agent(
#         name="DiceMaster",
#         instructions="You are a game master. Use the die tool when asked to roll.",
#         tools=[roll_die],
#     )

#     # 2) Wrap our own work in a custom span so it shows up in the trace too.
#     tracer = get_tracer()
#     with tracer.start_as_current_span("dice-demo"):
#         response = await agent.run("Roll a 20-sided die and tell me if I beat a 10.")

#     print("\nAGENT ANSWER:\n", response.text)
#     print(
#         "\n(Above/below you should see OpenTelemetry spans: the agent invocation,"
#         "\n the chat completion, and the roll_die tool call, with timings.)"
#     )


# if __name__ == "__main__":
#     asyncio.run(main())



"""
17 — Observability (OpenTelemetry Tracing & Metrics)
====================================================

CONCEPT
-------
Production agents are non-deterministic and multi-step, so you MUST be able to
see what happened: which tools were called, with what args, how long each model
call took, token usage, and where it failed. MAF is instrumented with
**OpenTelemetry** (the vendor-neutral standard), so every agent run, tool call,
and workflow step can emit spans, metrics and logs to any OTel backend
(console, Jaeger, Azure Monitor, Grafana, etc.).

KEY API
-------
* `configure_otel_providers(enable_console_exporters=True)`  -> wire exporters
* `enable_instrumentation()`                                 -> instrument MAF
* `get_tracer()` / `create_processing_span(...)`             -> custom spans
After that, just run agents normally — spans print to your console.

Interview soundbite:
  "MAF emits OpenTelemetry semantic-convention 'gen_ai' spans out of the box.
   Turn on instrumentation and point an exporter at Jaeger/Azure Monitor to get
   full traces of tool calls, latencies and token usage — essential for
   debugging and SLOs in production."

RUN
---
    python examples/17_observability.py
(You'll see structured OTel spans printed below the agent's answer.)
"""

import asyncio

from agent_framework import tool
from agent_framework.observability import (
    configure_otel_providers,
    enable_instrumentation,
    get_tracer,
)

from _shared import banner, build_chat_client

# ===========================================================================
# AZURE COSMOS DB TELEMETRY SINK (commented out — uncomment to enable)
# ===========================================================================
# There is no built-in OpenTelemetry exporter for Cosmos DB, so we implement a
# tiny custom SpanExporter (and LogExporter) that writes each span / log record
# as a JSON document into a Cosmos container. This runs ALONGSIDE the console
# exporter — the console keeps printing while Cosmos persists everything.
#
# Install deps:
#     pip install azure-cosmos opentelemetry-sdk
#
# Required imports for the Cosmos path:
# from opentelemetry.sdk.trace.export import (
#     SpanExporter,
#     SpanExportResult,
#     BatchSpanProcessor,
# )
# from opentelemetry.sdk._logs.export import (
#     LogExporter,
#     LogExportResult,
#     BatchLogRecordProcessor,
# )
# from opentelemetry.trace import get_tracer_provider
# from opentelemetry._logs import get_logger_provider
# from azure.cosmos import CosmosClient, PartitionKey
# # For AAD / Managed Identity instead of a key (recommended in prod):
# # from azure.identity import DefaultAzureCredential
#
#
# class CosmosSpanExporter(SpanExporter):
#     """Persists OTel spans (agent runs, chat completions, tool calls) to Cosmos DB."""
#
#     def __init__(self, endpoint: str, key: str, database: str, container: str):
#         # Key-based auth:
#         self._client = CosmosClient(endpoint, credential=key)
#         # AAD / Managed Identity (recommended):
#         # self._client = CosmosClient(endpoint, credential=DefaultAzureCredential())
#         db = self._client.create_database_if_not_exists(id=database)
#         self._container = db.create_container_if_not_exists(
#             id=container,
#             partition_key=PartitionKey(path="/trace_id"),
#         )
#
#     def export(self, spans) -> "SpanExportResult":
#         try:
#             for span in spans:
#                 ctx = span.get_span_context()
#                 trace_id = format(ctx.trace_id, "032x")
#                 span_id = format(ctx.span_id, "016x")
#                 start, end = span.start_time, span.end_time
#                 item = {
#                     # id must be unique within the partition; combine both ids.
#                     "id": f"{trace_id}-{span_id}",
#                     "trace_id": trace_id,          # partition key
#                     "span_id": span_id,
#                     "parent_span_id": (
#                         format(span.parent.span_id, "016x") if span.parent else None
#                     ),
#                     "name": span.name,
#                     "kind": str(span.kind),
#                     "start_time_ns": start,
#                     "end_time_ns": end,
#                     "duration_ms": ((end - start) / 1_000_000) if (start and end) else None,
#                     "status": str(span.status.status_code),
#                     # gen_ai.* attributes (model, tokens, tool args) live here:
#                     "attributes": dict(span.attributes or {}),
#                     "events": [
#                         {
#                             "name": e.name,
#                             "timestamp_ns": e.timestamp,
#                             "attributes": dict(e.attributes or {}),
#                         }
#                         for e in span.events
#                     ],
#                 }
#                 self._container.upsert_item(item)
#             return SpanExportResult.SUCCESS
#         except Exception:  # never let telemetry crash the agent
#             return SpanExportResult.FAILURE
#
#     def shutdown(self) -> None:
#         pass
#
#
# class CosmosLogExporter(LogExporter):
#     """Persists OTel log records to Cosmos DB (use if you want logs, not just spans)."""
#
#     def __init__(self, endpoint: str, key: str, database: str, container: str):
#         self._client = CosmosClient(endpoint, credential=key)
#         db = self._client.create_database_if_not_exists(id=database)
#         self._container = db.create_container_if_not_exists(
#             id=container,
#             partition_key=PartitionKey(path="/trace_id"),
#         )
#
#     def export(self, batch) -> "LogExportResult":
#         try:
#             for log_data in batch:
#                 record = log_data.log_record
#                 trace_id = format(record.trace_id, "032x") if record.trace_id else "none"
#                 item = {
#                     "id": f"{trace_id}-{record.observed_timestamp}",
#                     "trace_id": trace_id,          # partition key
#                     "timestamp_ns": record.timestamp,
#                     "severity": str(record.severity_text),
#                     "body": str(record.body),
#                     "attributes": dict(record.attributes or {}),
#                 }
#                 self._container.upsert_item(item)
#             return LogExportResult.SUCCESS
#         except Exception:
#             return LogExportResult.FAILURE
#
#     def shutdown(self) -> None:
#         pass
# ===========================================================================


@tool
def roll_die(sides: int = 6) -> int:
    """Roll a die with the given number of sides and return the result."""
    import random

    return random.randint(1, sides)


async def main() -> None:
    banner("17 — Observability (OpenTelemetry)")

    # 1) Send all telemetry to the console (swap the exporter for Jaeger/Azure
    #    Monitor/OTLP in production). enable_sensitive_data also logs prompts.
    configure_otel_providers(enable_console_exporters=True, enable_sensitive_data=True)
    enable_instrumentation()

    # -----------------------------------------------------------------------
    # 1b) ALSO persist telemetry to Azure Cosmos DB (commented out).
    #     MAF already created the OTel providers above; we just attach extra
    #     processors that fan telemetry out to our Cosmos exporters as well.
    #     The console output above stays exactly the same.
    # -----------------------------------------------------------------------
    # import os
    #
    # cosmos_endpoint = os.environ["COSMOS_ENDPOINT"]   # e.g. https://<acct>.documents.azure.com:443/
    # cosmos_key = os.environ["COSMOS_KEY"]
    #
    # # Traces (spans) -> Cosmos
    # span_exporter = CosmosSpanExporter(
    #     endpoint=cosmos_endpoint,
    #     key=cosmos_key,
    #     database="agent-telemetry",
    #     container="spans",
    # )
    # get_tracer_provider().add_span_processor(BatchSpanProcessor(span_exporter))
    #
    # # Logs -> Cosmos (optional)
    # log_exporter = CosmosLogExporter(
    #     endpoint=cosmos_endpoint,
    #     key=cosmos_key,
    #     database="agent-telemetry",
    #     container="logs",
    # )
    # get_logger_provider().add_log_record_processor(
    #     BatchLogRecordProcessor(log_exporter)
    # )
    # -----------------------------------------------------------------------

    agent = build_chat_client().as_agent(
        name="DiceMaster",
        instructions="You are a game master. Use the die tool when asked to roll.",
        tools=[roll_die],
    )

    # 2) Wrap our own work in a custom span so it shows up in the trace too.
    tracer = get_tracer()
    with tracer.start_as_current_span("dice-demo"):
        response = await agent.run("Roll a 20-sided die and tell me if I beat a 10.")

    print("\nAGENT ANSWER:\n", response.text)
    print(
        "\n(Above/below you should see OpenTelemetry spans: the agent invocation,"
        "\n the chat completion, and the roll_die tool call, with timings.)"
    )

    # -----------------------------------------------------------------------
    # If the Cosmos sink is enabled, flush before exit so buffered spans/logs
    # are written (BatchSpanProcessor batches asynchronously):
    # -----------------------------------------------------------------------
    # get_tracer_provider().force_flush()
    # get_logger_provider().force_flush()


if __name__ == "__main__":
    asyncio.run(main())