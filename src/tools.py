"""LangChain tools that let the agent read/write the finance database."""
from langchain_core.tools import tool
from . import database as db


@tool
def add_transaction(date: str, type: str, category: str, amount: float, note: str = "") -> str:
    """Add a new income or expense transaction to the database.

    Args:
        date: Transaction date in YYYY-MM-DD format.
        type: Either 'income' or 'expense'.
        category: A short category label, e.g. Food, Rent, Salary, Transport.
        amount: The transaction amount as a positive number.
        note: Optional short note describing the transaction.
    """
    if type not in ("income", "expense"):
        return "Error: type must be 'income' or 'expense'."
    tid = db.add_transaction(date, type, category, float(amount), note)
    return f"Recorded {type} of {amount} in category '{category}' on {date} (id={tid})."


@tool
def delete_transaction_tool(transaction_id: int) -> str:
    """Delete a transaction by its id.

    Args:
        transaction_id: The id of the transaction to delete.
    """
    ok = db.delete_transaction(transaction_id)
    return f"Deleted transaction {transaction_id}." if ok else f"No transaction found with id {transaction_id}."


@tool
def get_transactions_tool(category: str = "", type: str = "", start_date: str = "",
                            end_date: str = "", limit: int = 20) -> str:
    """List recent transactions, optionally filtered by category, type and date range.

    Args:
        category: Optional category filter.
        type: Optional 'income' or 'expense' filter.
        start_date: Optional start date (YYYY-MM-DD).
        end_date: Optional end date (YYYY-MM-DD).
        limit: Max number of transactions to return.
    """
    rows = db.get_transactions(
        category=category or None,
        type_=type or None,
        start_date=start_date or None,
        end_date=end_date or None,
        limit=limit,
    )
    if not rows:
        return "No transactions found."
    lines = [f"#{r['id']} {r['date']} {r['type']} {r['category']} {r['amount']} - {r['note']}" for r in rows]
    return "\n".join(lines)


@tool
def get_balance_tool() -> str:
    """Get the current total income, total expense, and net balance."""
    b = db.get_balance()
    return f"Income: {b['income']}, Expense: {b['expense']}, Balance: {b['balance']}"


@tool
def spending_by_category_tool(start_date: str = "", end_date: str = "") -> str:
    """Get total spending grouped by category, optionally within a date range.

    Args:
        start_date: Optional start date (YYYY-MM-DD).
        end_date: Optional end date (YYYY-MM-DD).
    """
    rows = db.spending_by_category(start_date=start_date or None, end_date=end_date or None)
    if not rows:
        return "No expense data found."
    return "\n".join(f"{r['category']}: {r['total']}" for r in rows)


@tool
def set_budget_tool(category: str, monthly_limit: float) -> str:
    """Set or update a monthly budget limit for a category.

    Args:
        category: The category to set a budget for.
        monthly_limit: The maximum amount allowed to be spent per month in this category.
    """
    db.set_budget(category, float(monthly_limit))
    return f"Budget for '{category}' set to {monthly_limit} per month."


@tool
def get_budget_status_tool(month: str = "") -> str:
    """Get budget status (limit, spent, remaining, percent used) for all budgeted categories.

    Args:
        month: Optional month in YYYY-MM format. Defaults to the current month.
    """
    rows = db.get_budget_status(month or None)
    if not rows:
        return "No budgets have been set yet."
    lines = [
        f"{r['category']}: spent {r['spent']} of {r['limit']} "
        f"({r['percent_used']}% used, {r['remaining']} remaining)"
        for r in rows
    ]
    return "\n".join(lines)


ALL_TOOLS = [
    add_transaction,
    delete_transaction_tool,
    get_transactions_tool,
    get_balance_tool,
    spending_by_category_tool,
    set_budget_tool,
    get_budget_status_tool,
]