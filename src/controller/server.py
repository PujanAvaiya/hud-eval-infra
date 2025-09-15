from fastmcp import FastMCP, Context
import os

# (Optional) Observability via OpenTelemetry
try:
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
except Exception:  # otel is optional at runtime
    trace = None

mcp = FastMCP("my_env")

# ---- OTEL setup (only if endpoint is provided) ----
if trace and os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
    provider = TracerProvider(resource=Resource.create({"service.name": "my_env"}))
    provider.add_span_processor(BatchSpanProcessor(
        OTLPSpanExporter(endpoint=os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"])
    ))
    trace.set_tracer_provider(provider)
    tracer = trace.get_tracer(__name__)
else:
    class _NoSpan:
        def __enter__(self): return self
        def __exit__(self, *a): pass
    class _NoTracer:
        def start_as_current_span(self, *a, **k): return _NoSpan()
    tracer = _NoTracer()

def _get_counter(ctx: Context) -> int:
    return int(ctx.state.get("counter", 0))

def _set_counter(ctx: Context, v: int) -> None:
    ctx.state["counter"] = int(v)

@mcp.tool()
def setup(ctx: Context) -> str:
    """Reset environment to a known initial state."""
    _set_counter(ctx, 0)
    return "ok"

@mcp.tool()
def act(ctx: Context) -> str:
    """Advance environment by one deterministic step."""
    with tracer.start_as_current_span("act_step"):
        v = _get_counter(ctx) + 1
        _set_counter(ctx, v)
        return f"counter={v}"

@mcp.tool()
def evaluate(target: int = 4, ctx: Context = None) -> dict:
    """
    Standard evaluation result for HUD.
    done: boolean, reward: 0..1, info/content help dashboards.
    """
    c = _get_counter(ctx)
    done = c >= target
    reward = min(1.0, c / float(target)) if target > 0 else 0.0
    return {
        "done": done,
        "reward": reward,
        "info": {"counter": c, "target": target},
        "content": f"counter={c}, target={target}",
        "isError": False,
    }

def run():
    mcp.run()  # stdio

if __name__ == "__main__":
    run()
