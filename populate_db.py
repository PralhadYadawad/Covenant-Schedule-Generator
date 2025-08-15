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
    {"covenant_id": "COV-001", "transaction_id": "TXN-001", "description": "Monthly Financial Statements", "frequency": "monthly", "owner_email": "finance@company.com"},
    {"covenant_id": "COV-002", "transaction_id": "TXN-001", "description": "Quarterly Compliance Certificate", "frequency": "quarterly", "owner_email": "legal@company.com"},
    {"covenant_id": "COV-003", "transaction_id": "TXN-001", "description": "Annual Audited Financials", "frequency": "annually", "owner_email": "finance@company.com"}
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