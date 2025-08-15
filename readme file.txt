# Covenant Schedule Generator

## Overview

The **Covenant Schedule Generator** is a robust Python system for generating, managing, and persisting covenant reminder schedules for financial transactions. It is designed for financial institutions and compliance teams to automate and enforce business rules for covenants (e.g., financial reporting, compliance certificates, audits) tied to loans and credit facilities.

**Highlights:**
- Clear business rule enforcement and edge case handling
- Modular, maintainable, and extensible codebase
- Fully documented and thoroughly tested

## Key Features

- **Flexible Schedule Generation:** Supports daily, weekly, monthly, quarterly, and annual frequencies. Handles month-end, weekends, leap years, holidays, and transaction end cutoffs automatically.
- **Business Rule Enforcement:** All business logic and edge cases are explicitly handled and documented. Configuration-driven frequency and holiday rules.
- **Persistence Layer:** Uses SQLite for reliable, lightweight storage. Full CRUD (Create, Read, Update, Delete) and bulk operations for transactions, covenants, and schedules.
- **Holiday Calendar Integration:** Customizable holiday lists for accurate business day calculations.
- **Comprehensive Testing:** Extensive unit test suite covering all business scenarios and edge cases.
- **Professional Documentation:** All code is clearly commented and includes descriptive docstrings for maintainability.



## Quick Start

**Requirements:**
- Python 3.8+
- Git

**Setup:**
1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   cd <repo-folder>
   ```
2. Create a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   # source venv/bin/activate  # On macOS/Linux
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage Example
```python
from schedule_generator import ScheduleGenerator
from database import Database

transaction = {
    "transaction_id": "TXN-001",
    "name": "Corporate Credit Facility",
    "start_date": "2025-01-15",
    "end_date": "2027-01-15"
}
covenants = [
    {"covenant_id": "COV-001", "transaction_id": "TXN-001", "description": "Monthly Financial Statements", "frequency": "monthly", "owner_email": "finance@company.com"},
    {"covenant_id": "COV-002", "transaction_id": "TXN-001", "description": "Quarterly Compliance Certificate", "frequency": "quarterly", "owner_email": "legal@company.com"},
    {"covenant_id": "COV-003", "transaction_id": "TXN-001", "description": "Annual Audited Financials", "frequency": "annually", "owner_email": "finance@company.com"}
]

sg = ScheduleGenerator()
schedules = sg.generate_schedules(transaction, covenants)

with Database('schedules.db') as db:
    db.save_schedules(schedules)

print(f"Generated {len(schedules)} schedule entries")
print(f"Generated {len(schedules)} schedule entries")


## Business Rules & Logic

The system enforces strict business rules for accuracy and compliance:

**Transaction & Covenant Validation**
- Required fields: `transaction_id`, `name`, `start_date`, `end_date` (transaction); `covenant_id`, `transaction_id`, `description`, `frequency`, `owner_email` (covenant)
- Dates: `YYYY-MM-DD` format; start date ≤ end date
- Valid email for `owner_email`
- Referential integrity: every covenant’s `transaction_id` must match a transaction
- Uniqueness: all IDs must be unique

**Frequency & Schedule Generation**
- Supported: `daily`, `weekly`, `monthly`, `quarterly`, `annually`
- Minimum durations: annual ≥ 1 year, quarterly ≥ 90 days, monthly ≥ 28 days, etc.
- Unsupported frequencies raise errors

**Business Day & Holiday Handling**
- Business days: Mon–Fri, excluding holidays
- Holidays: configurable list or auto-generated (via `holidays` package)
- Due dates on holidays/weekends are adjusted to the next/previous business day
- If all days in a period are holidays, no schedule is generated for that period
- If a business day cannot be found within 10 days, an error is raised

**Edge Cases**
- Month-end: schedules starting on the last day of a month always use month-end
- Leap years: annual schedules starting Feb 29 use Feb 29 in leap years, Feb 28 otherwise
- Quarterly: special handling for Feb/Mar period-ends
- No due date after the next business day following transaction end

**Data Integrity & Database**
- Foreign keys: deleting a transaction/covenant cascades deletes
- Status: `pending`, `completed`, `overdue`, `cancelled`
- Bulk operations: all inserts checked for uniqueness and referential integrity
- All violations raise clear errors

See `intern_reminder_assignment.md` for full requirements.


## How Schedule Generation Works

