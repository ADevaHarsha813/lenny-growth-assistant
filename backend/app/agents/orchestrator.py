"""Agentic orchestrator — runs the tool-use loop."""
import json
import asyncio
from typing import AsyncGenerator
from app.agents.provider import get_provider
from app.agents.tools import dispatch_tool, ANTHROPIC_TOOLS, OLLAMA_TOOL_DESCRIPTIONS
from app.config import settings
import structlog

log = structlog.get_logger()

SYSTEM_PROMPT = """You are Lenny's Growth Assistant — an expert AI trained on Lenny Rachitsky's podcast transcripts.

You help product managers, founders, and growth teams by:
1. Answering questions about product strategy, growth, metrics, and team building using real insights from Lenny's podcast
2. Writing Ship 30 for 30 atomic essays on product/growth topics
3. Generating Markdown documents and interactive HTML artifacts

TOOLS AVAILABLE:
- search_transcripts: Search Lenny's podcast transcripts for relevant insights. Use this for ANY question about growth, product, or strategy.
- generate_ship30_essay: Write a 1,200-word Ship 30 for 30 essay. Use when asked for an essay, article, or writing.
- generate_artifact: Create Markdown or HTML artifacts. Use when asked for a document, template, dashboard, or visual.

BEHAVIOR:
- Always search transcripts first before answering product/growth questions
- Cite specific episodes when referencing podcast content
- Be direct, specific, and actionable
- Use the guest's real frameworks and mental models from the podcast"""


async def run_agent(
    messages: list[dict],
    session_id: str,
    skill: str | None = None,
) -> AsyncGenerator[str, None]:
    """
    Run the agentic loop, yielding SSE-formatted strings.
    Yields: data: <json>\n\n
    """
    provider = get_provider()
    provider_name = settings.llm_provider

    # Adjust system prompt for specific skills
    system = SYSTEM_PROMPT
    if skill == "ship30":
        system += "\n\nThe user wants a Ship 30 for 30 essay. Use generate_ship30_essay after searching for relevant context."
    elif skill in ("artifact_markdown", "artifact_html"):
        artifact_type = "html" if skill == "artifact_html" else "markdown"
        system += f"\n\nThe user wants a {artifact_type} artifact. Use generate_artifact with type='{artifact_type}'."

    tools = ANTHROPIC_TOOLS if provider_name == "anthropic" else None
    loop_messages = list(messages)
    max_iterations = 5
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        log.info("agent_loop", iteration=iteration, provider=provider_name)

        # Stream or call LLM
        if provider_name == "anthropic":
            collected_text = ""
            tool_calls = []
            stop_reason = None

            async for chunk in provider.stream_chat(
                messages=loop_messages,
                system=system,
                max_tokens=4096,
                tools=tools,
            ):
                chunk_type = chunk.get("type")

                if chunk_type == "text":
                    delta = chunk.get("delta", "")
                    collected_text += delta
                    yield f"data: {json.dumps({'type': 'text', 'delta': delta})}\n\n"

                elif chunk_type == "tool_use":
                    tool_calls.append(chunk)

                elif chunk_type == "stop":
                    stop_reason = chunk.get("stop_reason")

            # Add assistant message to history
            assistant_content = []
            if collected_text:
                assistant_content.append({"type": "text", "text": collected_text})
            for tc in tool_calls:
                assistant_content.append({
                    "type": "tool_use",
                    "id": tc["id"],
                    "name": tc["name"],
                    "input": tc["input"],
                })
            if assistant_content:
                loop_messages.append({"role": "assistant", "content": assistant_content})

            # Execute tools if needed
            if tool_calls and stop_reason == "tool_use":
                tool_results = []
                for tc in tool_calls:
                    yield f"data: {json.dumps({'type': 'tool_start', 'tool': tc['name'], 'input': tc['input']})}\n\n"
                    result = await dispatch_tool(tc["name"], tc["input"])
                    yield f"data: {json.dumps({'type': 'tool_end', 'tool': tc['name']})}\n\n"

                    # If tool produced an artifact, emit it
                    if isinstance(result, dict) and result.get("artifact"):
                        yield f"data: {json.dumps({'type': 'artifact', 'artifact': result['artifact']})}\n\n"
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tc["id"],
                            "content": result.get("summary", "Artifact generated successfully."),
                        })
                    else:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tc["id"],
                            "content": str(result)[:8000],
                        })

                loop_messages.append({"role": "user", "content": tool_results})
                # Continue loop to get final response
            else:
                # Done
                break

        else:
            # Ollama path — collect first pass silently to detect tool calls
            # (avoids streaming raw "SEARCH: ..." tool-call syntax to the user)
            ollama_system = system + f"\n\n{OLLAMA_TOOL_DESCRIPTIONS}"
            response_text = ""
            async for chunk in provider.stream_chat(
                messages=loop_messages,
                system=ollama_system,
                max_tokens=4096,
            ):
                delta = chunk if isinstance(chunk, str) else chunk.get("delta", "")
                if delta:
                    response_text += delta

            loop_messages.append({"role": "assistant", "content": response_text})

            # Check for tool calls in response
            tool_call = _parse_ollama_tool_call(response_text)
            if tool_call:
                yield f"data: {json.dumps({'type': 'tool_start', 'tool': tool_call['name'], 'input': tool_call['input']})}\n\n"
                result = await dispatch_tool(tool_call["name"], tool_call["input"])
                yield f"data: {json.dumps({'type': 'tool_end', 'tool': tool_call['name']})}\n\n"

                if isinstance(result, dict) and result.get("artifact"):
                    yield f"data: {json.dumps({'type': 'artifact', 'artifact': result['artifact']})}\n\n"
                    loop_messages.append({
                        "role": "user",
                        "content": f"Tool result: {result.get('summary', 'Done')}. Now give a brief, natural response to the user."
                    })
                else:
                    loop_messages.append({
                        "role": "user",
                        "content": f"Tool result:\n{str(result)[:3000]}\n\nNow synthesize this into a helpful, direct answer."
                    })
                # Stream only the final synthesis — this is what the user sees
                async for chunk in provider.stream_chat(
                    messages=loop_messages,
                    system=system,
                    max_tokens=1024,
                ):
                    delta = chunk if isinstance(chunk, str) else chunk.get("delta", "")
                    if delta:
                        yield f"data: {json.dumps({'type': 'text', 'delta': delta})}\n\n"
            else:
                # No tool call — stream the already-collected response
                yield f"data: {json.dumps({'type': 'text', 'delta': response_text})}\n\n"
            break

    yield f"data: {json.dumps({'type': 'done'})}\n\n"


def _parse_ollama_tool_call(text: str) -> dict | None:
    """Parse Ollama's text-based tool calls like SEARCH: query or ESSAY: topic."""
    import re
    # SEARCH: <query>
    m = re.search(r'SEARCH:\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
    if m:
        return {"name": "search_transcripts", "input": {"query": m.group(1).strip()}}
    # ESSAY: <topic>
    m = re.search(r'ESSAY:\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
    if m:
        return {"name": "generate_ship30_essay", "input": {"topic": m.group(1).strip()}}
    # ARTIFACT: <type> | <prompt>
    m = re.search(r'ARTIFACT:\s*(html|markdown)\s*\|\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
    if m:
        return {"name": "generate_artifact", "input": {"type": m.group(1).lower(), "prompt": m.group(2).strip()}}
    return None
