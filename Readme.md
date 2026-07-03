# 💰 Finance Agent

An AI-powered personal finance tracker built with **LangGraph**, **LangChain**,
and **Streamlit**. Chat naturally to log income/expenses, set budgets, and get
spending insights — all backed by a real SQLite database and viewable on a
live dashboard.

Works with either **Google Gemini** or **Groq** as the LLM provider.

## Project Structure

```
finance-agent/
├── pyproject.toml              # uv-managed dependencies
├── .env.example                # copy to .env and add your API key
├── .gitignore
├── README.md
├── app.py                      # Streamlit entrypoint (chat + dashboard)
├── data/
│   └── finance.db              # created automatically on first run
└── src/
    |
    ├── __init__.py
    ├── config.py            # LLM provider setup (Google / Groq)
    ├── database.py          # SQLite CRUD for transactions & budgets
    ├── prompts.py           # system prompt / agent persona
    ├── tools.py             # LangChain @tool functions the agent can call
    └── graph.py             # LangGraph ReAct agent (LLM + tools + memory)
```

## Setup

1. **Install [uv](https://docs.astral.sh/uv/)** if you don't have it:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Install dependencies** (uv creates and manages the virtual env for you):
   ```bash
   uv sync
   ```

3. **Add your API key.** Copy `.env.example` to `.env` and fill in ONE of:
   - `GOOGLE_API_KEY` — get one free at https://aistudio.google.com/apikey
   - `GROQ_API_KEY` — get one free at https://console.groq.com/keys

   ```bash
   cp .env.example .env
   ```

   You can also skip this and simply paste your key into the sidebar when the
   app is running.

4. **Run the app:**
   ```bash
   uv run streamlit run app.py
   ```

   Then open the URL Streamlit prints (usually http://localhost:8501).

## How to use it

Go to the **Chat Assistant** tab and just talk to it naturally:

- "I spent 1200 on groceries today"
- "I got my salary of 50000 on the 1st"
- "Set a budget of 5000 for Food"
- "How much have I spent this month?"
- "What's my current balance?"
- "Show my last 10 transactions"
- "Delete transaction 4"

The agent extracts the details, calls the right tool, writes to the SQLite
database, and confirms what it recorded.

Switch to the **Dashboard** tab to see:
- Total income / expense / net balance
- A spending-by-category pie chart
- Budget progress bars with over-budget / near-limit warnings
- A full transaction table
- A manual "Add transaction" form (no chat required)

## Swapping / adding LLM providers

Provider logic lives entirely in `src/finance_agent/config.py`. To change the
model used for a provider, edit `GOOGLE_MODEL` or `GROQ_MODEL`. To add a new
provider (e.g. OpenAI, Anthropic), add another branch in `get_llm()` — no
other file needs to change since `graph.py` and `tools.py` are provider-agnostic.

## Notes

- Conversation memory is kept in-process via LangGraph's `MemorySaver` — it
  resets when the app restarts. Transaction/budget data persists in
  `data/finance.db` regardless.
- This is a personal-use tool; the SQLite database is local and unencrypted,
  so don't deploy it publicly without adding auth and a proper database.