The `ScheduleGenerator` class implements the core logic:
1. **Initialization:**
   - Optionally accepts holidays, adjustment direction, country code, and years
   - Auto-generates holidays if not provided
2. **Validation:**
   - Validates all input data before processing
3. **Schedule Generation:**
   - Selects method based on frequency
   - Calculates due dates, applies month-end/leap year/business day rules
   - Adjusts due dates for holidays/weekends
   - Creates schedule entries with unique IDs
4. **Edge Case Handling:**
   - Handles month-end, leap years, transaction end cutoffs, and quarterly logic
5. **Error Handling:**
   - Raises errors for unresolvable business days or rule violations
6. **Extensibility:**
   - Modular design for easy extension

See `schedule_generator.py` for details.

## Database Layer

The `Database` class provides a simple, reliable interface for persistence:

**Schema:**
- SQLite, self-contained
- Tables: `transactions`, `covenants`, `schedules` (with foreign keys and cascading deletes)

**Usage:**
- Used as a context manager (`with Database(...) as db:`)
- Auto-creates schema and enforces constraints

**Key Methods:**
- `save_transaction(transaction)` — insert transaction (unique ID)
- `save_covenants(covenants)` — bulk insert covenants (unique, referential integrity)
- `save_schedules(schedules, holidays=None)` — bulk insert schedules (unique, valid status, not on holidays/weekends)
- `get_schedules(covenant_id=None)` — fetch schedules
- `get_transaction(transaction_id)` — fetch transaction
- `get_covenants(transaction_id=None)` — fetch covenants
- `update_schedule_status(schedule_id, status)` — update status
- `delete_schedule(schedule_id)` — delete schedule

**Data Integrity:**
- All operations checked for uniqueness, referential integrity, and business rules
- Violations raise clear errors

See `database.py` for details.

## Testing

Testing is comprehensive and covers:
- All business rules and edge cases
- Realistic data factories for transactions/covenants
- Both success and failure scenarios
- In-memory database integration (persistence, uniqueness, referential integrity, CRUD)
- Performance and scalability (large datasets, stress tests)
- Full documentation for every test

**Run all tests:**
```bash
pytest test_schedule_generator.py
```
All tests should pass. See `test_schedule_generator.py` for details.

## Full Requirements
- See `intern_reminder_assignment.md` for the complete specification.

## Author
- [Your Name]







# Covenant Schedule Generator

## Overview

The Covenant Schedule Generator is a professional-grade Python system for generating, persisting, and managing covenant fulfillment schedules for financial transactions. Designed for financial institutions and compliance teams, it automates the creation of reminder schedules for covenants (such as financial reporting, compliance certificates, and audits) associated with loans, credit facilities, and other financial products.

This project is built to be robust, maintainable, and extensible, with a strong focus on business rule clarity, edge case handling, and data integrity. All code is thoroughly documented and tested.

## Key Features

- **Flexible Schedule Generation:**
  - Supports daily, weekly, monthly, quarterly, and annual covenant frequencies.
  - Automatically adjusts for month-end, weekends, leap years, holidays, and transaction end cutoffs.
- **Business Rule Enforcement:**
  - All business logic and edge cases are explicitly handled and documented.
  - Configuration-driven frequency and holiday rules.
- **Persistence Layer:**
  - Uses SQLite for reliable, lightweight storage.
  - Full CRUD (Create, Read, Update, Delete) and bulk operations for transactions, covenants, and schedules.
- **Holiday Calendar Integration:**
  - Customizable holiday lists for accurate business day calculations.
- **Comprehensive Testing:**
  - Extensive unit test suite covering all business scenarios and edge cases.
- **Professional Documentation:**
  - All code is clearly commented and includes descriptive docstrings for maintainability.

## Setup Instructions

**Requirements:**
- Python 3.8 or higher (recommended: latest stable Python 3.x)
- Git (for cloning the repository)

**Setup Steps:**
1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd <repo-folder>
   ```
2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   # Or, on macOS/Linux:
   # source venv/bin/activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage Example
```python
from schedule_generator import ScheduleGenerator
from database import Database

# Load transaction and covenants (example)
transaction = {
    "transaction_id": "TXN-001",
    "name": "Corporate Credit Facility",
    "start_date": "2025-01-15",
    "end_date": "2027-01-15"
}
covenants = [
    {"covenant_id": "COV-001", "transaction_id": "TXN-001", "description": "Monthly Financial Statements", "frequency": "monthly", "owner_email": "finance@company.com"},
    {"covenant_id": "COV-002", "transaction_id": "TXN-001", "description": "Quarterly Compliance Certificate", "frequency": "quarterly", "owner_email": "legal@company.com"},
    {"covenant_id": "COV-003", "transaction_id": "TXN-001", "description": "Annual Audited Financials", "frequency": "annually", "owner_email": "finance@company.com"}
]

