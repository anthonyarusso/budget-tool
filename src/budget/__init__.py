from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, TypedDict, get_args, Self, NoReturn, TypeGuard
import math
import csv
from currencies import Currency  # type: ignore

from .typedefs import (
    ExpenseCategory,
    ExpensePriority,
    IncomeCategory,
)
from .errors import BudgetFileParsingError
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


_IncomeOrExpense = Literal["income", "expense"]
_BoolString = Literal["true", "false"]


class _BudgetRow(TypedDict):
    income_or_expense: _IncomeOrExpense
    name: str
    category: ExpenseCategory | IncomeCategory
    amount: str
    currency: str
    recurrence_value: str
    recurrence_unit: CalendarTimeUnits | Literal[""]
    priority: ExpensePriority | Literal[""]
    savings_goal: str
    post_tax: _BoolString | Literal[""]


def _validate_budget_row(row: dict) -> TypeGuard[_BudgetRow]:
    """Run-time check that the input row (dict) is actually valid for use as a _BudgetRow."""

    def _raise_unexpected_value(row: dict, column_name: str) -> NoReturn:
        raise BudgetFileParsingError(
            f"Unexpected value for column '{column_name}': '{row[column_name]}'!"  # type: ignore
        )

    for k in _BudgetRow.__annotations__.keys():
        if k not in row:
            raise BudgetFileParsingError(
                f"The required column header, {k}, was not present in the provided CSV file!"
            )

    if row["income_or_expense"] not in get_args(_IncomeOrExpense):
        _raise_unexpected_value(row, "income_or_expense")

    if (row["recurrence_unit"] == "" and row["recurrence_value"] != "") or (
        row["recurrence_unit"] != "" and row["recurrence_value"] == ""
    ):
        raise BudgetFileParsingError(
            "Either both the recurrence_unit and recurrence_value "
            "columns must be blank or neither must be!"
        )

    if row["recurrence_unit"] != "" and row["recurrence_unit"] not in get_args(
        CalendarTimeUnits
    ):
        _raise_unexpected_value(row, "recurrence_unit")

    if row["income_or_expense"] == "expense":
        if row["category"] not in get_args(ExpenseCategory):
            _raise_unexpected_value(row, "category")
        if row["priority"] not in get_args(ExpensePriority):
            _raise_unexpected_value(row, "priority")

    if row["income_or_expense"] == "income":
        if row["category"] not in get_args(IncomeCategory):
            _raise_unexpected_value(row, "category")
        if row["post_tax"] not in get_args(_BoolString):
            _raise_unexpected_value(row, "post_tax")

    return True


@dataclass(kw_only=True)
class PlannedExpense(_PlannedItem):
    """Always used to express planned expenses (or savings contributions), not income."""

    category: ExpenseCategory
    priority: ExpensePriority = "necessity"
    recurrence: CalendarTime | None = None
    # used to indicate that the "expense" is a savings contribution towards a particular goal
    savings_goal: str | None = None

    def to_budget_row(self) -> _BudgetRow:
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
            post_tax="",
        )

    @classmethod
    def from_budget_row(cls, row: dict) -> Self:
        if _validate_budget_row(row):
            if row["recurrence_unit"] == "":
                recurrence: None | CalendarTime = None
            else:
                recurrence = CalendarTime(
                    int(row["recurrence_value"]),
                    row["recurrence_unit"],  # type: ignore
                )

            return cls(
                name=row["name"],
                amount=float(row["amount"]),
                recurrence=recurrence,
                currency=Currency(row["currency"]),
                category=row["category"],  # type: ignore
                priority=row["priority"],  # type: ignore
                savings_goal=row["savings_goal"],
            )
        raise BudgetFileParsingError(
            "An unspecified error occurred when attempt to parse the budget file!"
        )


@dataclass(kw_only=True)
class PlannedIncome(_PlannedItem):
    category: IncomeCategory
    post_tax: bool

    def to_budget_row(self) -> _BudgetRow:
        currency = (
            "" if self.currency.money_currency is None else self.currency.money_currency
        )
        recurrence_value = "" if self.recurrence is None else str(self.recurrence.value)
        recurrence_unit: CalendarTimeUnits | Literal[""] = (
            "" if self.recurrence is None else self.recurrence.unit
        )
        return _BudgetRow(
            income_or_expense="income",
            name=self.name,
            category=self.category,
            amount=f"{self.amount:.2f}",
            currency=currency,
            recurrence_value=recurrence_value,
            recurrence_unit=recurrence_unit,
            priority="",
            savings_goal="",
            post_tax="true" if self.post_tax else "false",
        )

    @classmethod
    def from_budget_row(cls, row: dict) -> Self:
        if _validate_budget_row(row):
            if row["recurrence_unit"] == "":
                recurrence: None | CalendarTime = None
            else:
                recurrence = CalendarTime(
                    int(row["recurrence_value"]),
                    row["recurrence_unit"],  # type: ignore
                )

            return cls(
                name=row["name"],
                amount=float(row["amount"]),
                recurrence=recurrence,
                currency=Currency(row["currency"]),
                category=row["category"],  # type: ignore
                post_tax=row["post_tax"],  # type: ignore
            )

        raise BudgetFileParsingError(
            "An unspecified error occurred when attempt to parse the budget file!"
        )


# TODO: implement a more sophisticated SavingsGoal class with CSV support.
# @dataclass(kw_only=True)
# class SavingsGoal:
#     name: str
#     timeline: CalendarTime
#     amount: float

SavingsGoal = str


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
        with open(path, "wt", newline="", encoding="utf-8") as outfile:
            writer = csv.DictWriter(
                outfile, fieldnames=_BudgetRow.__annotations__.keys()
            )

            # write the CSV headers
            writer.writeheader()

            for entry in self.entries:
                writer.writerow(entry.to_budget_row())

    @classmethod
    def from_file(cls, path: str) -> Self:
        if not (path.endswith(".csv") or path.endswith(".CSV")):
            raise ValueError("The provided path must point to a file ending in '.csv'!")

        entries: list[PlannedExpense | PlannedIncome] = []
        with open(path, "rt", newline="", encoding="utf-8") as infile:
            csv_reader = csv.DictReader(infile)
            for row in csv_reader:
                if row["income_or_expense"] == "expense":
                    entries.append(PlannedExpense.from_budget_row(row))
                elif row["income_or_expense"] == "income":
                    entries.append(PlannedIncome.from_budget_row(row))
                else:
                    raise BudgetFileParsingError(
                        "Unexpected value for column 'income_or_expense': "
                        f"'{row['income_or_expense']}'!"
                    )

        return cls()
