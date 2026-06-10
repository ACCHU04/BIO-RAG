"""
Incognito Mode — unrestricted general-purpose chat via OpenRouter (Gemma 4).
No guardrails, no RAG pipeline, no domain restrictions.
Works like a general AI chatbot (ChatGPT-style).
"""

from typing import List, Dict
from loguru import logger

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage

from app.config import get_settings

settings = get_settings()

INCOGNITO_SYSTEM_PROMPT = """You are a helpful, knowledgeable, and friendly AI assistant.
You can answer questions on ANY topic — science, coding, recipes, sports, history, math, creative writing, and more.
There are no domain restrictions. Be thorough, clear, and conversational.
Format your responses with markdown when appropriate (bold, lists, code blocks, etc.)."""


def incognito_chat(messages: List[Dict[str, str]]) -> str:
    """
    Send a multi-turn conversation via OpenRouter (Gemma 4) without any guardrails or RAG.

    Args:
        messages: List of dicts with 'role' ('user' or 'assistant') and 'content'.

    Returns:
        The AI's reply as a plain string.
    """
    llm = ChatOpenAI(
        model="openrouter/free",
        openai_api_key=settings.openrouter_api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0.7,
        max_tokens=4096,
    )

    # Build LangChain message list
    lc_messages = [SystemMessage(content=INCOGNITO_SYSTEM_PROMPT)]

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "user":
            lc_messages.append(HumanMessage(content=content))
        elif role == "assistant":
            lc_messages.append(AIMessage(content=content))

    logger.info(f"[INCOGNITO] Sending {len(lc_messages)} messages to OpenRouter (Gemma 4, no guardrails)")

    try:
        response = llm.invoke(lc_messages)
        reply = response.content.strip()
        logger.info(f"[INCOGNITO] Reply received ({len(reply)} chars)")
        return reply
    except Exception as e:
        logger.error(f"[INCOGNITO] OpenRouter call failed: {e}")
        return f"Sorry, I encountered an error: {str(e)}. Please try again."
