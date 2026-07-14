import time
import logging
from typing import Dict, Any

logger = logging.getLogger("airguard.telemetry")
logger.setLevel(logging.INFO)

class AgentTelemetry:
    """
    Captures exact operational metrics for the Investigation Agent.
    Guarantees every investigation is a highly observable and traceable event.
    """
    def __init__(self):
        self.metrics: Dict[str, Any] = {
            "session_duration_ms": 0.0,
            "skill_execution_latency_ms": 0.0,
            "llm_latency_ms": 0.0,
            "correlation_latency_ms": 0.0,
            "total_tokens": 0,
            "prompt_cost_usd": 0.0,
            "errors": 0,
            "planner_decisions": []
        }
        self._timers: Dict[str, float] = {}

    def start_timer(self, metric_name: str):
        """Starts a high-resolution timer for a specific span."""
        self._timers[metric_name] = time.perf_counter()

    def stop_timer(self, metric_name: str):
        """Stops the timer and accumulates the elapsed latency in milliseconds."""
        if metric_name in self._timers:
            elapsed = (time.perf_counter() - self._timers[metric_name]) * 1000
            metric_key = f"{metric_name}_latency_ms"
            if metric_key not in self.metrics:
                self.metrics[metric_key] = 0.0
            self.metrics[metric_key] += elapsed
            del self._timers[metric_name]

    def record_llm_call(self, tokens_used: int, cost: float):
        """Tracks the financial and computational cost of the LLM wrapper."""
        self.metrics["total_tokens"] += tokens_used
        self.metrics["prompt_cost_usd"] += cost

    def record_planner_decision(self, intent: str, skills_selected: list):
        """Provides absolute traceability for *why* specific skills were run."""
        self.metrics["planner_decisions"].append({
            "intent": intent,
            "skills_selected": skills_selected,
            "timestamp": time.time()
        })
        
    def record_error(self):
        """Tracks hallucination or execution faults."""
        self.metrics["errors"] += 1

    def emit(self) -> Dict[str, Any]:
        """Flushes the metrics to standard output or a tracing backend (e.g., Datadog, X-Ray)."""
        logger.info(f"[TELEMETRY] AirGuard Agent Run: {self.metrics}")
        return self.metrics
