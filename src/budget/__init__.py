from dataclasses import dataclass
from typing import Literal
from currencies import Currency  # type: ignore

from .enums import ExpenseCategory, ExpensePriority, IncomeCategory


@dataclass
class CalendarTime:
    value: int
    unit: Literal["days", "weeks", "months", "years"]

    def __post_init__(self):
        if self.value <= 0:
            raise ValueError("Calendar time must be at least one!")


@dataclass
class SavingsContribution:
    savings_goal: str


@dataclass(kw_only=True)
class PlannedExpense:
    """Always used to express planned expenses (or savings contributions), not income."""

    name: str
    category: ExpenseCategory | SavingsContribution
    priority: ExpensePriority
    currency: Currency
    amount: float
    tax: float
    recurrence: CalendarTime | None = None


@dataclass(kw_only=True)
class PlannedIncome:
    name: str
    category: IncomeCategory
    currency: Currency
    amount: float
    post_tax: bool
    recurrence: CalendarTime | None = None


class Budget:
    """A summary of all PLANNED expenses and income. To clarify, the budget is the PLAN not the
    the realization of actual financial events."""

    def __init__(self, *entries: PlannedExpense | PlannedIncome) -> None:
        self.entries: list[PlannedExpense | PlannedIncome] = list(entries)
