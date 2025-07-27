import math
from datetime import datetime, timedelta
import warnings
from dataclasses import dataclass
from phonenumbers import PhoneNumber


class Party:
    """An entitiy which is capable of participating in a transaction. Could be a financial
    instituion, a business, a private individual, etc."""

    name: str
    phone: PhoneNumber | None = None
    # email: str | None = None # come back around to this, maybe


@dataclass(kw_only=True)
class Transaction:
    """Tracks realized financial transacations which have already occurred. I.e. NOT PLANNED
    but OCCURRED events!"""

    title: str
    creditor: Party
    debtor: Party
    amount: float
    date: datetime
    tax: float = 0.0

    def __post_init__(self) -> None:
        if not math.isfinite(self.amount) or self.amount <= 0.0:
            raise ValueError(
                "Transaction amount must be a positive, finite, normalized value!"
            )

        one_hundred_years = timedelta(days=365 * 200)
        if self.date < datetime.now() - one_hundred_years:
            warnings.warn(
                f"Warning: the transaction '{self.title}' occurred on a date more than one "
                "hundred years before today. Please review this transaction for errors."
            )

        if self.date > datetime.now() + timedelta(days=1):
            # I provide one day buffer to fully account for all timezone complexity. ;)
            raise ValueError("Transactions cannot occur in the future!")
