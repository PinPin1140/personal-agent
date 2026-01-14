#!/usr/bin/env python3
"""Simple test script for model router functionality."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agent.model_router import ModelRouter


def test_router():
    """Test router registration and generation."""
    router = ModelRouter()

    # Test provider registration
    providers = router.list_providers()
    assert "dummy" in providers, "Dummy provider should be registered"
    assert "openai" in providers, "OpenAI provider should be registered"

    # Test generation returns string
    response = router.generate("Test prompt")
    assert isinstance(response, str), "Generate should return string"
    assert len(response) > 0, "Response should not be empty"

    print("✓ Provider registration test passed")
    print("✓ Generate method returns string test passed")
    print(f"✓ Response: {response}")


if __name__ == "__main__":
    test_router()
    print("\nAll tests passed!")