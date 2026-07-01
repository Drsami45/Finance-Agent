"""Finance Agent — Streamlit front-end.

Two tabs:
    1. Chat Assistant — natural-language interface backed by a LangGraph agent.
    2. Dashboard — balance, spending breakdown, budget progress, transaction table.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import streamlit as st
import pandas as pd
import plotly.express as px

from src import database as db
from src.graph import build_agent, run_agent

st.set_page_config(page_title="Finance Agent", page_icon="💰", layout="wide")
db.init_db()

# ---------------------------------------------------------------- Sidebar --
st.sidebar.title("💰 Finance Agent")
st.sidebar.caption("AI-powered personal finance tracker")

provider = st.sidebar.selectbox("LLM Provider", ["google", "groq"], index=0)
api_key = st.sidebar.text_input(
    f"{provider.capitalize()} API Key",
    type="password",
    help="Leave blank to use the key from your .env file instead.",
)

if st.sidebar.button("🔄 Reset conversation"):
    st.session_state.pop("messages", None)
    st.session_state.pop("agent", None)
    st.session_state.pop("provider", None)
    st.rerun()

st.sidebar.divider()
st.sidebar.markdown(
    "**Try asking:**\n"
    "- I spent 1200 on groceries today\n"
    "- I got my salary of 50000\n"
    "- Set a budget of 5000 for Food\n"
    "- How much have I spent this month?\n"
    "- What's my current balance?\n"
    "- Show my last 10 transactions"
)

# ------------------------------------------------------------ Session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent" not in st.session_state or st.session_state.get("provider") != provider:
    try:
        st.session_state.agent = build_agent(provider, api_key or None)
        st.session_state.provider = provider
        st.session_state.agent_error = None
    except Exception as e:
        st.session_state.agent = None
        st.session_state.agent_error = str(e)

# ------------------------------------------------------------------- Tabs --
tab_chat, tab_dashboard = st.tabs(["💬 Chat Assistant", "📊 Dashboard"])

with tab_chat:
    st.subheader("Chat with your Finance Agent")

    if st.session_state.get("agent_error") and not api_key:
        st.info(f"👋 Enter your {provider.capitalize()} API key in the sidebar to get started.")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Tell me about a transaction, or ask about your finances...")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            try:
                if st.session_state.agent is None:
                    st.session_state.agent = build_agent(provider, api_key or None)
                with st.spinner("Thinking..."):
                    reply = run_agent(st.session_state.agent, user_input)
                st.markdown(reply)
            except Exception as e:
                reply = f"⚠️ Error: {e}"
                st.markdown(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})

with tab_dashboard:
    st.subheader("Financial Overview")

    balance = db.get_balance()
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Income", f"{balance['income']:,.2f}")
    col2.metric("Total Expense", f"{balance['expense']:,.2f}")
    col3.metric("Net Balance", f"{balance['balance']:,.2f}")

    st.divider()
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### Spending by Category")
        spend = db.spending_by_category()
        if spend:
            df_spend = pd.DataFrame(spend)
            fig = px.pie(df_spend, names="category", values="total", hole=0.4)
            fig.update_layout(margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No expenses recorded yet.")

    with col_right:
        st.markdown("#### Budget Status")
        statuses = db.get_budget_status()
        if statuses:
            for s in statuses:
                pct = min(s["percent_used"], 100)
                label = f"{s['category']}: {s['spent']:,.0f} / {s['limit']:,.0f} ({s['percent_used']}%)"
                st.progress(pct / 100, text=label)
                if s["percent_used"] >= 100:
                    st.error(f"⚠️ Over budget for {s['category']}!")
                elif s["percent_used"] >= 80:
                    st.warning(f"Nearing budget limit for {s['category']}.")
        else:
            st.info("No budgets set yet. Ask the assistant to set one!")

    st.divider()
    st.markdown("#### Recent Transactions")
    txns = db.get_transactions(limit=100)
    if txns:
        df = pd.DataFrame(txns)[["id", "date", "type", "category", "amount", "note"]]
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No transactions yet. Start chatting with the assistant to add some!")

    st.divider()
    with st.expander("➕ Add transaction manually"):
        with st.form("manual_txn_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            m_date = c1.date_input("Date")
            m_type = c2.selectbox("Type", ["expense", "income"])
            m_amount = c3.number_input("Amount", min_value=0.0, step=1.0)
            c4, c5 = st.columns(2)
            m_category = c4.text_input("Category")
            m_note = c5.text_input("Note (optional)")
            submitted = st.form_submit_button("Add")
            if submitted and m_category and m_amount > 0:
                db.add_transaction(str(m_date), m_type, m_category, m_amount, m_note)
                st.success("Transaction added!")
                st.rerun()