import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from domain import ValidationError, summarize, validate_expense


class ExpenseDomainTests(unittest.TestCase):
    def test_valid_expense_is_normalized(self):
        result = validate_expense({
            "description": "  AWS course  ",
            "amount": "29.99",
            "category": "Education",
            "date": "2026-09-18",
        })
        self.assertEqual(result["description"], "AWS course")
        self.assertEqual(result["amount"], Decimal("29.99"))
        self.assertEqual(result["category"], "education")
        self.assertEqual(result["month"], "2026-09")

    def test_invalid_expense_is_rejected(self):
        with self.assertRaises(ValidationError):
            validate_expense({"description": "x", "amount": -1, "category": "unknown", "date": "today"})

    def test_summary_groups_categories(self):
        result = summarize([
            {"category": "food", "amount": Decimal("12.50")},
            {"category": "food", "amount": Decimal("7.50")},
            {"category": "education", "amount": Decimal("30")},
        ])
        self.assertEqual(result["total"], 50.0)
        self.assertEqual(result["count"], 3)
        self.assertEqual(result["byCategory"]["food"], 20.0)


if __name__ == "__main__":
    unittest.main()

