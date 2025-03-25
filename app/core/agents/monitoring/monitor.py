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

    def register_agent(self, agent_id: str) -> AgentMetrics:
        """Register an agent for monitoring"""
        with self._lock:
            if agent_id not in self._agent_metrics:
                self._agent_metrics[agent_id] = AgentMetrics()
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
                    result[agent_id] = metric.get_values()
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
    MESSAGES_PROCESSED: MetricType.COUNTER,
    MESSAGES_SENT: MetricType.COUNTER,
    PROCESSING_TIME: MetricType.HISTOGRAM,
    QUEUE_SIZE: MetricType.GAUGE,
    MEMORY_USAGE: MetricType.GAUGE,
    CPU_USAGE: MetricType.GAUGE,
    AGENT_STATUS: MetricType.GAUGE,
    ERROR_COUNT: MetricType.COUNTER,
}
