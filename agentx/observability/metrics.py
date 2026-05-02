from typing import Dict, Any

class MetricsSystem:
    """Collects real-time and historical execution metrics."""
    
    def __init__(self):
        self.metrics = {
            "total_nodes_executed": 0,
            "success_count": 0,
            "failure_count": 0,
            "rollback_count": 0,
            "repair_success_count": 0,
            "total_latency_sec": 0.0
        }

    def record_success(self, latency: float = 0.0):
        self.metrics["total_nodes_executed"] += 1
        self.metrics["success_count"] += 1
        self.metrics["total_latency_sec"] += latency

    def record_failure(self):
        self.metrics["total_nodes_executed"] += 1
        self.metrics["failure_count"] += 1

    def record_rollback(self):
        self.metrics["rollback_count"] += 1

    def record_repair(self):
        self.metrics["repair_success_count"] += 1

    def get_summary(self) -> Dict[str, Any]:
        total = max(self.metrics["total_nodes_executed"], 1)
        return {
            "success_rate": self.metrics["success_count"] / total,
            "rollback_count": self.metrics["rollback_count"],
            "repair_rate": self.metrics["repair_success_count"] / max(self.metrics["failure_count"], 1),
            "avg_latency": self.metrics["total_latency_sec"] / total
        }

metrics_system = MetricsSystem()

# We can wire this up to EventBus as well
from agentx.runtime.event_bus import bus, EVENTS
bus.subscribe(EVENTS["NODE_SUCCESS"], lambda n: metrics_system.record_success())
bus.subscribe(EVENTS["NODE_FAILED"], lambda n: metrics_system.record_failure())
bus.subscribe(EVENTS["ROLLBACK"], lambda n: metrics_system.record_rollback())
bus.subscribe(EVENTS["REPAIR"], lambda n: metrics_system.record_repair())
