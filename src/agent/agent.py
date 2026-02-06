import os
from dotenv import load_dotenv
from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from openai import AsyncOpenAI

load_dotenv(".env.local")  # loads variables from .env.local

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

class AgentState(TypedDict):
    history: List[dict] # Full conversation history
    next_action: str # Logic routing ( for tools/ CRM integration )
    output_text: str # Current sentence to be spoken
    tool_calls: List[dict] # For parsed tool calls

async def general_assistant_node(state: AgentState) -> dict:
    """Calls OpenRouter LLM to decide on a response"""
    messages = state["history"]
    tools = state.get("tools", []) # Pass tools if provided

    # Fromat tools for OpenAI/OpenRouter
    formatted_tools = [{"type": "function", "function": {"name": t["name"], "description": t["description"], "parameters": {"type": "object", "properties": t["parameters"]}}} for t in tools] if tools else None
    # Call OpenRouter 
    response = await client.chat.completions.create(
        model="meta-llama/llama-3.2-3b-instruct:free",
        messages=messages,
        max_tokens=300,
        temperature=0.7,
        tools=formatted_tools,
        tool_choice="auto" if tools else None
    )

    message = response.choices[0].message
    output_text = message.content or ""
    tool_calls = message.tool_calls or []

    # Update history
    updated_history = state['history'] + [{"role": "assistant", "content": output_text}]

    return {"output_text": output_text, "history": updated_history, "tool_calls": tool_calls}

# Build the Graph
workflow = StateGraph(AgentState)
workflow.add_node('assistant', general_assistant_node)
workflow.add_edge(START, "assistant")
workflow.add_edge("assistant", END)

agent_brain = workflow.compile()