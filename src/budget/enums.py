from enum import Enum, auto


class ExpenseCategory(Enum):
    AUTOMOTIVE = auto()
    CHARITY = auto()
    DINING = auto()
    EDUCATION = auto()
    FINANCIAL_SERVICES = auto()  # membership dues, bank fees, etc.
    # FUN --> luxury expenses that make life worth living.
    # For example: Hobbies, entertainment, shopping for trinkets / new clothes, etc.
    FUN = auto()
    GIFTS = auto()
    GROCERIES = auto()
    HOME_AND_GARDEN = auto()  # home maintenance and improvement
    HOUSING = auto()  # rent / mortgage / homeowner's insurance, etc.
    LEGAL_SERVICES = auto()
    LENDING = auto()  # a loan that you give to someone else
    LOAN_PAYMENTS = auto()  # repaying loans that were made to yourself
    MEDICAL = auto()
    PETS = auto()
    RAINY_DAY = auto()
    RENT = auto()
    TRAVEL = auto()
    UTILITIES = auto()
    WELLBEING = auto()  # anything related to fitness and self-care


class ExpensePriority(Enum):
    NECESSITY = auto()
    NEGOTIABLE = auto()
    LUXURY = auto()


class IncomeCategory(Enum):
    GIFTS = auto()
    INVESTMENTS = auto()  # includes dividends, etc.
    JOB = auto()
    REIMBURSEMENT = auto()
    RENT = auto()
    SALE = auto()  # sale of property not including captial gains / stock related sales.
    SIDE_HUSTLE = auto()
