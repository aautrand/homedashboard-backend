from flask import current_app


def get_ai_client(source: str = "claude"):
    """Build an AI client, wired from app config.

    This is the composition root for the AI clients: the clients themselves
    take plain arguments and read no globals, so everything they need is
    resolved here. Requires an app context.

    Args:
        source: "claude" (text generation), "whisper" (speech-to-text), or
            "ollama" (local text generation).
    """
    if source == "claude":
        from .claude_client import ClaudeClient

        return ClaudeClient(
            api_key=current_app.config["ANTHROPIC_API_KEY"],
            workspace_id=current_app.config["ANTHROPIC_WORKSPACE_ID"],
        )
    elif source == "whisper":
        from .whisper_client import WhisperClient

        return WhisperClient(url=current_app.config["WHISPER_URL"])
    elif source == "ollama":
        from .ollama_client import OllamaClient

        return OllamaClient(host=current_app.config["OLLAMA_HOST"])
    else:
        raise ValueError(f"Unknown source {source!r}")
