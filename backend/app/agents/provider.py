"""
Unified LLM provider abstraction.
Supports Anthropic (cloud) and Ollama (local) behind a common interface.
"""
import httpx
import anthropic
import structlog
from app.config import settings

logger = structlog.get_logger()


class LLMProvider:
    """Wraps Anthropic or Ollama and exposes a unified chat interface."""

    def __init__(self):
        self.provider = settings.llm_provider
        if self.provider == "anthropic":
            self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        logger.info("llm.provider_init", provider=self.provider)

    async def chat(
        self,
        messages: list[dict],
        system: str = "",
        tools: list[dict] | None = None,
        max_tokens: int = 4096,
    ) -> dict:
        """
        Send messages and return response dict:
        {
          "content": str | None,
          "tool_use": {"name": str, "input": dict} | None,
          "stop_reason": str,
        }
        """
        if self.provider == "anthropic":
            return await self._anthropic_chat(messages, system, tools, max_tokens)
        else:
            return await self._ollama_chat(messages, system, tools, max_tokens)

    async def _anthropic_chat(self, messages, system, tools, max_tokens):
        kwargs = dict(
            model="claude-3-5-haiku-20241022",
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        )
        if tools:
            kwargs["tools"] = tools

        resp = await self._client.messages.create(**kwargs)
        tool_use = None
        text_content = None

        for block in resp.content:
            if block.type == "tool_use":
                tool_use = {"name": block.name, "input": block.input, "id": block.id}
            elif block.type == "text":
                text_content = block.text

        return {"content": text_content, "tool_use": tool_use, "stop_reason": resp.stop_reason}

    async def _ollama_chat(self, messages, system, tools, max_tokens):
        # Build Ollama-format messages
        ollama_messages = []
        if system:
            ollama_messages.append({"role": "system", "content": system})
        ollama_messages.extend(messages)

        payload = {
            "model": settings.ollama_model,
            "messages": ollama_messages,
            "stream": False,
            "options": {"num_predict": max_tokens},
        }

        # Ollama tool_use: simulate via prompt injection when tools provided
        if tools:
            tool_desc = "\n".join(
                f"- {t['name']}: {t['description']}" for t in tools
            )
            payload["messages"][-1]["content"] += (
                f"\n\n[Available tools: {tool_desc}. "
                "If you need to search transcripts, say 'SEARCH: <query>'. "
                "Otherwise answer directly.]"
            )

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{settings.ollama_base_url}/api/chat",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        content = data["message"]["content"]

        # Parse simulated tool calls from Ollama
        tool_use = None
        if tools and "SEARCH:" in content:
            import re
            m = re.search(r"SEARCH:\s*(.+?)(?:\n|$)", content)
            if m:
                tool_use = {"name": "search_transcripts", "input": {"query": m.group(1).strip()}, "id": "ollama-tool"}
                content = None

        return {"content": content, "tool_use": tool_use, "stop_reason": "end_turn"}

    async def stream_chat(self, messages: list[dict], system: str = "", max_tokens: int = 2048, tools=None):
        """Async generator that yields text tokens."""
        if self.provider == "anthropic":
            async with self._client.messages.stream(
                model="claude-3-5-haiku-20241022",
                max_tokens=max_tokens,
                system=system,
                messages=messages,
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        else:
            # Ollama streaming
            ollama_messages = []
            if system:
                ollama_messages.append({"role": "system", "content": system})
            ollama_messages.extend(messages)

            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    f"{settings.ollama_base_url}/api/chat",
                    json={"model": settings.ollama_model, "messages": ollama_messages, "stream": True},
                ) as resp:
                    import json
                    async for line in resp.aiter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                token = data.get("message", {}).get("content", "")
                                if token:
                                    yield token
                            except Exception:
                                pass


_provider: LLMProvider | None = None


def get_provider() -> LLMProvider:
    global _provider
    if _provider is None:
        _provider = LLMProvider()
    return _provider
