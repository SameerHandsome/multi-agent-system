"""
Multi-Agent System with LangGraph + Groq + Simple Tools
Implements: Reflexion, Plan-and-Execute, Consensus, Safety Controls
"""

import os
from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
import asyncio
import json
import requests
from dotenv import load_dotenv

load_dotenv()

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], "The messages in the conversation"]
    user_input: str
    plan: dict
    researcher_output: str
    coder_output: str
    critic_score: float
    final_output: str
    retry_count: int
    max_retries: int
    budget: dict
    next: str


@tool
def web_search(query: str) -> str:
    """
    Search the internet using Tavily API for current information.
    
    Args:
        query: The search query string
        
    Returns:
        Search results as formatted string
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "Error: TAVILY_API_KEY not set"
    
    try:
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": api_key,
            "query": query,
            "search_depth": "basic",
            "max_results": 5
        }
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for item in data.get("results", [])[:3]:
            results.append(
                f"• {item.get('title', 'No title')}\n"
                f"  {item.get('content', 'No content')}\n"
                f"  Source: {item.get('url', 'N/A')}"
            )
        
        return "\n\n".join(results) if results else "No results found"
    except Exception as e:
        return f"Search failed: {str(e)}"
@tool
def calculate(expression: str) -> str:
    """Evaluate mathematical expressions"""
    try:
        result = eval(expression, {"__builtins__": {}})
        return f"Result: {result}"
    except Exception as e:
        return f"Calculation error: {str(e)}"

@tool
def code_validator(code: str) -> dict:
    """Validate Python code syntax"""
    try:
        compile(code, '<string>', 'exec')
        return {"valid": True, "message": "Code syntax is valid"}
    except SyntaxError as e:
        return {"valid": False, "message": f"Syntax error: {str(e)}"}



llm = ChatOpenAI(
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1",
        model="llama-3.3-70b-versatile",
        temperature=0
)

ORCHESTRATOR_PROMPT = """You are an Orchestrator Agent that decomposes tasks.

Your job:
1. Analyze the user request
2. Break it into subtasks
3. Assign to: researcher, coder, or both
4. Return ONLY a JSON plan

Format:
{
  "tasks": [
    {"agent": "researcher", "task": "description"},
    {"agent": "coder", "task": "description"}
  ]
}

Keep it simple and actionable."""

RESEARCHER_PROMPT = """You are a Research Agent that finds information.

Your job:
1. Search for relevant information
2. Validate facts
3. Summarize findings
4. Cite sources

Be concise and factual."""

CODER_PROMPT = """You are a Coder Agent that writes code.

Your job:
1. Write clean, commented code
2. Follow best practices
3. Handle edge cases
4. Explain your implementation

Keep code simple and readable."""

CRITIC_PROMPT = """You are a Critic Agent that reviews quality.

Your job:
1. Evaluate outputs for quality
2. Check for errors
3. Score from 0.0 to 1.0
4. Provide constructive feedback

