from flask import current_app


def get_ai_client(source: str = "claude"):
    """Build an AI client, wired from app config.

    This is the composition root for the AI clients: the clients themselves
    take plain arguments and read no globals, so everything they need is
    resolved here. Requires an app context.

    Args:
        source: "claude" (text generation), "openai" (speech-to-text), or
            "ollama" (local text generation).
    """
    if source == "openai":
        from .openai_transcription_client import OpenAITranscriptionClient

        return OpenAITranscriptionClient(
            api_key=current_app.config["OPENAI_API_KEY"],
            model=current_app.config["OPENAI_STT_MODEL"],
        )
    elif source == "claude":
        from .claude_client import ClaudeClient

        return ClaudeClient(
            api_key=current_app.config["ANTHROPIC_API_KEY"],
            workspace_id=current_app.config["ANTHROPIC_WORKSPACE_ID"],
        )
    elif source == "ollama":
        from .ollama_client import OllamaClient

        return OllamaClient(host=current_app.config["OLLAMA_HOST"])
    else:
        raise ValueError(f"Unknown source {source!r}")


# The agent loop resends its whole history on every tool call, so it runs on
# LangChain's chat model rather than ClaudeClient's single-turn helper.
AGENT_MODEL = "claude-opus-5-5"


def get_chat_model():
    """Build the LangChain chat model the agents run on, wired from app config.

    Opus 5.5 always thinks; effort is the only depth control and its default
    is medium, so it is pinned here rather than left implicit. Requires an
    app context.
    """
    from langchain_anthropic import ChatAnthropic

    headers = {}
    workspace_id = current_app.config.get("ANTHROPIC_WORKSPACE_ID")
    if workspace_id:
        headers["anthropic-workspace-id"] = workspace_id

    return ChatAnthropic(
        model=AGENT_MODEL,
        api_key=current_app.config["ANTHROPIC_API_KEY"],
        max_tokens=16000,
        output_config={"effort": "medium"},
        default_headers=headers,
        timeout=180,
    )
