# Covenant Schedule Generator

## Overview

The **Covenant Schedule Generator** is a professional-grade Python system designed to generate, persist, and manage covenant fulfillment schedules for financial transactions. Tailored for financial institutions and compliance teams, it automates the creation of reminder schedules for covenants—such as financial reporting, compliance certificates, and audits—associated with loans, credit facilities, and other financial products.

This project prioritizes robustness, maintainability, and extensibility, with a strong emphasis on clear business rule enforcement, comprehensive edge case handling, and data integrity. All code is thoroughly documented and tested to ensure reliability.

## Key Features

- **Flexible Schedule Generation:**
  - Supports daily, weekly, monthly, quarterly, and annual frequencies.
  - Automatically adjusts for month-end, weekends, leap years, holidays, and transaction end cutoffs.
- **Business Rule Enforcement:**
  - Explicitly handles and documents all business logic and edge cases.
  - Configuration-driven frequency and holiday rules.
- **Persistence Layer:**
  - Utilizes SQLite for lightweight, reliable storage.
  - Supports full CRUD (Create, Read, Update, Delete) and bulk operations for transactions, covenants, and schedules.
- **Holiday Calendar Integration:**
  - Offers customizable holiday lists for precise business day calculations.
- **Comprehensive Testing:**
  - Features an extensive unit test suite covering all business scenarios and edge cases.
- **Professional Documentation:**
  - Includes clear comments and descriptive docstrings for maintainability.

## Setup Instructions

**Requirements:**
- Python 3.8 or higher
- Git

**Setup Steps:**
1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd <repo-folder>
   ```
2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage Example

```python
from schedule_generator import ScheduleGenerator
from database import Database

# Define a sample transaction and covenants
transaction = {
    "transaction_id": "TXN-001",
    "name": "Corporate Credit Facility",
    "start_date": "2025-01-15",
    "end_date": "2027-01-15"
}
covenants = [

    {
      "covenant_id": "COV-001",
      "transaction_id": "TXN-001",
      "description": "Monthly Financial Statements",
      "frequency": "monthly",
      "owner_email": "finance@company.com"
    },

    {
      "covenant_id": "COV-002",
      "transaction_id": "TXN-001",
      "description": "Quarterly Compliance Certificate",
      "frequency": "quarterly",
      "owner_email": "legal@company.com"
    },

    {
      "covenant_id": "COV-003",
      "transaction_id": "TXN-001",
      "description": "Annual Audited Financials",
      "frequency": "annually",
      "owner_email": "finance@company.com"
    }

]

# Generate schedules
sg = ScheduleGenerator()
schedules = sg.generate_schedules(transaction, covenants)

# Save to database
with Database('schedules.db') as db:
    db.save_transaction(transaction)
    db.save_covenants(covenants)
    db.save_schedules(schedules)

print(f"Generated {len(schedules)} schedule entries")
```

## Business Rules & Logic

The system enforces strict business rules to ensure accuracy, compliance, and data integrity:

### Transaction & Covenant Validation
- **Required Fields:**
  - Transaction: `transaction_id`, `name`, `start_date`, `end_date` (non-empty strings).
  - Covenant: `covenant_id`, `transaction_id`, `description`, `frequency`, `owner_email` (non-empty strings).
- **Date Format:** Must be `YYYY-MM-DD`; `start_date` must not exceed `end_date`.
- **Email Validation:** `owner_email` must be a valid email address.
- **Referential Integrity:** Each covenant’s `transaction_id` must correspond to an existing transaction.
- **Uniqueness:** `covenant_id` and `schedule_id` must be unique system-wide.

### Frequency & Schedule Generation
- **Supported Frequencies:** `daily`, `weekly`, `monthly`, `quarterly`, `annually` (case-insensitive).
- **Minimum Durations:**
  - Annual: ≥ 1 year
  - Quarterly: ≥ 90 days
  - Monthly: ≥ 28 days
  - Weekly/Daily: ≥ 1 week/day
- **Unsupported Frequencies:** Raise an error if not listed above.

### Business Day & Holiday Handling
- **Business Days:** Monday–Friday, excluding holidays.
- **Holiday Configuration:** Accepts a custom list or auto-generates holidays via the `holidays` package.
- **Due Date Adjustments:** Shifts to the next/previous business day (configurable) if on a weekend/holiday.
- **Edge Cases:**
  - No schedules generated if all days in a period are holidays.
  - Error raised if no business day is found within 10 days of adjustment.

### Edge Case Handling
- **Month-End Logic:** Schedules starting on a month’s last day maintain month-end due dates (e.g., Jan 31 → Feb 28/29).
- **Leap Year Logic:** Annual schedules from Feb 29 use Feb 29 in leap years, Feb 28 otherwise.
- **Quarterly Schedules:** Special handling for February/March period-ends.
- **Transaction End Cutoff:** No due dates beyond the next business day after `end_date`.

### Data Integrity & Database Rules
- **Foreign Keys:** Cascading deletes for transactions and covenants.
- **Status Field:** Limited to `pending`, `completed`, `overdue`, `cancelled`.
- **Bulk Operations:** Ensures uniqueness and referential integrity before committing.
- **Error Handling:** Raises descriptive errors for all violations.

For complete details, see `intern_reminder_assignment.md`.

## How the Schedule Generation Logic Works

The `ScheduleGenerator` class drives the core functionality:

1. **Initialization:**
   - Accepts optional holidays, adjustment direction (`forward`/`backward`), country code, and years.
   - Auto-generates holidays if unspecified, using the `holidays` package or defaults.
2. **Validation:**
   - Checks all transaction and covenant data against business rules.
3. **Schedule Generation:**
   - Selects generation method by frequency.
   - Calculates due dates, applying month-end, leap year, and business day rules.
   - Creates unique schedule entries with `schedule_id`, `covenant_id`, due date, status, and period dates.
4. **Edge Case Handling:**
   - Manages month-end transitions, leap years, transaction cutoffs, and holiday/weekend adjustments.
5. **Error Handling:**
   - Raises errors for unresolvable business days or rule violations.
6. **Extensibility:**
   - Modular design supports new frequencies or rules.

See `schedule_generator.py` for more.

## Database Layer & Persistence Logic

The `Database` class ensures robust data management:

- **Schema:** SQLite-based with tables for `transactions`, `covenants`, and `schedules` (foreign keys, cascading deletes).
- **Context Management:** Used via `with Database(...) as db:` to handle connections and schema creation.
- **Core Methods:**
  - `save_transaction(transaction)`: Inserts unique transactions.
  - `save_covenants(covenants)`: Bulk-inserts with integrity checks.
  - `save_schedules(schedules, holidays=None)`: Bulk-inserts, enforces rules.
  - `get_schedules(covenant_id=None)`, `get_transaction(transaction_id)`, `get_covenants(transaction_id=None)`: Retrieval methods.
  - `update_schedule_status(schedule_id, status)`, `delete_schedule(schedule_id)`: Updates and deletes.
- **Integrity:** Validates uniqueness, referential integrity, and business rules; logs errors as `[DB ERROR]`.

See `database.py` for details.

## Testing Philosophy & Coverage

The test suite ensures quality:
- Tests all business rules, edge cases, success/failure scenarios, and database operations.
- Uses realistic data factories and in-memory databases.
- Includes performance tests for scalability.
- Fully documented with docstrings.

**Run Tests:**
```bash
pytest test_schedule_generator.py
```
See `test_schedule_generator.py` for more.

## Full Requirements
- Refer to `intern_reminder_assignment.md`.

## Author
- Pralhad R Yadawad

