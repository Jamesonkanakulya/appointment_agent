"""
LiteLLM-based agentic loop for appointment booking.
Handles tool calling iteratively until the agent produces a final text response.
"""
import json
import logging
from datetime import datetime

import litellm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Instance, GlobalSettings, ConversationHistory
from ..encryption import decrypt
from .tool_schemas import TOOL_SCHEMAS
from .tools import execute_tool
from .prompts import build_system_prompt

logger = logging.getLogger(__name__)

MAX_TOOL_ITERATIONS = 15  # Safety cap to prevent infinite loops


async def run_agent(
    session_id: str,
    user_message: str,
    instance: Instance,
    db: AsyncSession,
) -> str:
    """
    Run the appointment booking agent for one user turn.
    Loads conversation history, calls LLM with tools, executes tools, returns final text.
    """
    # Load global LLM settings
    result = await db.execute(select(GlobalSettings).where(GlobalSettings.id == 1))
    llm_settings = result.scalar_one_or_none()
    if not llm_settings:
        raise RuntimeError("LLM settings not initialized.")

    api_key = decrypt(llm_settings.llm_api_key) if llm_settings.llm_api_key else None
    if not api_key:
        raise RuntimeError("LLM API key not configured. Please set it in Global Settings.")

    # Load conversation history
    history_result = await db.execute(
        select(ConversationHistory).where(
            ConversationHistory.instance_id == instance.id,
            ConversationHistory.session_id == session_id
        )
    )
    history_record = history_result.scalar_one_or_none()
    messages: list[dict] = list(history_record.messages) if history_record else []

    # Append new user message
    messages.append({"role": "user", "content": user_message})

    # Build system prompt
    system_prompt = build_system_prompt(
        timezone=instance.timezone,
        timezone_offset=instance.timezone_offset,
        business_name=instance.business_name,
        workday_start=instance.workday_start,
        workday_end=instance.workday_end,
    )

    # Agentic loop
    final_response = ""
    for iteration in range(MAX_TOOL_ITERATIONS):
        logger.info(f"Agent iteration {iteration + 1} for session {session_id}")

        call_kwargs = dict(
            model=llm_settings.llm_model,
            api_key=api_key,
            messages=[{"role": "system", "content": system_prompt}] + messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
            temperature=0.2,
            max_tokens=4096,
        )
        if llm_settings.llm_base_url:
            call_kwargs["api_base"] = llm_settings.llm_base_url

        try:
            response = await litellm.acompletion(**call_kwargs)
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise RuntimeError(f"LLM error: {e}")

        choice = response.choices[0]
        message = choice.message

        # Collect text content
        text_content = message.content or ""

        # Check for tool calls
        tool_calls = getattr(message, "tool_calls", None) or []

        if not tool_calls:
            # No more tool calls — this is the final response
            final_response = text_content
            messages.append({"role": "assistant", "content": text_content})
            break

        # Add assistant message with tool calls to history
        messages.append({
            "role": "assistant",
            "content": text_content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    }
                }
                for tc in tool_calls
            ]
        })

        # Execute each tool call and collect results
        tool_result_messages = []
        for tc in tool_calls:
            tool_name = tc.function.name
            try:
                tool_input = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                tool_input = {}

            logger.info(f"Executing tool: {tool_name} with input: {tool_input}")
            result = await execute_tool(tool_name, tool_input, instance, db)
            logger.info(f"Tool {tool_name} result: {result}")

            tool_result_messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result),
            })

        messages.extend(tool_result_messages)

    else:
        # Hit iteration limit — extract any text from last message
        final_response = final_response or "I'm sorry, I was unable to complete your request. Please try again."

    # Save updated conversation history
    await _save_history(session_id, instance.id, messages, history_record, db)

    return final_response or "I'm sorry, I couldn't generate a response. Please try again."


async def _save_history(
    session_id: str,
    instance_id,
    messages: list[dict],
    existing_record,
    db: AsyncSession
):
    # Only keep the last 40 messages to prevent unbounded growth
    messages = messages[-40:]

    if existing_record:
        existing_record.messages = messages
        existing_record.updated_at = datetime.utcnow()
    else:
        record = ConversationHistory(
            instance_id=instance_id,
            session_id=session_id,
            messages=messages,
        )
        db.add(record)

    await db.commit()
