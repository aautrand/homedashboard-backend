import requests

DEFAULT_MODEL = "claude-opus-5"

# Non-streaming replies must finish inside the request timeout, so this stays
# well below the model's 128k output ceiling.
DEFAULT_MAX_TOKENS = 16000

# Adaptive thinking makes a slow call slower; the weather clients' 10s timeout
# is far too tight for a generation request.
DEFAULT_TIMEOUT = 180


class ClaudeClient:
    """Text generation backed by the Anthropic Messages REST API.

    Talks to the endpoint directly with `requests` rather than the `anthropic`
    SDK, matching how the weather clients call their upstreams.

    `instructions` maps to Claude's top-level `system` field rather than being
    prepended to the user turn, so the two are cached and billed separately.
    """

    BASE_URL = "https://api.anthropic.com/v1/messages"
    API_VERSION = "2023-06-01"

    def __init__(
        self,
        api_key: str,
        workspace_id: str = None,
        model: str = DEFAULT_MODEL,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        """
        Args:
            api_key: Anthropic API key.
            workspace_id: Required for identity-linked (service account) keys,
                which are not bound to a single workspace. Workspace-scoped
                keys leave this unset.
            model: Default model for requests that don't override it.
            timeout: Seconds to wait on the API.
        """
        self.api_key = api_key
        self.workspace_id = workspace_id
        self.model = model
        self.timeout = timeout

    def generate_response(
        self,
        prompt: str,
        instructions: str = None,
        model: str = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> str:
        """Send a single-turn prompt and return the text of the reply.

        Args:
            prompt: The user turn.
            instructions: Optional system prompt.
            model: Overrides the model chosen at construction time.
            max_tokens: Ceiling on the reply length.
        """
        payload = {
            "model": model or self.model,
            "max_tokens": max_tokens,
            # Adaptive lets Claude decide how much to reason per request. The
            # thinking blocks it returns are filtered out of the result below.
            "thinking": {"type": "adaptive"},
            "messages": [{"role": "user", "content": prompt}],
        }
        if instructions:
            payload["system"] = instructions

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.API_VERSION,
            "content-type": "application/json",
        }
        if self.workspace_id:
            headers["anthropic-workspace-id"] = self.workspace_id

        try:
            response = requests.post(
                self.BASE_URL,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.HTTPError as e:
            # Anthropic returns the reason in the body; the status line alone
            # does not distinguish a bad key from a rate limit.
            raise Exception(
                f"Claude request failed ({e.response.status_code}): {e.response.text}"
            ) from e
        except requests.RequestException as e:
            raise Exception(f"Failed to reach Claude: {e}") from e

        return self._extract_text(response.json())

    @staticmethod
    def _extract_text(body: dict) -> str:
        """Join the text blocks of a response, dropping thinking blocks."""
        return "".join(
            block.get("text", "")
            for block in body.get("content", [])
            if block.get("type") == "text"
        ).strip()
