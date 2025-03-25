import json
import pytest
from pathlib import Path

from app.core.agents.monitoring import (
    MetricType,
    MetricValue,
    AgentMetrics,
    MESSAGES_PROCESSED,
    MESSAGES_SENT,
    PROCESSING_TIME,
    QUEUE_SIZE,
    DEFAULT_METRICS,
)


def test_metric_registration(monitor_manager):
    """Test metric registration and retrieval."""
    agent_id = "test_agent"
    metrics = monitor_manager.register_agent(agent_id)

    # Verify default metrics are registered
    for metric_name in DEFAULT_METRICS:
        assert metrics.get_metric(metric_name) is not None

    # Test custom metric registration
    metrics.register_metric(
        name="custom_metric",
        type=MetricType.COUNTER,
        description="Test custom metric",
        unit="count",
    )
    assert metrics.get_metric("custom_metric") is not None

    # Test metric type
    assert metrics.get_metric("custom_metric").type == MetricType.COUNTER


def test_metric_recording(monitor_manager):
    """Test recording metric values."""
    agent_id = "test_agent"
    metrics = monitor_manager.register_agent(agent_id)

    # Record some values
    metrics.record_value(MESSAGES_PROCESSED, 1)
    metrics.record_value(MESSAGES_PROCESSED, 1)
    metrics.record_value(QUEUE_SIZE, 5)

    # Check counter behavior
    messages_processed = metrics.get_metric(MESSAGES_PROCESSED)
    values = messages_processed.values
    assert len(values) == 2
    assert sum(v.value for v in values) == 2

    # Check gauge behavior
    queue_size = metrics.get_metric(QUEUE_SIZE)
    values = queue_size.values
    assert len(values) == 1
    assert values[-1].value == 5


def test_metric_history_limit(monitor_manager):
    """Test metric history size limit."""
    agent_id = "test_agent"
    metrics = monitor_manager.register_agent(agent_id)

    # Record more than the limit
    for i in range(1100):  # Limit is 1000
        metrics.record_value(MESSAGES_PROCESSED, 1)

    values = metrics.get_metric(MESSAGES_PROCESSED).values
    assert len(values) == 1000  # Should be capped at 1000


def test_metric_retrieval(monitor_manager):
    """Test retrieving metrics across agents."""
    # Register two agents
    agent1_metrics = monitor_manager.register_agent("agent1")
    agent2_metrics = monitor_manager.register_agent("agent2")

    # Record some values
    agent1_metrics.record_value(PROCESSING_TIME, 0.1)
    agent2_metrics.record_value(PROCESSING_TIME, 0.2)

    # Get metrics by name
    processing_times = monitor_manager.get_metric_by_name(PROCESSING_TIME)
    assert "agent1" in processing_times
    assert "agent2" in processing_times
    assert processing_times["agent1"][0].value == 0.1
    assert processing_times["agent2"][0].value == 0.2


def test_agent_cleanup(monitor_manager):
    """Test agent cleanup on unregistration."""
    agent_id = "test_agent"
    monitor_manager.register_agent(agent_id)

    assert agent_id in monitor_manager.get_active_agents()

    monitor_manager.unregister_agent(agent_id)
    assert agent_id not in monitor_manager.get_active_agents()
    assert monitor_manager.get_agent_metrics(agent_id) is None


@pytest.mark.asyncio
async def test_logging_output(temp_log_dir, configured_logging, test_agent):
    """Test logging output format and content."""
    log_file = Path(temp_log_dir) / "agent.log"

    # Generate some log entries
    test_agent.logger.info("Test message", {"extra_field": "test_value"})
    test_agent.logger.error("Error message", {"error_code": 500})

    # Read and parse log file
    with open(log_file, "r") as f:
        logs = [json.loads(line) for line in f]

    # Verify log structure
    assert len(logs) == 2

    info_log = logs[0]
    assert info_log["level"] == "INFO"
    assert info_log["message"] == "Test message"
    assert info_log["agent_id"] == test_agent.agent_id
    assert info_log["agent_type"] == test_agent.agent_type
    assert info_log["extra_fields"]["extra_field"] == "test_value"

    error_log = logs[1]
    assert error_log["level"] == "ERROR"
    assert error_log["message"] == "Error message"
    assert error_log["extra_fields"]["error_code"] == 500
