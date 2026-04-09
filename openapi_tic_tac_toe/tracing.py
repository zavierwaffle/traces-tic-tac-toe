from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

def tracing_configure():
    attributes = {}
    attributes[SERVICE_NAME] = "tictactoe-app"

    resource = Resource.create(attributes)
    provider = TracerProvider(resource = resource)

    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter("http://tempo:4318/v1/traces")))
    trace.set_tracer_provider(provider)
