# Technical Evaluation: Covenant Schedule Generator

**Type:** Coding evaluation assignment

## Problem Statement
Build a system that automatically generates fulfillment schedules for transaction covenants based on their frequency requirements and transaction lifecycle dates.

## Business Context
A financial transaction has multiple covenant obligations (reporting requirements) that must be fulfilled at regular intervals. Each covenant has a specific frequency (daily, weekly, monthly, quarterly, annually) and the system needs to generate all expected due dates for the covenant's entire lifecycle.

## Your Task
Create a schedule generator that takes covenant definitions and produces a complete schedule of due dates that can be persisted to a database.

## Input Data Structure

**Transaction:**
```json
{
  "transaction_id": "TXN-001",
  "name": "Corporate Credit Facility",
  "start_date": "2025-01-15",
  "end_date": "2027-01-15"
}
```

**Covenants:**
```json
[
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
```

## Expected Output Structure

**Generated Schedule:**
```json
[
  {
    "schedule_id": "SCH-001",
    "covenant_id": "COV-001",
    "due_date": "2025-02-15",
    "status": "pending",
    "period_start": "2025-01-15",
    "period_end": "2025-02-14"
  },
  {
    "schedule_id": "SCH-002", 
    "covenant_id": "COV-001",
    "due_date": "2025-03-15",
    "status": "pending",
    "period_start": "2025-02-15",
    "period_end": "2025-03-14"
  }
  // ... continue for entire transaction lifecycle
]
```

## Requirements

### 1. Core Logic 
Implement schedule generation with these rules:
- **Monthly**: Due on the same day each month (e.g., 15th of each month)
- **Quarterly**: Due every 3 months from start date
- **Annually**: Due on anniversary of start date each year
- **Weekly**: Due same day of week, every week
- **Daily**: Due every business day (Monday-Friday)

### 2. Edge Case Handling 
Handle these scenarios:
- Month-end dates (e.g., Jan 31 → Feb 28/29)
- Weekends and holidays (move to next business day)
- Leap years
- Transaction end date cutoff (don't generate schedules beyond end date)

### 3. Data Persistence 
- Design database schema for storing schedules
- Implement CRUD operations
- Include data validation
- Support bulk inserts for efficiency

### 4. Testing & Documentation
- Unit tests covering all frequency types
- Edge case test scenarios
- Clear documentation of business rules
- Usage examples

## Deliverables

**Code Files:**
- `schedule_generator.py` (or `.js`, `.java`, etc.)
- `database.py` - Schema and persistence logic
- `test_schedule_generator.py` - Comprehensive tests
- `README.md` - Setup and usage instructions

**Test Cases to Include:**
```python
# Example test scenarios
def test_monthly_schedule_generation():
    # Monthly covenant from Jan 15, 2025 to Jan 15, 2027
    # Should generate 24 monthly due dates
    
def test_quarter_end_dates():
    # Quarterly covenant starting March 31
    # Handle Feb 28/29 correctly
    
def test_weekend_adjustment():
    # Due dates falling on weekends move to Monday
    
def test_transaction_end_cutoff():
    # Don't generate schedules past transaction end date
```

## Sample Usage
```python
generator = ScheduleGenerator()

# Load transaction and covenants
transaction = load_transaction("TXN-001")
covenants = load_covenants("TXN-001")

# Generate all schedules
schedules = generator.generate_schedules(transaction, covenants)

# Persist to database
db.save_schedules(schedules)

print(f"Generated {len(schedules)} schedule entries")
```

## Evaluation Criteria

**Code Quality (40%)**
- Clean, readable code structure
- Proper error handling
- Meaningful variable/function names
- Code organization and modularity

**Business Logic (30%)**
- Correct implementation of frequency rules
- Proper handling of edge cases
- Accurate date calculations
- Transaction boundary respect

**Testing (20%)**
- Comprehensive test coverage
- Edge case testing
- Clear test descriptions
- Test data setup

**Documentation (10%)**
- Clear README with setup instructions
- Code comments for complex logic
- Usage examples
- Business rule documentation

## Technology Choice
Use any language you're comfortable with:
- **Python**: datetime, SQLite/PostgreSQL
- **JavaScript/Node.js**: Date objects, SQLite
- **Java**: LocalDate, H2/PostgreSQL
- **C#**: DateTime, SQL Server/SQLite

## Bonus Points
- Performance optimization for large datasets
- Configuration-driven frequency definitions
- Holiday calendar integration
- Schedule modification/regeneration logic

## Getting Started
1. Choose your technology stack
2. Design the data structures
3. Implement basic monthly schedule generation
4. Add other frequencies incrementally
5. Implement persistence layer
6. Add comprehensive testing

## Sample Test Data
```json
{
  "transaction": {
    "transaction_id": "TXN-TEST",
    "start_date": "2025-01-01",
    "end_date": "2025-12-31"
  },
  "covenants": [
    {"frequency": "monthly", "description": "Monthly Reports"},
    {"frequency": "quarterly", "description": "Quarterly Filing"},
    {"frequency": "annually", "description": "Annual Review"}
  ]
}
```

Expected output: 11 monthly + 3 quarterly + 0 annual = 14 total schedule entries

---

**Submission:** Email code files + brief explanation of approach  
**Questions:** Available via email/Slack during evaluation period