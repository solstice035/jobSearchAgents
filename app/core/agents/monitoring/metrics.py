from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List


class MetricType(Enum):
    """Types of metrics that can be collected"""

    COUNTER = "counter"  # Monotonically increasing value
    GAUGE = "gauge"  # Value that can go up and down
    HISTOGRAM = "histogram"  # Distribution of values
    SUMMARY = "summary"  # Statistical summary of values


@dataclass
class MetricValue:
    """Value of a metric at a point in time"""

    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class Metric:
    """Representation of a monitored metric"""

    name: str
    type: MetricType
    description: str
    unit: str
    values: List[MetricValue] = field(default_factory=list)

    def add_value(self, value: float, labels: Optional[Dict[str, str]] = None):
        """Add a new value to the metric"""
        self.values.append(
            MetricValue(timestamp=datetime.now(), value=value, labels=labels or {})
        )

        # Keep only last 1000 values
        if len(self.values) > 1000:
            self.values = self.values[-1000:]


@dataclass
class AgentMetrics:
    """Collection of metrics for an agent"""

    agent_id: str
    agent_type: str
    metrics: Dict[str, Metric] = field(default_factory=dict)

    def register_metric(
        self, name: str, type: MetricType, description: str, unit: str
    ) -> Metric:
        """Register a new metric"""
        metric = Metric(name=name, type=type, description=description, unit=unit)
        self.metrics[name] = metric
        return metric

    def record_value(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ):
        """Record a value for a metric"""
        if name in self.metrics:
            self.metrics[name].add_value(value, labels)

    def get_metric(self, name: str) -> Optional[Metric]:
        """Get a metric by name"""
        return self.metrics.get(name)

    def get_all_metrics(self) -> Dict[str, Metric]:
        """Get all metrics"""
        return self.metrics.copy()
