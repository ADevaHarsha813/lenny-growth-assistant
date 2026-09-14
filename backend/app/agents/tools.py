"""
Tool definitions for the agentic loop.
Three tools: search_transcripts, generate_ship30_essay, generate_artifact.
"""
from app.rag.retriever import search

TOOLS = [
    {
        "name": "search_transcripts",
        "description": (
            "Search Lenny's Podcast transcripts for relevant content. "
            "Use this to ground answers in actual transcript material. "
            "Returns the most relevant chunks with their source episode."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query, e.g. 'how to find product-market fit'",
                }
            },
            "required": ["query"],
        },
    },
    {
        "name": "generate_ship30_essay",
        "description": (
            "Generate a Ship 30 for 30 style essay (~1250 words) on a topic, "
            "grounded in Lenny's transcript content. "
            "Use AFTER searching transcripts to have source material."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "The essay topic"},
                "grounding": {"type": "string", "description": "Key insights from transcripts to use"},
            },
            "required": ["topic", "grounding"],
        },
    },
    {
        "name": "generate_artifact",
        "description": (
            "Generate a Markdown document or complete HTML/CSS artifact "
            "based on the conversation. Returns structured content for the artifact viewer."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "artifact_type": {
                    "type": "string",
                    "enum": ["markdown", "html"],
                    "description": "Type of artifact to generate",
                },
                "title": {"type": "string", "description": "Title for the artifact"},
                "content_brief": {"type": "string", "description": "What the artifact should contain"},
            },
            "required": ["artifact_type", "title", "content_brief"],
        },
    },
]

# Anthropic-format tools
ANTHROPIC_TOOLS = TOOLS

# For Ollama (description only, no schema)
OLLAMA_TOOL_DESCRIPTIONS = [
    {"name": t["name"], "description": t["description"]} for t in TOOLS
]


async def dispatch_tool(name: str, inputs: dict, session_messages: list[dict]) -> dict:
    """Execute a tool call and return result."""
    if name == "search_transcripts":
        hits = await search(inputs["query"], n_results=5)
        if not hits:
            return {"result": "No relevant transcript content found for this query.", "hits": []}
        formatted = []
        for h in hits:
            formatted.append(
                f"**{h['episode_title']}** (source: {h['source_file']})\n{h['text'][:600]}..."
            )
        return {
            "result": "\n\n---\n\n".join(formatted),
            "hits": hits,
            "sources": [
                {"title": h["episode_title"], "excerpt": h["text"][:200], "chunk_index": h["chunk_index"]}
                for h in hits
            ],
        }

    elif name == "generate_ship30_essay":
        from app.skills.ship30 import generate_essay
        essay = await generate_essay(inputs["topic"], inputs["grounding"])
        return {"result": essay, "artifact_type": "ship30", "title": f"Ship 30 Essay: {inputs['topic']}"}

    elif name == "generate_artifact":
        from app.skills.artifact_gen import generate_artifact
        content = await generate_artifact(
            inputs["artifact_type"],
            inputs["title"],
            inputs["content_brief"],
            session_messages,
        )
        return {
            "result": content,
            "artifact_type": inputs["artifact_type"],
            "title": inputs["title"],
        }

    return {"result": f"Unknown tool: {name}"}
