import unittest
from datetime import datetime, timedelta
from schedule_generator import ScheduleGenerator

class TestScheduleGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = ScheduleGenerator()

    def test_monthly_schedule_generation(self):
        transaction = {
            "transaction_id": "TXN-001",
            "start_date": "2025-01-15",
            "end_date": "2027-01-15"
        }
        covenants = [{
            "covenant_id": "COV-001",
            "transaction_id": "TXN-001",
            "description": "Monthly Financial Statements",
            "frequency": "monthly",
            "owner_email": "finance@company.com"
        }]

        schedules = self.generator.generate_schedules(transaction, covenants)
        self.assertEqual(len(schedules), 24)
        self.assertEqual(schedules[0]['due_date'], '2025-02-15')

    def test_quarter_end_dates(self):
        transaction = {
            "transaction_id": "TXN-002",
            "start_date": "2025-03-31",
            "end_date": "2026-03-31"
        }
        covenants = [{
            "covenant_id": "COV-002",
            "transaction_id": "TXN-002",
            "description": "Quarterly Compliance Certificate",
            "frequency": "quarterly",
            "owner_email": "legal@company.com"
        }]

        schedules = self.generator.generate_schedules(transaction, covenants)
        self.assertEqual(len(schedules), 5)
        expected_due_dates = ["2025-06-30", "2025-09-30", "2025-12-31", "2026-02-28", "2026-03-31"]
        actual_due_dates = [s['due_date'] for s in schedules]
        self.assertEqual(actual_due_dates, expected_due_dates)

    def test_annual_schedule_generation(self):
        transaction = {
            "transaction_id": "TXN-003",
            "start_date": "2024-02-29",
            "end_date": "2028-02-28"
        }
        covenants = [{
            "covenant_id": "COV-003",
            "transaction_id": "TXN-003",
            "description": "Annual Audited Financials",
            "frequency": "annually",
            "owner_email": "finance@company.com"
        }]

        schedules = self.generator.generate_schedules(transaction, covenants)
        self.assertEqual(len(schedules), 3)
        expected_due_dates = ["2025-02-28", "2026-02-28", "2027-02-28"]
        actual_due_dates = [s['due_date'] for s in schedules]
        self.assertEqual(actual_due_dates, expected_due_dates)

    def test_weekly_schedule_generation(self):
        transaction = {
            "transaction_id": "TXN-004",
            "start_date": "2025-01-01",
            "end_date": "2025-03-01"
        }
        covenants = [{
            "covenant_id": "COV-004",
            "transaction_id": "TXN-004",
            "description": "Weekly Update",
            "frequency": "weekly",
            "owner_email": "team@company.com"
        }]

        schedules = self.generator.generate_schedules(transaction, covenants)
        first_due_date = datetime.strptime(schedules[0]['due_date'], "%Y-%m-%d")
        for s in schedules:
            due_date = datetime.strptime(s['due_date'], "%Y-%m-%d")
            self.assertEqual(due_date.weekday(), first_due_date.weekday())

    def test_daily_schedule_generation_excludes_weekends(self):
        transaction = {
            "transaction_id": "TXN-005",
            "start_date": "2025-01-01",
            "end_date": "2025-01-10"
        }
        covenants = [{
            "covenant_id": "COV-005",
            "transaction_id": "TXN-005",
            "description": "Daily Snapshot",
            "frequency": "daily",
            "owner_email": "daily@company.com"
        }]

        schedules = self.generator.generate_schedules(transaction, covenants)
        for s in schedules:
            due_date = datetime.strptime(s['due_date'], "%Y-%m-%d")
            self.assertNotIn(due_date.weekday(), [5, 6])

    def test_transaction_end_cutoff(self):
        transaction = {
            "transaction_id": "TXN-006",
            "start_date": "2025-12-01",
            "end_date": "2025-12-31"
        }
        covenants = [{
            "covenant_id": "COV-006",
            "transaction_id": "TXN-006",
            "description": "Monthly Covenant",
            "frequency": "monthly",
            "owner_email": "monthly@company.com"
        }]

        schedules = self.generator.generate_schedules(transaction, covenants)
        for s in schedules:
            due = datetime.strptime(s['due_date'], "%Y-%m-%d")
            self.assertLessEqual(due, datetime.strptime(transaction['end_date'], "%Y-%m-%d"))

    def test_month_end_edge_case(self):
        transaction = {
            "transaction_id": "TXN-007",
            "start_date": "2025-01-31",
            "end_date": "2025-06-30"
        }
        covenants = [{
            "covenant_id": "COV-007",
            "transaction_id": "TXN-007",
            "description": "Month-End Case",
            "frequency": "monthly",
            "owner_email": "edge@company.com"
        }]

        schedules = self.generator.generate_schedules(transaction, covenants)
        due_dates = [s['due_date'] for s in schedules]
        self.assertIn("2025-02-28", due_dates)
        self.assertIn("2025-03-31", due_dates)

if __name__ == '__main__':
    unittest.main()
