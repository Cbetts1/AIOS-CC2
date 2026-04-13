"""pytest configuration and shared fixtures for the AI-OS test suite."""
import pytest
from aios.core.state_registry import StateRegistry


@pytest.fixture(autouse=True)
def reset_state_registry():
    """Reset the StateRegistry singleton before and after every test."""
    StateRegistry.reset()
    yield
    StateRegistry.reset()
