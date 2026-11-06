import os

from ai_module.ai_provider import AIProvider
from ai_module._constants import DEFAULT_MODEL


class GroqProvider(AIProvider):
    # Adapt the Groq SDK and track whether its client is owned or borrowed.

    def __init__(self, client, owns_client=False):
        self._client = client
        self._owns_client = owns_client

    def complete(self, messages):
        # Send one assessment request; the Groq SDK handles transient API retries.
        return self._client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "").strip() or DEFAULT_MODEL,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.2,
            max_completion_tokens=4096,
        )

    def close(self):
        if self._owns_client:
            self._client.close()

