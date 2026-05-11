from typing import AsyncIterator, Optional
from .config import settings
from .telemetry import estimate_tokens

_llm = None


def get_llm():
    global _llm
    if _llm is not None:
        return _llm
    if not settings.has_llm:
        return None
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        _llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.google_api_key,
            temperature=0.3,
            convert_system_message_to_human=True,
        )
        return _llm
    except Exception:
        return None


async def ainvoke(prompt: str, system: Optional[str] = None) -> tuple[str, int, int]:
    """Returns (text, input_tokens, output_tokens)."""
    llm = get_llm()
    if llm is None:
        # Demo-mode fallback handled by callers. Should not be called here.
        return "", 0, 0

    from langchain_core.messages import HumanMessage, SystemMessage
    messages = []
    if system:
        messages.append(SystemMessage(content=system))
    messages.append(HumanMessage(content=prompt))

    response = await llm.ainvoke(messages)
    text = response.content if hasattr(response, "content") else str(response)
    if isinstance(text, list):
        text = "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in text)

    in_tok, out_tok = 0, 0
    meta = getattr(response, "usage_metadata", None) or getattr(response, "response_metadata", {})
    if isinstance(meta, dict):
        usage = meta.get("usage_metadata") or meta.get("token_usage") or meta
        in_tok = usage.get("input_tokens") or usage.get("prompt_tokens") or 0
        out_tok = usage.get("output_tokens") or usage.get("completion_tokens") or 0
    if not in_tok:
        in_tok = estimate_tokens((system or "") + prompt)
    if not out_tok:
        out_tok = estimate_tokens(text)

    return text, in_tok, out_tok


async def ainvoke_stream(prompt: str, system: Optional[str] = None) -> AsyncIterator[dict]:
    """Yields {type:'chunk', text:str} and finally {type:'usage', input, output, full}."""
    llm = get_llm()
    if llm is None:
        yield {"type": "usage", "input": 0, "output": 0, "full": ""}
        return

    from langchain_core.messages import HumanMessage, SystemMessage
    messages = []
    if system:
        messages.append(SystemMessage(content=system))
    messages.append(HumanMessage(content=prompt))

    full = ""
    in_tok = out_tok = 0
    async for chunk in llm.astream(messages):
        text = getattr(chunk, "content", "") or ""
        if isinstance(text, list):
            text = "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in text)
        if text:
            full += text
            yield {"type": "chunk", "text": text}
        meta = getattr(chunk, "usage_metadata", None) or {}
        if isinstance(meta, dict):
            in_tok = meta.get("input_tokens", in_tok) or in_tok
            out_tok = meta.get("output_tokens", out_tok) or out_tok

    if not in_tok:
        in_tok = estimate_tokens((system or "") + prompt)
    if not out_tok:
        out_tok = estimate_tokens(full)
    yield {"type": "usage", "input": in_tok, "output": out_tok, "full": full}