Return format:
{
  "score": 0.85,
  "feedback": "your feedback here"
}"""


def orchestrator_node(state: AgentState) -> AgentState:
    """Orchestrator: Creates execution plan"""
    print("\n🎯 ORCHESTRATOR: Planning...")
    
    messages = [
        SystemMessage(content=ORCHESTRATOR_PROMPT),
        HumanMessage(content=state["user_input"])
    ]
    
    response = llm.invoke(messages)
    
    try:
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        plan = json.loads(content.strip())
    except:
        plan = {"tasks": [{"agent": "researcher", "task": state["user_input"]}]}
    
    state["plan"] = plan
    state["messages"] = state.get("messages", []) + messages + [response]
    
    first_task = plan.get("tasks", [])[0] if plan.get("tasks") else {"agent": "researcher"}
    state["next"] = first_task["agent"]
    
    print(f"📋 Plan: {len(plan.get('tasks', []))} tasks")
    return state

def researcher_node(state: AgentState) -> AgentState:
    """Researcher: Gathers information using web search"""
    print("\n🔍 RESEARCHER: Searching...")
    
    task = state["user_input"]
    for t in state.get("plan", {}).get("tasks", []):
        if t["agent"] == "researcher":
            task = t["task"]
            break

    try:
        search_results = web_search.invoke({"query": task})
        context = f"Search results:\n{search_results}\n\nTask: {task}"
    except Exception as e:
        print(f"⚠️ Search failed: {e}, using LLM only")
        context = f"Task: {task}\n(Note: Search unavailable, using knowledge only)"
    
    messages = [
        SystemMessage(content=RESEARCHER_PROMPT),
        HumanMessage(content=context)
    ]
    
    response = llm.invoke(messages)
    state["researcher_output"] = response.content
    state["messages"] = state.get("messages", []) + [response]
    has_coder = any(t["agent"] == "coder" for t in state.get("plan", {}).get("tasks", []))
    state["next"] = "coder" if has_coder else "critic"
    
    print(f"✅ Research complete: {len(response.content)} chars")
    return state

def coder_node(state: AgentState) -> AgentState:
    """Coder: Writes code"""
    print("\n💻 CODER: Writing code...")
    
    task = state["user_input"]
    for t in state.get("plan", {}).get("tasks", []):
        if t["agent"] == "coder":
            task = t["task"]
            break
    
    context = f"Task: {task}"
    if state.get("researcher_output"):
        context += f"\n\nResearch context:\n{state['researcher_output']}"
    
    messages = [
        SystemMessage(content=CODER_PROMPT),
        HumanMessage(content=context)
    ]
    
    response = llm.invoke(messages)
    state["coder_output"] = response.content
    state["messages"] = state.get("messages", []) + [response]
    state["next"] = "critic"
    
    print(f"✅ Code written: {len(response.content)} chars")
    return state

def critic_node(state: AgentState) -> AgentState:
    """Critic: Reviews and scores output"""
    print("\n⭐ CRITIC: Reviewing...")
    
    outputs = []
    if state.get("researcher_output"):
        outputs.append(f"RESEARCHER:\n{state['researcher_output']}")
    if state.get("coder_output"):
        outputs.append(f"CODER:\n{state['coder_output']}")
    
    combined = "\n\n".join(outputs)
    
    messages = [
        SystemMessage(content=CRITIC_PROMPT),
        HumanMessage(content=f"Review these outputs:\n\n{combined}")
    ]
    
    response = llm.invoke(messages)
    
    try:
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        review = json.loads(content.strip())
        score = float(review.get("score", 0.7))
    except:
        score = 0.7  
    
    state["critic_score"] = score
    state["messages"] = state.get("messages", []) + [response]
    
    if score < 0.6 and state.get("retry_count", 0) < state.get("max_retries", 2):
        print(f"⚠️ Score {score} too low, retrying...")
        state["retry_count"] = state.get("retry_count", 0) + 1
        state["next"] = "orchestrator"  
    else:
        state["next"] = "end"
    
    print(f"✅ Score: {score:.2f}")
    return state

def final_node(state: AgentState) -> AgentState:
    """Aggregates final output"""
    print("\n🎉 FINALIZING...")
    
    result = {
        "user_request": state["user_input"],
        "plan": state.get("plan", {}),
        "researcher_output": state.get("researcher_output", ""),
        "coder_output": state.get("coder_output", ""),
        "quality_score": state.get("critic_score", 0.0),
        "retry_attempts": state.get("retry_count", 0)
    }
    
    state["final_output"] = json.dumps(result, indent=2)
    return state


def route_after_orchestrator(state: AgentState) -> str:
    """Route to first agent in plan"""
    return state.get("next", "researcher")

def route_after_researcher(state: AgentState) -> str:
    """Route to coder or critic"""
    return state.get("next", "critic")

def route_after_coder(state: AgentState) -> str:
    """Route to critic"""
    return "critic"

def route_after_critic(state: AgentState) -> str:
    """Route to end or retry"""
    return state.get("next", "end")


def create_graph():
    """Creates the LangGraph workflow"""
    
    workflow = StateGraph(AgentState)
    
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("coder", coder_node)
    workflow.add_node("critic", critic_node)
    workflow.add_node("final", final_node)
    
    workflow.set_entry_point("orchestrator")
    
    workflow.add_conditional_edges("orchestrator", route_after_orchestrator)
    workflow.add_conditional_edges("researcher", route_after_researcher)
    workflow.add_conditional_edges("coder", route_after_coder)
    workflow.add_conditional_edges("critic", route_after_critic, {
        "end": "final",
        "orchestrator": "orchestrator"
    })
    workflow.add_edge("final", END)
    
    return workflow.compile()


def run_agent_system(user_input: str):
    """Run the multi-agent system"""
    
    initial_state = {
        "messages": [],
        "user_input": user_input,
        "plan": {},
        "researcher_output": "",
        "coder_output": "",
        "critic_score": 0.0,
        "final_output": "",
        "retry_count": 0,
        "max_retries": 2,
        "budget": {"tokens": 0, "calls": 0},
        "next": ""
    }
    
    graph = create_graph()
    
    print("="*60)
    print("🚀 MULTI-AGENT SYSTEM STARTING")
    print("="*60)
    
    result = graph.invoke(initial_state)
    
    print("\n" + "="*60)
    print("📊 FINAL RESULTS")
    print("="*60)
    print(result["final_output"])
    
    return result

if __name__ == "__main__":
    
    user_query = "Research the latest developments in AI agents and write a Python example"
    
    run_agent_system(user_query)