# Generate schedules
sg = ScheduleGenerator()
schedules = sg.generate_schedules(transaction, covenants)

# Persist to database
with Database('schedules.db') as db:
    db.save_schedules(schedules)

print(f"Generated {len(schedules)} schedule entries")
  
## Business Rules & Logic

The Covenant Schedule Generator enforces the following business rules and logic to ensure accuracy, compliance, and data integrity:

### Transaction & Covenant Validation
- **Transaction fields required:** `transaction_id`, `name`, `start_date`, `end_date` (all must be non-empty strings).
- **Covenant fields required:** `covenant_id`, `transaction_id`, `description`, `frequency`, `owner_email` (all must be non-empty strings).
- **Date format:** All dates must be in `YYYY-MM-DD` format. Start date must not be after end date.
- **Email validation:** Owner email must be a valid email address.
- **Referential integrity:** Each covenant’s `transaction_id` must match an existing transaction.
- **Uniqueness:** Each `covenant_id` and `schedule_id` must be unique within the system.

### Frequency & Schedule Generation
- **Supported frequencies:** `daily`, `weekly`, `monthly`, `quarterly`, `annually` (case-insensitive).
- **Minimum transaction duration:**
  - Annual: at least 1 year
  - Quarterly: at least 90 days
  - Monthly: at least 28 days
  - Weekly/Daily: at least 1 week/day respectively
- **Unsupported frequencies:** Any frequency not listed above will raise an error.

### Business Day & Holiday Handling
- **Business day definition:** Monday–Friday, excluding holidays.
- **Holiday configuration:**
  - Holidays can be provided as a list or auto-generated for a country using the `holidays` package.
  - All due dates are adjusted to the next (or previous, if configured) business day if they fall on a weekend or holiday.
- **Holiday edge cases:**
  - If all days in a period are holidays, no schedules are generated for that period.
  - If a due date cannot be adjusted to a business day within 10 days, an error is raised.

### Edge Case Handling
- **Month-end logic:**
  - If a schedule starts on the last day of a month, all subsequent due dates are also set to the last day of each period’s month (e.g., Jan 31 → Feb 28/29).
- **Leap year logic:**
  - Annual schedules starting on Feb 29 will use Feb 29 in leap years and Feb 28 in non-leap years.
- **Quarterly schedules:**
  - Special handling for February and March to ensure correct period-end and due dates.
- **Transaction end cutoff:**
  - No due date will be after the next business day following the transaction’s end date.

### Data Integrity & Database Rules
- **Foreign key enforcement:**
  - Schedules reference covenants, which reference transactions. Deleting a transaction or covenant cascades deletes.
- **Status field:**
  - Allowed values: `pending`, `completed`, `overdue`, `cancelled`.
- **Bulk operations:**
  - All inserts are checked for uniqueness and referential integrity before committing.
- **Error handling:**
  - All business rule violations raise clear, descriptive errors.

For a full list of requirements and business rules, see `intern_reminder_assignment.md`.

## How the Schedule Generation Logic Works

The core logic of the Covenant Schedule Generator is implemented in the `ScheduleGenerator` class. Here’s a high-level summary of how the system works:

### 1. Initialization
- When you create a `ScheduleGenerator` object, you can provide a list of holidays, a business day adjustment direction (`forward` or `backward`), a country code for holiday calculation, and a list of years. If holidays are not provided, the system will auto-generate them for the specified country and years using the `holidays` package. If the package is unavailable, a default set of holidays is used.

### 2. Validation
- Every transaction and covenant is validated for required fields, correct types, and business logic (see Business Rules above). This prevents invalid data from entering the system.

### 3. Schedule Generation
- For each covenant, the generator selects the appropriate schedule generation method based on the frequency (`daily`, `weekly`, `monthly`, `quarterly`, `annually`).
- The generator calculates the correct due dates for each period, taking into account:
  - The start and end dates of the transaction
  - The frequency and period length
  - Month-end and leap year rules
  - Business day and holiday adjustments
