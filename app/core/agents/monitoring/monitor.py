import threading
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Set

from .metrics import AgentMetrics, Metric, MetricType, MetricValue


class MonitoringManager:
    """Manager for collecting and accessing agent metrics"""

    def __init__(self):
        self._agent_metrics: Dict[str, AgentMetrics] = {}
        self._lock = threading.Lock()
        self._registered_agents: Set[str] = set()

    def register_agent(
        self, agent_id: str, agent_type: str = "unknown"
    ) -> AgentMetrics:
        """Register an agent for monitoring"""
        with self._lock:
            if agent_id not in self._agent_metrics:
                metrics = AgentMetrics(agent_id=agent_id, agent_type=agent_type)

                # Register default metrics
                for metric_name, config in DEFAULT_METRICS.items():
                    metrics.register_metric(
                        name=metric_name,
                        type=config["type"],
                        description=config["description"],
                        unit=config["unit"],
                    )

                self._agent_metrics[agent_id] = metrics
                self._registered_agents.add(agent_id)
            return self._agent_metrics[agent_id]

    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent from monitoring"""
        with self._lock:
            if agent_id in self._agent_metrics:
                del self._agent_metrics[agent_id]
                self._registered_agents.remove(agent_id)

    def get_agent_metrics(self, agent_id: str) -> Optional[AgentMetrics]:
        """Get metrics for a specific agent"""
        return self._agent_metrics.get(agent_id)

    def get_all_metrics(self) -> Dict[str, Dict[str, List[MetricValue]]]:
        """Get all metrics for all agents"""
        result = {}
        with self._lock:
            for agent_id, metrics in self._agent_metrics.items():
                result[agent_id] = metrics.get_all_metrics()
        return result

    def get_metric_by_name(self, metric_name: str) -> Dict[str, List[MetricValue]]:
        """Get a specific metric across all agents"""
        result = {}
        with self._lock:
            for agent_id, metrics in self._agent_metrics.items():
                metric = metrics.get_metric(metric_name)
                if metric:
                    result[agent_id] = metric.values
        return result

    def get_active_agents(self) -> Set[str]:
        """Get set of currently registered agents"""
        return self._registered_agents.copy()


# Global monitoring manager instance
_monitor_manager = MonitoringManager()


def get_monitor_manager() -> MonitoringManager:
    """Get the global monitoring manager instance"""
    return _monitor_manager


# Common metric names
MESSAGES_PROCESSED = "messages_processed"
MESSAGES_SENT = "messages_sent"
PROCESSING_TIME = "processing_time"
QUEUE_SIZE = "queue_size"
MEMORY_USAGE = "memory_usage"
CPU_USAGE = "cpu_usage"
AGENT_STATUS = "agent_status"
ERROR_COUNT = "error_count"

# Default metrics configuration
DEFAULT_METRICS = {
    MESSAGES_PROCESSED: {
        "type": MetricType.COUNTER,
        "description": "Number of messages processed by the agent",
        "unit": "messages",
    },
    MESSAGES_SENT: {
        "type": MetricType.COUNTER,
        "description": "Number of messages sent by the agent",
        "unit": "messages",
    },
    PROCESSING_TIME: {
        "type": MetricType.HISTOGRAM,
        "description": "Time taken to process messages",
        "unit": "seconds",
    },
    QUEUE_SIZE: {
        "type": MetricType.GAUGE,
        "description": "Current size of the agent's message queue",
        "unit": "messages",
    },
    MEMORY_USAGE: {
        "type": MetricType.GAUGE,
        "description": "Memory usage of the agent",
        "unit": "bytes",
    },
    CPU_USAGE: {
        "type": MetricType.GAUGE,
        "description": "CPU usage of the agent",
        "unit": "percent",
    },
    AGENT_STATUS: {
        "type": MetricType.GAUGE,
        "description": "Current status of the agent",
        "unit": "status",
    },
    ERROR_COUNT: {
        "type": MetricType.COUNTER,
        "description": "Number of errors encountered by the agent",
        "unit": "errors",
    },
}
