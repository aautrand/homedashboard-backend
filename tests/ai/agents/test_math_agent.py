import json
from unittest.mock import MagicMock

import pytest


class TestMathAgent:
    """Tests for the MathAgent class."""

    def test_init_with_client(self):
        """Test MathAgent initializes with provided client."""
        from dashboard.src.ai.agents.math_agent import MathAgent

        mock_client = MagicMock()
        agent = MathAgent(client=mock_client)

        assert agent.client is mock_client

    def test_generate_problems_success(self):
        """Test generate_problems returns parsed JSON on valid response."""
        from dashboard.src.ai.agents.math_agent import MathAgent

        mock_client = MagicMock()
        mock_client.generate_response.return_value = json.dumps(
            {
                "topic": "algebra",
                "problems": [
                    {
                        "id": 1,
                        "type": "word",
                        "elements": [
                            {"kind": "text", "content": "Solve for x: 2x + 5 = 15"}
                        ],
                    }
                ],
            }
        )

        agent = MathAgent(client=mock_client)
        result = agent.generate_problems("Generate 1 algebra problem")

        assert result["topic"] == "algebra"
        assert len(result["problems"]) == 1
        assert result["problems"][0]["id"] == 1
        assert result["problems"][0]["type"] == "word"

    def test_generate_problems_removes_json_markdown_delimiters(self):
        """Test generate_problems strips ```json and ``` delimiters."""
        from dashboard.src.ai.agents.math_agent import MathAgent

        mock_client = MagicMock()
        # Response wrapped in markdown code block
        mock_client.generate_response.return_value = (
            '```json\n{"topic": "geometry", "problems": []}\n```'
        )

        agent = MathAgent(client=mock_client)
        result = agent.generate_problems("Generate geometry problems")

        assert result["topic"] == "geometry"
        assert result["problems"] == []

    def test_generate_problems_removes_plain_json_word(self):
        """Test generate_problems removes stray 'json' word from response."""
        from dashboard.src.ai.agents.math_agent import MathAgent

        mock_client = MagicMock()
        # Response with 'json' prefix
        mock_client.generate_response.return_value = (
            'json{"topic": "calculus", "problems": []}'
        )

        agent = MathAgent(client=mock_client)
        result = agent.generate_problems("Generate calculus problems")

        assert result["topic"] == "calculus"

    def test_generate_problems_calls_client_with_correct_params(self):
        """Test generate_problems calls client with correct model and prompt."""
        from dashboard.src.ai.agents.math_agent import MathAgent
        from dashboard.src.ai.prompts import math_problem_generator_prompt

        mock_client = MagicMock()
        mock_client.generate_response.return_value = '{"topic": "test", "problems": []}'

        agent = MathAgent(client=mock_client)
        agent.generate_problems("5 problems about fractions")

        mock_client.generate_response.assert_called_once_with(
            "5 problems about fractions", instructions=math_problem_generator_prompt
        )

    def test_generate_problems_with_multiple_problems(self):
        """Test generate_problems handles multiple problems."""
        from dashboard.src.ai.agents.math_agent import MathAgent

        problems_data = {
            "topic": "trigonometry",
            "problems": [
                {
                    "id": 1,
                    "type": "word",
                    "elements": [{"kind": "text", "content": "Find sin(30)"}],
                },
                {
                    "id": 2,
                    "type": "formula",
                    "elements": [
                        {"kind": "latex", "content": r"\sin^2(x) + \cos^2(x) = 1"}
                    ],
                },
                {
                    "id": 3,
                    "type": "mixed",
                    "elements": [
                        {"kind": "text", "content": "Simplify:"},
                        {"kind": "latex", "content": r"\tan(x) \cdot \cot(x)"},
                    ],
                },
            ],
        }

        mock_client = MagicMock()
        mock_client.generate_response.return_value = json.dumps(problems_data)

        agent = MathAgent(client=mock_client)
        result = agent.generate_problems("3 trigonometry problems")

        assert result["topic"] == "trigonometry"
        assert len(result["problems"]) == 3
        assert result["problems"][0]["type"] == "word"
        assert result["problems"][1]["type"] == "formula"
        assert result["problems"][2]["type"] == "mixed"

    def test_generate_problems_raises_on_invalid_json(self):
        """Test generate_problems raises JSONDecodeError on invalid JSON."""
        from dashboard.src.ai.agents.math_agent import MathAgent

        mock_client = MagicMock()
        mock_client.generate_response.return_value = "This is not valid JSON at all"

        agent = MathAgent(client=mock_client)

        with pytest.raises(json.JSONDecodeError):
            agent.generate_problems("Generate problems")

    def test_generate_problems_raises_on_partial_json(self):
        """Test generate_problems raises error on incomplete JSON."""
        from dashboard.src.ai.agents.math_agent import MathAgent

        mock_client = MagicMock()
        mock_client.generate_response.return_value = '{"topic": "math", "problems": ['

        agent = MathAgent(client=mock_client)

        with pytest.raises(json.JSONDecodeError):
            agent.generate_problems("Generate problems")

    def test_generate_problems_with_nested_json_structures(self):
        """Test generate_problems handles deeply nested JSON."""
        from dashboard.src.ai.agents.math_agent import MathAgent

        complex_problems = {
            "topic": "complex analysis",
            "problems": [
                {
                    "id": 1,
                    "type": "mixed",
                    "elements": [
                        {"kind": "text", "content": "Given the function:"},
                        {"kind": "latex", "content": "f(z) = \\frac{z^2 + 1}{z - i}"},
                        {"kind": "text", "content": "Find all singularities."},
                    ],
                }
            ],
        }

        mock_client = MagicMock()
        mock_client.generate_response.return_value = json.dumps(complex_problems)

        agent = MathAgent(client=mock_client)
        result = agent.generate_problems("Complex analysis problem")

        assert len(result["problems"][0]["elements"]) == 3

    def test_generate_problems_with_unicode_content(self):
        """Test generate_problems handles unicode in problem content."""
        from dashboard.src.ai.agents.math_agent import MathAgent

        problems_with_unicode = {
            "topic": "Greek letters",
            "problems": [
                {
                    "id": 1,
                    "type": "formula",
                    "elements": [{"kind": "latex", "content": "α + β = γ"}],
                }
            ],
        }

        mock_client = MagicMock()
        mock_client.generate_response.return_value = json.dumps(
            problems_with_unicode, ensure_ascii=False
        )

        agent = MathAgent(client=mock_client)
        result = agent.generate_problems("Problem with Greek letters")

        assert "α" in result["problems"][0]["elements"][0]["content"]

    def test_generate_problems_with_svg_content(self):
        """Test generate_problems handles SVG elements."""
        from dashboard.src.ai.agents.math_agent import MathAgent

        problems_with_svg = {
            "topic": "geometry",
            "problems": [
                {
                    "id": 1,
                    "type": "mixed",
                    "elements": [
                        {"kind": "text", "content": "Draw a triangle:"},
                        {
                            "kind": "svg",
                            "content": '<svg width="100" height="100"><polygon points="50,10 90,90 10,90" fill="none" stroke="black"/></svg>',
                        },
                    ],
                }
            ],
        }

        mock_client = MagicMock()
        mock_client.generate_response.return_value = json.dumps(problems_with_svg)

        agent = MathAgent(client=mock_client)
        result = agent.generate_problems("Geometry with diagram")

        assert result["problems"][0]["elements"][1]["kind"] == "svg"
        assert "<svg" in result["problems"][0]["elements"][1]["content"]

    def test_generate_problems_client_error_propagates(self):
        """Test generate_problems propagates client errors."""
        from dashboard.src.ai.agents.math_agent import MathAgent

        mock_client = MagicMock()
        mock_client.generate_response.side_effect = Exception("API connection failed")

        agent = MathAgent(client=mock_client)

        with pytest.raises(Exception) as exc_info:
            agent.generate_problems("Generate problems")

        assert "API connection failed" in str(exc_info.value)

    def test_generate_problems_with_empty_problems_list(self):
        """Test generate_problems handles empty problems list."""
        from dashboard.src.ai.agents.math_agent import MathAgent

        mock_client = MagicMock()
        mock_client.generate_response.return_value = '{"topic": "none", "problems": []}'

        agent = MathAgent(client=mock_client)
        result = agent.generate_problems("No problems")

        assert result["topic"] == "none"
        assert result["problems"] == []

    def test_generate_problems_with_mathml_content(self):
        """Test generate_problems handles MathML elements."""
        from dashboard.src.ai.agents.math_agent import MathAgent

        problems_with_mathml = {
            "topic": "arithmetic",
            "problems": [
                {
                    "id": 1,
                    "type": "formula",
                    "elements": [
                        {
                            "kind": "mathml",
                            "content": "<math><mi>x</mi><mo>=</mo><mn>5</mn></math>",
                        }
                    ],
                }
            ],
        }

        mock_client = MagicMock()
        mock_client.generate_response.return_value = json.dumps(problems_with_mathml)

        agent = MathAgent(client=mock_client)
        result = agent.generate_problems("MathML problem")

        assert result["problems"][0]["elements"][0]["kind"] == "mathml"
        assert "<math>" in result["problems"][0]["elements"][0]["content"]

    def test_generate_problems_strips_multiple_markdown_blocks(self):
        """Test generate_problems handles multiple backtick sequences."""
        from dashboard.src.ai.agents.math_agent import MathAgent

        mock_client = MagicMock()
        # Response with extra backticks
        mock_client.generate_response.return_value = (
            '```json\n```{"topic": "test", "problems": []}```\n```'
        )

        agent = MathAgent(client=mock_client)
        result = agent.generate_problems("Test")

        assert result["topic"] == "test"

    def test_generate_problems_preserves_latex_backslashes(self):
        """Test generate_problems preserves backslashes in LaTeX."""
        from dashboard.src.ai.agents.math_agent import MathAgent

        problems_with_latex = {
            "topic": "calculus",
            "problems": [
                {
                    "id": 1,
                    "type": "formula",
                    "elements": [
                        {
                            "kind": "latex",
                            "content": "\\int_0^\\infty e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}",
                        }
                    ],
                }
            ],
        }

        mock_client = MagicMock()
        mock_client.generate_response.return_value = json.dumps(problems_with_latex)

        agent = MathAgent(client=mock_client)
        result = agent.generate_problems("Integration problem")

        latex_content = result["problems"][0]["elements"][0]["content"]
        assert "\\int" in latex_content
        assert "\\infty" in latex_content
