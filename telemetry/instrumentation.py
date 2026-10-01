import time
import uuid
from typing import Any, Dict
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

class Instrumentation:
    def __init__(self, service_name: str = "agent-chaos", otlp_endpoint: str = "http://localhost:4317" , enable_otlp: bool = True) -> None:
        self.service_name = service_name
        self.otlp_endpoint = otlp_endpoint
        self.enable_otlp = enable_otlp

        self.resource = Resource.create({"service.name": self.service_name})
        self.provider = trace.TracerProvider(resource=self.resource)

        self._memory = InMemorySpanExporter()
        self.provider.add_span_processor(SimpleSpanProcessor(self._memory))

        if enable_otlp:
            self.provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(endpoint=self.otlp_endpoint, insecure=True)))

        trace.set_tracer_provider(self.provider)
        self.tracer = self.provider.get_tracer(service_name)

    def start_span(self, name: str, **attrs) -> trace.Span:
        span= self.tracer.start_span(name, attributes=attrs)
        if attrs:
            span.set_attributes(attrs)
        return span

    def end_span(self, span: trace.Span, status: str = "OK", **attrs) -> None:
        if attrs:
            span.set_attributes(attrs)
        span.set_status(trace.Status(status))
        span.end()


    def get_finished_spans(self) -> list:
        return self._memory.get_finished_spans()

