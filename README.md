# Multi-Agent AI System with LangGraph

A production-ready multi-agent system using LangGraph, Groq API, and advanced AI patterns.

## Features

- 🎯 **Multi-Agent Architecture**: Orchestrator, Researcher, Coder, and Critic agents
- 🔄 **Reflexion Pattern**: Auto-retry with learning from failures
- 📋 **Plan-and-Execute**: Strategic task decomposition
- ⭐ **Quality Consensus**: Critic-based validation and scoring
- 🛡️ **Safety Controls**: Budget limits and error handling

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv venv

# Activate
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Install dependencies
pip install langgraph langchain-openai langchain-community tavily-python python-dotenv
```

### 2. Configure API Key

Create a `.env` file:

```env
GROQ_API_KEY=gsk_your_api_key_here
TAVILY_API_KEY=tvly-your_api_key_here
```

Get API keys:
- Groq: [console.groq.com](https://console.groq.com)
- Tavily: [tavily.com](https://app.tavily.com)

### 3. Run

```bash
python agent.py
```

## How It Works

```
User Input → Orchestrator → Researcher → Coder → Critic → Final Output
                ↑                                    ↓
                └────────── Retry if score < 0.6 ───┘
```

1. **Orchestrator**: Creates execution plan
2. **Researcher**: Searches web for information
3. **Coder**: Writes code if needed
4. **Critic**: Reviews quality (0.0-1.0 score)
5. **Reflexion**: Retries if quality too low

## Example Usage

```python
from agent import run_agent_system

result = run_agent_system("Research AI agents and write a Python example")
print(result["final_output"])
```

## Tools Available

- `tavily_search`: Tavily advanced web search
- `calculate`: Math expression evaluator
- `code_validator`: Python syntax checker

## Configuration

Edit these in `agent.py`:

```python
llm = ChatOpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
    model="llama-3.3-70b-versatile",
    temperature=0.7,
    max_tokens=1024
)

# Retry settings
max_retries: 2
quality_threshold: 0.6
```

## Project Structure

```
.
├── agent.py       # Main multi-agent system
├── .env           # API keys (create this)
├── README.md      # This file
└── requirements.txt
```

## Troubleshooting

**Import Error**: Make sure virtual environment is activated
```bash
source venv/bin/activate
```

**API Error**: Check your `.env` file has both `GROQ_API_KEY` and `TAVILY_API_KEY`

**No Search Results**: Verify Tavily API key is valid and has credits remaining
