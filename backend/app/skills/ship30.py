"""Ship 30 for 30 essay generation skill."""
from app.agents.provider import get_provider

SHIP30_SYSTEM_PROMPT = """You are an expert writer trained in the Ship 30 for 30 atomic essay framework.

SHIP 30 FOR 30 PRINCIPLES:
1. HEADLINE: Powerful, curiosity-driven opener using patterns like "How X Does Y", "Why X Is Y", or a bold contrarian claim.
2. OPENING LINE: One sentence that stops the scroll. Bold, counterintuitive, or surprising.
3. MAIN BODY: 3-5 sections, each with:
   - A bold section header (### )
   - 2-4 short punchy sentences (max 20 words each)
   - Concrete examples from Lenny's podcast data
   - One memorable insight per section
4. LENGTH: Exactly 1,200–1,350 words. No shorter. No longer.
5. STYLE:
   - Short sentences only. Never more than 25 words.
   - Use numbers ("3 ways", "7 principles") over vague quantifiers
   - End each section with a takeaway
   - Use analogies to make abstract concepts concrete
6. CLOSING: One memorable sentence that recontextualizes the opening claim.

FORMAT: Markdown. Use ## for essay title, ### for section headers, **bold** for key terms."""


async def generate_essay(topic: str, context_chunks: list[dict]) -> str:
    """Generate a Ship 30 for 30 atomic essay on the given topic."""
    context_text = ""
    if context_chunks:
        context_text = "\n\nRELEVANT PODCAST INSIGHTS:\n"
        for i, chunk in enumerate(context_chunks[:5], 1):
            episode = chunk.get("episode_title", "Unknown Episode")
            text = chunk.get("text", "")[:600]
            context_text += f"\n[{i}] From \"{episode}\":\n{text}\n"

    user_prompt = f"""Write a Ship 30 for 30 atomic essay on: **{topic}**
{context_text}

Requirements:
- Exactly 1,200–1,350 words
- Use insights from the podcast context above as concrete evidence
- Follow all Ship 30 principles: punchy sentences, clear structure, memorable close
- Make it genuinely insightful, not generic"""

    provider = get_provider()
    messages = [{"role": "user", "content": user_prompt}]
    response = await provider.chat(
        messages=messages,
        system=SHIP30_SYSTEM_PROMPT,
        max_tokens=2000,
        tools=None,
    )
    # provider.chat() returns {"content": str, "tool_use": ..., "stop_reason": ...}
    if isinstance(response, dict):
        return response.get("content") or ""
    # fallback for any legacy format
    if isinstance(response, list):
        for block in response:
            if hasattr(block, "text"):
                return block.text
            if isinstance(block, dict) and block.get("type") == "text":
                return block["text"]
    return str(response)
