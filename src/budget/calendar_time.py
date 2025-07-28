from typing import Literal
from dataclasses import dataclass

CalendarTimeUnits = Literal[
    "months", "years"
]  # Literal["days", "weeks", "months", "years"]


@dataclass
class CalendarTime:
    value: int
    unit: CalendarTimeUnits

    def __post_init__(self):
        if self.value <= 0:
            raise ValueError("Calendar time must be at least one!")
