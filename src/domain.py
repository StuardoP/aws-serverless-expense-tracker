from datetime import date
from decimal import Decimal, InvalidOperation

CATEGORIES = {"food", "transport", "education", "health", "entertainment", "other"}


class ValidationError(ValueError):
    pass


def validate_expense(payload):
    if not isinstance(payload, dict):
        raise ValidationError("Request body must be a JSON object")

    description = str(payload.get("description", "")).strip()
    if not 2 <= len(description) <= 120:
        raise ValidationError("Description must contain 2 to 120 characters")

    try:
        amount = Decimal(str(payload.get("amount")))
    except (InvalidOperation, TypeError):
        raise ValidationError("Amount must be a valid number")
    if amount <= 0 or amount > Decimal("1000000"):
        raise ValidationError("Amount must be greater than 0 and at most 1000000")

    category = str(payload.get("category", "")).lower().strip()
    if category not in CATEGORIES:
        raise ValidationError(f"Category must be one of: {', '.join(sorted(CATEGORIES))}")

    expense_date = str(payload.get("date", ""))
    try:
        date.fromisoformat(expense_date)
    except ValueError:
        raise ValidationError("Date must use YYYY-MM-DD format")

    return {
        "description": description,
        "amount": amount,
        "category": category,
        "date": expense_date,
        "month": expense_date[:7],
    }


def summarize(expenses):
    by_category = {}
    for expense in expenses:
        category = expense["category"]
        by_category[category] = by_category.get(category, Decimal("0")) + Decimal(str(expense["amount"]))
    total = sum(by_category.values(), Decimal("0"))
    return {
        "total": float(total),
        "count": len(expenses),
        "byCategory": {key: float(value) for key, value in sorted(by_category.items())},
    }

