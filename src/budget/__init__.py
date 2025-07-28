from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, TypedDict, get_args
import math
import csv
from currencies import Currency  # type: ignore

from .typedefs import (
    ExpenseCategory,
    ExpensePriority,
    IncomeCategory,
)

from .calendar_time import CalendarTime, CalendarTimeUnits


def _one_month_factory() -> CalendarTime:
    return CalendarTime(1, "months")


@dataclass(kw_only=True)
class _PlannedItem:
    name: str
    amount: float
    recurrence: CalendarTime | None = field(default_factory=_one_month_factory)
    currency: Currency = Currency("USD")

    def __post_init__(self) -> None:
        if self.amount < 0.0:
            raise ValueError("Amount must be non-negative!")

    def get_normalized_monthly_amount(self) -> float:
        if self.recurrence is None:
            return self.amount
        else:
            if self.recurrence.unit == "years":
                return self.amount / (12 * self.recurrence.value)
            elif self.recurrence.unit == "months":
                return self.amount / (self.recurrence.value)
            else:
                raise TypeError(
                    "A CalendarTime's unit attribute was set to an unsupported value! "
                    "Please only use 'months' or 'years' for this field."
                )


class _BudgetRow(TypedDict):
    income_or_expense: Literal["income", "expense"]
    name: str
    category: ExpenseCategory | IncomeCategory
    amount: str
    currency: str
    recurrence_value: str
    recurrence_unit: CalendarTimeUnits | Literal[""]
    priority: ExpensePriority | Literal[""]
    savings_goal: str


@dataclass(kw_only=True)
class PlannedExpense(_PlannedItem):
    """Always used to express planned expenses (or savings contributions), not income."""

    category: ExpenseCategory
    priority: ExpensePriority = "necessity"
    recurrence: CalendarTime | None = None
    # used to indicate that the "expense" is a savings contribution towards a particular goal
    savings_goal: str | None = None

    def as_budget_row(self) -> _BudgetRow:
        currency = (
            "" if self.currency.money_currency is None else self.currency.money_currency
        )
        recurrence_value = "" if self.recurrence is None else str(self.recurrence.value)
        recurrence_unit: CalendarTimeUnits | Literal[""] = (
            "" if self.recurrence is None else self.recurrence.unit
        )
        savings_goal = "" if self.savings_goal is None else self.savings_goal
        return _BudgetRow(
            income_or_expense="expense",
            name=self.name,
            category=self.category,
            amount=f"{self.amount:.2f}",
            currency=currency,
            recurrence_value=recurrence_value,
            recurrence_unit=recurrence_unit,
            priority=self.priority,
            savings_goal=savings_goal,
        )


@dataclass(kw_only=True)
class PlannedIncome(_PlannedItem):
    category: IncomeCategory
    post_tax: bool

    def as_budget_row(self) -> _BudgetRow:
        currency = (
            "" if self.currency.money_currency is None else self.currency.money_currency
        )
        recurrence_value = "" if self.recurrence is None else str(self.recurrence.value)
        recurrence_unit: CalendarTimeUnits | Literal[""] = (
            "" if self.recurrence is None else self.recurrence.unit
        )
        return _BudgetRow(
            income_or_expense="expense",
            name=self.name,
            category=self.category,
            amount=f"{self.amount:.2f}",
            currency=currency,
            recurrence_value=recurrence_value,
            recurrence_unit=recurrence_unit,
            priority="",
            savings_goal="",
        )


@dataclass(kw_only=True)
class SavingsGoal:
    name: str
    timeline: CalendarTime
    amount: float


class Budget:
    """A summary of all PLANNED expenses and income. To clarify, the budget is the PLAN not the
    the realization of actual financial events."""

    def __init__(self, *entries: PlannedExpense | PlannedIncome) -> None:
        self.balance: float = 0.0
        self.entries: list[PlannedExpense | PlannedIncome] = list(entries)
        self.saving_goals: dict[str, SavingsGoal] = {}
        self.allocations: dict[ExpenseCategory, float] = {
            k: 0.0 for k in get_args(ExpenseCategory)
        }

        for entry in entries:
            if not (
                isinstance(entry, PlannedExpense) or isinstance(entry, PlannedIncome)
            ):
                raise TypeError(
                    "Entries must be either a PlannedExpense or PlannedIncome object!"
                )
            if isinstance(entry, PlannedExpense):
                self.allocations[entry.category] += (
                    entry.get_normalized_monthly_amount()
                )

    def get_monthly_gross(self) -> float:
        """Returns the sum of all income minus the sum of all expenses on a monthly basis. All
        annual items are divided by 12 for this consideration. All multi-month items are divided
        by the number of months they span.

        TODO: implement a strategy for dealing with daily & weekly items."""
        gross = 0.0
        for entry in self.entries:
            sign = -1.0 if isinstance(entry, PlannedExpense) else 1.0
            gross += sign * entry.get_normalized_monthly_amount()

        return gross

    def get_total_monthly_expense(self) -> float:
        total_expense: float = 0.0
        for entry in self.entries:
            if isinstance(entry, PlannedExpense):
                total_expense += entry.amount

        return total_expense

    def get_monthly_expenses_as_fraction(self) -> dict[ExpenseCategory, float]:
        total = self.get_total_monthly_expense()
        if math.isclose(total, 0.0):
            raise RuntimeError(
                "Attempted to call 'get_monthly_expenses_as_fraction()' "
                "without any non-zero monthly expenses registered to the Budget yet!"
            )
        return {k: (v / total) for k, v in self.allocations.items()}

    def export_file(self, path: str) -> None:
        if not (path.endswith(".csv") or path.endswith(".CSV")):
            raise ValueError("The provided path must point to a file ending in '.csv'!")
        with open(path, "wt", newline="", encoding="UTF8") as outfile:
            writer = csv.writer(outfile)

            # write the CSV headers
            writer.writerow(_BudgetRow.__annotations__.keys())

            for entry in self.entries:
                writer.writerow(entry.as_budget_row().values())
