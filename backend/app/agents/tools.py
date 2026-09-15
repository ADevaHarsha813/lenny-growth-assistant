"""Tool definitions and dispatch for the agentic loop."""
import json
from app.rag.retriever import get_retriever

ANTHROPIC_TOOLS = [
    {
        "name": "search_transcripts",
        "description": "Search Lenny's Podcast transcripts for relevant insights, frameworks, and advice. Use this for any product, growth, or strategy question.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find relevant podcast content",
                },
                "n_results": {
                    "type": "integer",
                    "description": "Number of results to return (default: 5)",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "generate_ship30_essay",
        "description": "Generate a Ship 30 for 30 atomic essay (1,200 words) on a product or growth topic, using insights from Lenny's podcast.",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The topic for the essay",
                },
            },
            "required": ["topic"],
        },
    },
    {
        "name": "generate_artifact",
        "description": "Generate a Markdown document or interactive HTML artifact on a given topic.",
        "input_schema": {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["markdown", "html"],
                    "description": "Type of artifact to generate",
                },
                "prompt": {
                    "type": "string",
                    "description": "Description of what to generate",
                },
            },
            "required": ["type", "prompt"],
        },
    },
]

OLLAMA_TOOL_DESCRIPTIONS = """
AVAILABLE TOOLS (use exactly these formats when you need to call a tool):

To search podcast transcripts:
SEARCH: <your search query here>

To write a Ship 30 essay:
ESSAY: <topic here>

To generate an artifact:
ARTIFACT: markdown | <description>
ARTIFACT: html | <description>

Only use ONE tool per response. After the tool call, wait for the result.
"""


async def dispatch_tool(name: str, input_data: dict) -> dict | str:
    """Dispatch a tool call and return the result."""
    if name == "search_transcripts":
        return await _search_transcripts(
            query=input_data.get("query", ""),
            n_results=input_data.get("n_results", 5),
        )
    elif name == "generate_ship30_essay":
        return await _generate_ship30(topic=input_data.get("topic", ""))
    elif name == "generate_artifact":
        return await _generate_artifact(
            artifact_type=input_data.get("type", "markdown"),
            prompt=input_data.get("prompt", ""),
        )
    else:
        return f"Unknown tool: {name}"


async def _search_transcripts(query: str, n_results: int = 5) -> str:
    """Search the ChromaDB vector store."""
    try:
        retriever = get_retriever()
        results = await retriever.search(query=query, n_results=n_results)
        if not results:
            return "No relevant content found in the podcast transcripts for this query."
        
        formatted = f"Found {len(results)} relevant passages:\n\n"
        for i, r in enumerate(results, 1):
            episode = r.get("episode_title", "Unknown Episode")
            source = r.get("source_file", "")
            text = r.get("text", "")
            formatted += f"[{i}] **{episode}**\n{text}\n\n"
        return formatted
    except Exception as e:
        return f"Search error: {str(e)}. The vector store may not be initialized yet."


async def _generate_ship30(topic: str) -> dict:
    """Generate a Ship 30 essay and return as artifact."""
    from app.skills.ship30 import generate_essay
    try:
        # Search for context first
        retriever = get_retriever()
        context = await retriever.search(query=topic, n_results=5)
    except Exception:
        context = []
    
    essay = await generate_essay(topic=topic, context_chunks=context)
    return {
        "artifact": {
            "type": "ship30",
            "title": f"Essay: {topic}",
            "content": essay,
        },
        "summary": f"Generated Ship 30 essay on '{topic}' ({len(essay.split())} words)",
    }


async def _generate_artifact(artifact_type: str, prompt: str) -> dict:
    """Generate a markdown or HTML artifact."""
    from app.skills.artifact_gen import generate_artifact
    try:
        retriever = get_retriever()
        context = await retriever.search(query=prompt, n_results=4)
    except Exception:
        context = []
    
    content = await generate_artifact(
        artifact_type=artifact_type,
        prompt=prompt,
        context_chunks=context,
    )
    return {
        "artifact": {
            "type": artifact_type,
            "title": prompt[:80],
            "content": content,
        },
        "summary": f"Generated {artifact_type} artifact: {prompt[:60]}",
    }
