import pytest
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def sample_math_problems():
    """Sample math problems data for testing."""
    return {
        "topic": "algebra",
        "problems": [
            {
                "id": 1,
                "type": "word",
                "elements": [
                    {"kind": "text", "content": "Solve for x: 2x + 5 = 15"}
                ],
            },
            {
                "id": 2,
                "type": "formula",
                "elements": [
                    {"kind": "latex", "content": "x^2 + 2x + 1 = 0"}
                ],
            },
            {
                "id": 3,
                "type": "mixed",
                "elements": [
                    {"kind": "text", "content": "Simplify the expression:"},
                    {"kind": "latex", "content": "(x + 1)^2"},
                ],
            },
        ],
    }


@pytest.fixture
def sample_messages():
    """Sample chat messages for testing."""
    return [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"},
    ]