- If a due date falls on a weekend or holiday, it is automatically adjusted to the next or previous business day, depending on configuration.
- For each period, a schedule entry is created with a unique `schedule_id`, the associated `covenant_id`, the due date, status, and the period start/end dates.

### 4. Edge Case Handling
- The generator includes robust logic for:
  - Month-end transitions (e.g., Jan 31 → Feb 28/29)
  - Leap years (e.g., Feb 29 handling for annual schedules)
  - Transaction end cutoffs (no due date after the next business day following the end date)
  - Holidays and weekends (with configurable adjustment direction)
  - Quarterly schedules with special handling for February and March

### 5. Error Handling
- If a business day cannot be found within 10 days of adjustment, a runtime error is raised to prevent infinite loops (e.g., if all days are holidays).
- All business rule violations raise clear, descriptive errors.

### 6. Extensibility
- The code is modular and can be easily extended to support new frequencies, custom business day rules, or additional schedule attributes.

For more details, see the comments and docstrings in `schedule_generator.py`.

## Database Layer & Persistence Logic

The `Database` class provides a robust, professional, and easy-to-use interface for all data persistence needs in the Covenant Schedule Generator system. Here’s how it works:

### 1. Schema & Structure
- The database uses SQLite and is fully self-contained—no external server required.
- Three main tables:
  - **transactions:** Stores transaction metadata (ID, name, start/end dates).
  - **covenants:** Stores covenant definitions, linked to transactions via `transaction_id` (with referential integrity enforced).
  - **schedules:** Stores generated schedule entries, linked to covenants via `covenant_id`.
- Indexes and foreign key constraints ensure fast queries and data integrity. Deleting a transaction or covenant cascades deletes to dependent records.

### 2. Connection & Context Management
- The `Database` class is used as a context manager (`with Database(...) as db:`), which:
  - Opens a connection and enforces foreign key constraints.
  - Ensures the schema is present (auto-creates tables and indexes if needed).
  - Commits and closes the connection automatically on exit.

### 3. Core Methods
- **save_transaction(transaction):**
  - Inserts a new transaction. Enforces uniqueness of `transaction_id`.
- **save_covenants(covenants):**
  - Bulk-inserts covenants. Checks referential integrity (transaction must exist) and uniqueness of `covenant_id`.
- **save_schedules(schedules, holidays=None):**
  - Bulk-inserts schedules. Checks uniqueness, referential integrity, allowed status values, and ensures due dates are not on holidays or weekends.
- **get_schedules(covenant_id=None):**
  - Retrieves all schedules, or those for a specific covenant.
- **get_transaction(transaction_id):**
  - Retrieves a transaction by ID.
- **get_covenants(transaction_id=None):**
  - Retrieves all covenants, or those for a specific transaction.
- **update_schedule_status(schedule_id, status):**
  - Updates the status of a schedule entry (e.g., to `completed`, `overdue`).
- **delete_schedule(schedule_id):**
  - Deletes a schedule entry by ID.

### 4. Data Integrity & Error Handling
- All inserts and updates are checked for uniqueness, referential integrity, and business rule compliance before committing.
- Any violation (e.g., duplicate IDs, missing foreign keys, invalid status, due date on holiday/weekend) raises a clear error.
- All exceptions are logged with a `[DB ERROR]` prefix for easy debugging.

### 5. Extensibility
- The schema and methods are designed to be easily extended for new fields, tables, or business rules as needed.

For more details, see the comments and docstrings in `database.py`.
```

## Testing Philosophy & Coverage

Testing is a core part of this project’s quality and reliability. The test suite is designed to:

- **Cover all business rules and edge cases:** Every rule, validation, and edge case described above is explicitly tested.
- **Use realistic data factories:** Helper functions generate realistic transaction and covenant data for each test.
- **Test both success and failure:** Tests check for correct schedule generation, as well as proper error handling for invalid input, data integrity violations, and edge cases.
- **Database integration:** Tests include in-memory database operations to verify persistence, uniqueness, referential integrity, and CRUD operations.
- **Performance and scalability:** The suite includes tests for large datasets and stress scenarios to ensure the system remains robust under load.
- **Documentation:** Every test is clearly documented with docstrings and comments, making the intent and business logic explicit.

### Running the Tests
To run all tests, simply execute:
```bash
pytest test_schedule_generator.py
```
All tests should pass with no errors or warnings. For more details, see the comments and docstrings in `test_schedule_generator.py`.

## Business Rules
- See `intern_reminder_assignment.md` for full requirements and rules.

## Author
- [Your Name]
