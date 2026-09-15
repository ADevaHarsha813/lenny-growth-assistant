"""Artifact generation skill — Markdown and HTML artifacts."""
from app.agents.provider import get_provider

MARKDOWN_SYSTEM = """You are an expert technical writer. Generate clean, well-structured Markdown documents.
Use proper heading hierarchy (# ## ###), bullet points, tables where helpful, and code blocks.
Documents should be comprehensive, actionable, and immediately useful."""

HTML_SYSTEM = """You are an expert frontend developer and designer. Generate beautiful, self-contained HTML artifacts.
Requirements:
- Single HTML file, all CSS inline in <style> tags, all JS inline in <script> tags
- Modern design: Inter or system font, clean white/light background, good spacing
- Responsive (works on mobile)
- No external dependencies (no CDN links)
- Interactive where appropriate (toggles, tabs, hover effects)
- Professional quality — something you'd be proud to show a client"""


async def generate_artifact(
    artifact_type: str,
    prompt: str,
    context_chunks: list[dict],
) -> str:
    """Generate a markdown or HTML artifact."""
    context_text = ""
    if context_chunks:
        context_text = "\n\nRELEVANT CONTEXT FROM LENNY'S PODCAST:\n"
        for i, chunk in enumerate(context_chunks[:4], 1):
            episode = chunk.get("episode_title", "Unknown Episode")
            text = chunk.get("text", "")[:500]
            context_text += f"\n[{i}] {episode}:\n{text}\n"

    if artifact_type == "html":
        system = HTML_SYSTEM
        user_prompt = f"""Create a beautiful, self-contained HTML artifact for: {prompt}
{context_text}
Return ONLY the complete HTML document. No explanation, no markdown code fences — just the raw HTML starting with <!DOCTYPE html>."""
        max_tokens = 4000
    else:
        system = MARKDOWN_SYSTEM
        user_prompt = f"""Create a comprehensive Markdown document for: {prompt}
{context_text}
Return well-structured Markdown with clear headings, examples, and actionable takeaways."""
        max_tokens = 3000

    provider = get_provider()
    messages = [{"role": "user", "content": user_prompt}]
    response = await provider.chat(
        messages=messages,
        system=system,
        max_tokens=max_tokens,
        tools=None,
    )
    if isinstance(response, list):
        for block in response:
            if hasattr(block, 'text'):
                return block.text
            elif isinstance(block, dict) and block.get('type') == 'text':
                return block['text']
    return str(response)
